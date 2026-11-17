#!/usr/bin/env python3
"""
Updates Jenkins job configurations for billing-develop, billing-qa, and billing-prod
with the latest pipeline definitions from ci-cd/jenkins/pipelines/.
"""

import subprocess
import xml.sax.saxutils as saxutils
import re
import os

JOBS = [
    {
        "name": "billing-develop",
        "jenkinsfile": "ci-cd/jenkins/pipelines/develop/Jenkinsfile",
        "description": "Hotel Billing System - Local Development Pipeline (Account 111122223333)"
    },
    {
        "name": "billing-qa",
        "jenkinsfile": "ci-cd/jenkins/pipelines/qa/Jenkinsfile",
        "description": "Hotel Billing System - Local QA Pipeline (Account 444455556666)"
    },
    {
        "name": "billing-prod",
        "jenkinsfile": "ci-cd/jenkins/pipelines/prod/Jenkinsfile",
        "description": "Hotel Billing System - Local Production Pipeline (Account 777788889999)"
    }
]

def update_job(job_name, jenkinsfile_path, description):
    print(f"Updating job {job_name} from {jenkinsfile_path}...")
    if not os.path.isfile(jenkinsfile_path):
        print(f"Error: Jenkinsfile not found at {jenkinsfile_path}")
        return False

    with open(jenkinsfile_path, "r", encoding="utf-8") as f:
        pipeline_code = f.read()

    # Get current job config XML via jenkins-cli
    cmd_get = [
        "docker", "exec", "jenkins",
        "java", "-jar", "/tmp/jenkins-cli.jar",
        "-s", "http://localhost:8080/",
        "get-job", job_name
    ]
    res_get = subprocess.run(cmd_get, capture_output=True, text=True)
    if res_get.returncode != 0:
        print(f"Error getting config for {job_name}: {res_get.stderr}")
        return False

    config_xml = res_get.stdout

    # Escape XML characters for pipeline script
    escaped_code = saxutils.escape(pipeline_code)
    # Also escape double quotes and single quotes
    escaped_code = escaped_code.replace('"', '&quot;').replace("'", '&#x27;')

    # Replace <script>...</script>
    new_config = re.sub(
        r'<script>.*?</script>',
        lambda m: f'<script>{escaped_code}</script>',
        config_xml,
        flags=re.DOTALL
    )

    # Update description if present
    if "<description>" in new_config:
        new_config = re.sub(
            r'<description>.*?</description>',
            lambda m: f'<description>{saxutils.escape(description)}</description>',
            new_config,
            flags=re.DOTALL
        )

    # Write new config to container and call update-job
    proc_update = subprocess.Popen(
        [
            "docker", "exec", "-i", "jenkins",
            "java", "-jar", "/tmp/jenkins-cli.jar",
            "-s", "http://localhost:8080/",
            "update-job", job_name
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc_update.communicate(input=new_config)

    if proc_update.returncode == 0:
        print(f"Successfully updated Jenkins job: {job_name}")
        return True
    else:
        print(f"Failed to update {job_name}: {stderr}")
        return False

if __name__ == "__main__":
    for job in JOBS:
        update_job(job["name"], job["jenkinsfile"], job["description"])
