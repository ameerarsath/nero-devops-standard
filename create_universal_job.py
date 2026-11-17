"""
Register or update the 'universal-application-pipeline' job in Jenkins.
"""

import sys
import urllib.request
import urllib.parse
import http.cookiejar
import json
import xml.etree.ElementTree as ET
from pathlib import Path

JENKINS_URL = "http://localhost:8080"
JOB_NAME = "universal-application-pipeline"
JENKINSFILE_PATH = Path("ci-cd/jenkins/pipelines/universal/Jenkinsfile")

with open(JENKINSFILE_PATH, "r", encoding="utf-8") as f:
    pipeline_script = f.read()

config_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@1622.vc41c189cb_e5f">
  <actions>
    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobAction plugin="pipeline-model-definition@2.2293.v6e7193cec599"/>
  </actions>
  <description>Enterprise Universal Application Delivery Platform - Golden Path Multi-Cloud &amp; Multi-Account Deployment Engine</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>-1</daysToKeep>
        <numToKeep>30</numToKeep>
        <artifactDaysToKeep>-1</artifactDaysToKeep>
        <artifactNumToKeep>-1</artifactNumToKeep>
        <removeLastBuild>false</removeLastBuild>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty>
      <abortPrevious>false</abortPrevious>
    </org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.ChoiceParameterDefinition>
          <name>APPLICATION</name>
          <description>Approved application identifier registered in the central catalog.</description>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>hotel-billing</string>
              <string>sample-node-service</string>
              <string>sample-python-worker</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>ENVIRONMENT</name>
          <description>Target deployment environment: 'all' executes sequential promotion across develop, qa, and prod; or select an individual environment.</description>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>all</string>
              <string>develop</string>
              <string>qa</string>
              <string>prod</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>TARGET_PLATFORM</name>
          <description>Cloud provider target: Floci local simulation or Real AWS Cloud.</description>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>floci</string>
              <string>floci-local</string>
              <string>aws</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>ACCOUNT_TOPOLOGY</name>
          <description>Account isolation topology: Multi-Account (STS AssumeRole isolation) or Single-Account (ABAC / prefix isolation).</description>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>multi_account</string>
              <string>single_account</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>ACTION</name>
          <description>Execution lifecycle phase: DEPLOY executes full promotion; PLAN_ONLY stops after Terraform plan; VALIDATE_ONLY checks catalog &amp; specs; BUILD_RELEASE produces release manifest.</description>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>DEPLOY</string>
              <string>PLAN_ONLY</string>
              <string>VALIDATE_ONLY</string>
              <string>BUILD_RELEASE</string>
              <string>ROLLBACK</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>RELEASE_ID</name>
          <description>Optional immutable Release ID (e.g. rel-20261106173000). Auto-generated if omitted.</description>
          <defaultValue></defaultValue>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@4403.v471713a_cea_19">
    <script>{ET.cdata(pipeline_script) if hasattr(ET, 'cdata') else pipeline_script.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
"""

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
crumb = None
crumb_field = None
try:
    crumb_resp = opener.open(f"{JENKINS_URL}/crumbIssuer/api/json")
    crumb_data = json.loads(crumb_resp.read().decode())
    crumb = crumb_data.get("crumb")
    crumb_field = crumb_data.get("crumbRequestField")
except Exception as e:
    print(f"[WARN] Crumb issue: {e}")

headers = {"Content-Type": "application/xml"}
if crumb and crumb_field:
    headers[crumb_field] = crumb

# Check if job exists
check_req = urllib.request.Request(f"{JENKINS_URL}/job/{JOB_NAME}/config.xml")
job_exists = False
try:
    with opener.open(check_req) as resp:
        if resp.status == 200:
            job_exists = True
except Exception:
    job_exists = False

if job_exists:
    print(f"Job '{JOB_NAME}' exists. Updating configuration...")
    url = f"{JENKINS_URL}/job/{JOB_NAME}/config.xml"
    req = urllib.request.Request(
        url,
        data=config_xml.encode("utf-8"),
        method="POST",
        headers=headers
    )
else:
    print(f"Creating job '{JOB_NAME}'...")
    url = f"{JENKINS_URL}/createItem?name={urllib.parse.quote(JOB_NAME)}"
    req = urllib.request.Request(
        url,
        data=config_xml.encode("utf-8"),
        method="POST",
        headers=headers
    )

try:
    with opener.open(req) as resp:
        print(f"[OK] Job successfully registered/updated (HTTP {resp.status})")
except urllib.error.HTTPError as e:
    print(f"[ERROR] Failed registering job: {e.code} - {e.read().decode()}", file=sys.stderr)
    sys.exit(1)
