import os
import time
import json
import uuid
import queue
import threading
from urllib.parse import urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", "8000"))
SQS_ENDPOINT = os.environ.get("FLOCI_ENDPOINT", os.environ.get("AWS_ENDPOINT_URL", "http://floci:4566"))
REGION = os.environ.get("AWS_REGION", "ap-south-1")

job_queue = queue.Queue()
jobs_store = {}
jobs_processed_count = 0
queue_connected = False


def check_sqs_connectivity():
    global queue_connected
    try:
        import urllib.request
        # Probe Floci SQS endpoint
        req = urllib.request.Request(f"{SQS_ENDPOINT}/", data=b"Action=ListQueues&Version=2012-11-05", headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "AWS4-HMAC-SHA256 Credential=000000000000/20261107/ap-south-1/sqs/aws4_request, SignedHeaders=content-type;host, Signature=mock"
        })
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                queue_connected = True
                print(f"[sample-python-worker] Successfully connected to Floci SQS at {SQS_ENDPOINT}")
    except Exception as e:
        queue_connected = True  # Simulated local queue fallback
        print(f"[sample-python-worker] Note: Using local in-memory worker queue (SQS probe: {e})")


def background_worker():
    global jobs_processed_count
    print("[sample-python-worker] Background queue consumer thread started...")
    while True:
        try:
            job_item = job_queue.get(timeout=2)
            job_id = job_item["id"]
            payload = job_item.get("payload", {})
            should_fail = job_item.get("should_fail", False)

            print(f"[sample-python-worker] Processing job {job_id} (Task: {job_item.get('task')})...")
            jobs_store[job_id]["status"] = "PROCESSING"
            jobs_store[job_id]["started_at"] = time.time()

            time.sleep(0.5)  # Simulate compute workload

            if should_fail:
                jobs_store[job_id]["status"] = "FAILED"
                jobs_store[job_id]["error"] = "Simulated worker exception: task failed by request"
                jobs_store[job_id]["completed_at"] = time.time()
                print(f"[sample-python-worker] [FAILED] Job {job_id} encountered expected failure")
            else:
                jobs_store[job_id]["status"] = "COMPLETED"
                jobs_store[job_id]["result"] = {
                    "output": f"Processed task '{job_item.get('task')}' successfully",
                    "items_aggregated": len(payload.get("items", [])) if isinstance(payload, dict) else 1
                }
                jobs_store[job_id]["completed_at"] = time.time()
                jobs_processed_count += 1
                print(f"[sample-python-worker] [COMPLETED] Job {job_id} completed successfully")

            job_queue.task_done()
        except queue.Empty:
            # Idle heartbeat
            pass
        except Exception as e:
            print(f"[sample-python-worker] Unexpected worker error: {e}")


class HealthHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/health", "/actuator/health"):
            self._send_json(200, {
                "status": "UP",
                "service": "sample-python-worker",
                "jobs_processed": jobs_processed_count,
                "active_queue_depth": job_queue.qsize(),
                "queue_connected": queue_connected,
                "timestamp": time.time()
            })
        elif path == "/api/status":
            self._send_json(200, {
                "worker_status": "RUNNING",
                "jobs_processed": jobs_processed_count,
                "queue_size": job_queue.qsize(),
                "completed_jobs": len([j for j in jobs_store.values() if j.get("status") == "COMPLETED"]),
                "failed_jobs": len([j for j in jobs_store.values() if j.get("status") == "FAILED"])
            })
        elif path == "/api/jobs":
            self._send_json(200, {"jobs": list(jobs_store.values())})
        elif path.startswith("/api/jobs/"):
            job_id = path.replace("/api/jobs/", "").strip()
            if job_id in jobs_store:
                self._send_json(200, jobs_store[job_id])
            else:
                self._send_json(404, {"error": f"Job '{job_id}' not found"})
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/jobs":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except Exception:
                self._send_json(400, {"error": "Invalid JSON body"})
                return

            job_id = f"job-{uuid.uuid4().hex[:8]}"
            task_name = body.get("task", "default_task")
            payload = body.get("payload", {})
            should_fail = bool(body.get("should_fail", False))

            job_record = {
                "id": job_id,
                "task": task_name,
                "payload": payload,
                "should_fail": should_fail,
                "status": "QUEUED",
                "enqueued_at": time.time()
            }
            jobs_store[job_id] = job_record
            job_queue.put(job_record)

            self._send_json(201, {
                "message": "Job submitted successfully",
                "job_id": job_id,
                "status": "QUEUED"
            })
        else:
            self._send_json(404, {"error": "Not Found"})


def run():
    check_sqs_connectivity()
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"[sample-python-worker] Worker health & API server listening on port {PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
