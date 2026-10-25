"""
Banker's Algorithm Web Server
-----------------------------
Zero-dependency HTTP server using Python's built-in `http.server`.
Serves a responsive web application and JSON REST API
for Banker's Algorithm Simulator on localhost:8080.
"""

import sys
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure current dir is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from banker_algorithm import (
    calculate_need,
    calculate_available,
    run_safety_algorithm,
    simulate_resource_request,
    get_classic_safe_preset,
    get_classic_unsafe_preset,
    get_zero_need_preset,
    generate_random_valid_scenario
)
from validation import validate_scenario, validate_dimensions, validate_names


def get_html_page() -> str:
    """Returns the single-page application HTML/CSS/JavaScript."""
    # Read index.html from static directory
    html_path = os.path.join(BASE_DIR, "web", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Banker's Algorithm Simulator</h1>"


class BankersHTTPRequestHandler(BaseHTTPRequestHandler):
    """Handles REST API and static page requests."""

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]} {args[1]}\n")

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/", "/index.html"]:
            html = get_html_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        elif path == "/api/preset/safe":
            self._send_json(get_classic_safe_preset())
            return

        elif path == "/api/preset/unsafe":
            self._send_json(get_classic_unsafe_preset())
            return

        elif path == "/api/preset/zero-need":
            self._send_json(get_zero_need_preset())
            return

        elif path.startswith("/api/preset/random"):
            query = urllib.parse.parse_qs(parsed.query)
            n = int(query.get("n", [5])[0])
            m = int(query.get("m", [3])[0])
            self._send_json(generate_random_valid_scenario(n, m))
            return

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        try:
            req_data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            self._send_json({"error": "Invalid JSON payload"}, 400)
            return

        if path == "/api/run-safety":
            total = req_data.get("total", [])
            allocation = req_data.get("allocation", [])
            maximum = req_data.get("maximum", [])
            process_names = req_data.get("process_names", None)
            resource_names = req_data.get("resource_names", None)

            valid, err = validate_scenario(total, allocation, maximum, process_names, resource_names)
            if not valid:
                self._send_json({"success": False, "error": err}, 400)
                return

            res = run_safety_algorithm(total, allocation, maximum, process_names, resource_names)
            need = calculate_need(allocation, maximum)
            available = calculate_available(total, allocation)

            # Convert SafetyResult to serializable dict
            steps_data = []
            for s in res.steps:
                steps_data.append({
                    "step_number": s.step_number,
                    "process_index": s.process_index,
                    "process_name": s.process_name,
                    "work_before": s.work_before,
                    "need": s.need,
                    "allocation": s.allocation,
                    "work_after": s.work_after,
                    "finish_status": s.finish_status,
                    "is_success": s.is_success,
                    "description": s.description
                })

            resp = {
                "success": True,
                "is_safe": res.is_safe,
                "safe_sequence": res.safe_sequence,
                "safe_sequence_indices": res.safe_sequence_indices,
                "unfinished_processes": res.unfinished_processes,
                "unfinished_indices": res.unfinished_indices,
                "initial_available": res.initial_available,
                "final_work": res.final_work,
                "summary_title": res.summary_title,
                "summary_message": res.summary_message,
                "educational_note": res.educational_note,
                "steps": steps_data,
                "need": need,
                "available": available
            }
            self._send_json(resp)
            return

        elif path == "/api/simulate-request":
            total = req_data.get("total", [])
            allocation = req_data.get("allocation", [])
            maximum = req_data.get("maximum", [])
            process_index = req_data.get("process_index", 0)
            request_vector = req_data.get("request_vector", [])
            process_names = req_data.get("process_names", None)
            resource_names = req_data.get("resource_names", None)

            res = simulate_resource_request(
                total, allocation, maximum, process_index,
                request_vector, process_names, resource_names
            )

            safety_dict = None
            if res.safety_result:
                safety_dict = {
                    "is_safe": res.safety_result.is_safe,
                    "safe_sequence": res.safety_result.safe_sequence,
                    "unfinished_processes": res.safety_result.unfinished_processes,
                    "summary_title": res.safety_result.summary_title,
                    "summary_message": res.safety_result.summary_message
                }

            resp = {
                "is_granted": res.is_granted,
                "rejection_stage": res.rejection_stage,
                "rejection_reason": res.rejection_reason,
                "process_index": res.process_index,
                "process_name": res.process_name,
                "request_vector": res.request_vector,
                "original_allocation": res.original_allocation,
                "original_need": res.original_need,
                "original_available": res.original_available,
                "tentative_allocation": res.tentative_allocation,
                "tentative_need": res.tentative_need,
                "tentative_available": res.tentative_available,
                "safety_result": safety_dict,
                "explanation": res.explanation
            }
            self._send_json(resp)
            return

        else:
            self.send_response(404)
            self.end_headers()


def run_server(port: int = 8080):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, BankersHTTPRequestHandler)
    print(f"Banker's Algorithm Simulator Server running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
