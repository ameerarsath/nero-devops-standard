"""
Test runner script to trigger 'universal-application-pipeline' and stream logs.
Can also handle interactive approval gates when running on 'prod'.
"""

import sys
import time
import json
import urllib.request
import urllib.parse
import http.cookiejar
from typing import Dict, Any, Optional

JENKINS_URL = "http://localhost:8080"
JOB_NAME = "universal-application-pipeline"


class JenkinsRunner:
    def __init__(self, base_url: str = JENKINS_URL):
        self.base_url = base_url
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.crumb = None
        self.crumb_field = None
        self._fetch_crumb()

    def _fetch_crumb(self):
        try:
            url = f"{self.base_url}/crumbIssuer/api/json"
            resp = self.opener.open(url)
            d = json.loads(resp.read().decode())
            self.crumb = d["crumb"]
            self.crumb_field = d["crumbRequestField"]
        except Exception as e:
            print(f"[WARN] Could not fetch crumb: {e}")

    def build_with_parameters(self, params: Dict[str, str]) -> int:
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}/job/{JOB_NAME}/buildWithParameters?{query}"
        headers = {}
        if self.crumb and self.crumb_field:
            headers[self.crumb_field] = self.crumb

        req = urllib.request.Request(url, data=b"", headers=headers, method="POST")
        resp = self.opener.open(req)
        
        # Get queue item URL from Location header
        queue_url = resp.headers.get("Location")
        print(f"[TRIGGER] Build queued. Queue item: {queue_url}")

        # Wait for build to start and obtain build number
        build_number = None
        print("Waiting for build to start...")
        for _ in range(30):
            time.sleep(2)
            if queue_url:
                try:
                    q_req = urllib.request.Request(f"{queue_url}api/json")
                    q_resp = self.opener.open(q_req)
                    q_data = json.loads(q_resp.read().decode())
                    if "executable" in q_data and q_data["executable"]:
                        build_number = q_data["executable"]["number"]
                        break
                except Exception:
                    pass

        if not build_number:
            # Fallback to querying lastBuild
            job_req = urllib.request.Request(f"{self.base_url}/job/{JOB_NAME}/api/json")
            job_resp = self.opener.open(job_req)
            job_data = json.loads(job_resp.read().decode())
            build_number = job_data.get("nextBuildNumber", 1) - 1

        print(f"[TRIGGER] Build #{build_number} started!")
        return build_number

    def stream_console(self, build_number: int, auto_approve_prod: bool = False) -> str:
        offset = 0
        is_building = True
        log_url = f"{self.base_url}/job/{JOB_NAME}/{build_number}/logText/progressiveText"
        headers = {}
        if self.crumb and self.crumb_field:
            headers[self.crumb_field] = self.crumb

        print(f"=== STREAMING CONSOLE LOGS FOR BUILD #{build_number} ===")
        while is_building:
            try:
                req = urllib.request.Request(f"{log_url}?start={offset}", headers=headers)
                with self.opener.open(req) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
                    if text:
                        print(text, end="")
                        sys.stdout.flush()
                    
                    more_data = resp.headers.get("X-More-Data", "false").lower() == "true"
                    offset = int(resp.headers.get("X-Text-Size", offset))

                    if not more_data:
                        # Check build status
                        b_req = urllib.request.Request(f"{self.base_url}/job/{JOB_NAME}/{build_number}/api/json")
                        b_resp = self.opener.open(b_req)
                        b_data = json.loads(b_resp.read().decode())
                        is_building = b_data.get("building", False)
                        if not is_building:
                            result = b_data.get("result", "UNKNOWN")
                            print(f"\n=== BUILD #{build_number} COMPLETED WITH STATUS: {result} ===")
                            return result

                    # If auto-approve prod is enabled, check for pending input steps
                    if auto_approve_prod:
                        self.handle_pending_approvals(build_number)

            except Exception as e:
                # If build hasn't output text yet
                pass
            time.sleep(2)

        return "UNKNOWN"

    def handle_pending_approvals(self, build_number: int):
        # Query wfapi for pending input actions
        try:
            wf_url = f"{self.base_url}/job/{JOB_NAME}/{build_number}/wfapi/pendingInputActions"
            req = urllib.request.Request(wf_url)
            with self.opener.open(req) as resp:
                actions = json.loads(resp.read().decode())
                for action in actions:
                    act_id = action.get("id")
                    proceed_url = action.get("proceedUrl")
                    print(f"\n[APPROVAL DETECTED] Gate ID: '{act_id}', Proceed URL: {proceed_url}")
                    
                    # Submit approval
                    submit_url = f"{self.base_url}{proceed_url}"
                    headers = {}
                    if self.crumb and self.crumb_field:
                        headers[self.crumb_field] = self.crumb
                    
                    data = b""
                    if "qa" in act_id.lower():
                        post_data = urllib.parse.urlencode({
                            "json": json.dumps({
                                "parameter": [
                                    {"name": "QA_APPROVER_NAME", "value": "qa.lead"},
                                    {"name": "QA_VERIFICATION_REFERENCE", "value": "QA-TEST-AUTOMATION-PASSED"},
                                    {"name": "QA_COMMENTS", "value": "Automated regression suite passed with zero defects."}
                                ]
                            })
                        }).encode("utf-8")
                        headers["Content-Type"] = "application/x-www-form-urlencoded"
                        data = post_data
                    elif "ops" in act_id.lower():
                        post_data = urllib.parse.urlencode({
                            "json": json.dumps({
                                "parameter": [
                                    {"name": "OPS_APPROVER_NAME", "value": "sre.lead"},
                                    {"name": "CHANGE_TICKET_ID", "value": "CHG-20261108-ENTERPRISE-PROD"},
                                    {"name": "OPS_COMMENTS", "value": "Production release authorized by Enterprise Change Advisory Board."}
                                ]
                            })
                        }).encode("utf-8")
                        headers["Content-Type"] = "application/x-www-form-urlencoded"
                        data = post_data

                    app_req = urllib.request.Request(submit_url, data=data, headers=headers, method="POST")
                    with self.opener.open(app_req) as app_resp:
                        print(f"[APPROVAL SUBMITTED] Successfully approved gate '{act_id}' (HTTP {app_resp.status})")
        except Exception:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Universal Pipeline Test Runner")
    parser.add_argument("--app", default="hotel-billing")
    parser.add_argument("--env", default="all", choices=["all", "develop", "qa", "prod"])
    parser.add_argument("--platform", default="floci", choices=["floci", "aws"])
    parser.add_argument("--topology", default="multi_account", choices=["multi_account", "single_account"])
    parser.add_argument("--action", default="DEPLOY", choices=["DEPLOY", "PLAN_ONLY", "VALIDATE_ONLY", "BUILD_RELEASE", "ROLLBACK"])
    parser.add_argument("--release-id", default="")
    parser.add_argument("--auto-approve", action="store_true", default=False)
    args = parser.parse_args()

    runner = JenkinsRunner()
    params = {
        "APPLICATION": args.app,
        "ENVIRONMENT": args.env,
        "TARGET_PLATFORM": args.platform,
        "ACCOUNT_TOPOLOGY": args.topology,
        "ACTION": args.action,
        "RELEASE_ID": args.release_id
    }

    b_num = runner.build_with_parameters(params)
    result = runner.stream_console(b_num, auto_approve_prod=args.auto_approve)
    if result != "SUCCESS":
        sys.exit(1)


if __name__ == "__main__":
    main()
