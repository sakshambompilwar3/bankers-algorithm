#!/usr/bin/env python3
"""
Banker's Algorithm Simulator — Application Server
--------------------------------------------------
Zero-dependency HTTP server using Python's built-in http.server.
Serves the single-page web application and JSON REST API.

Usage:
    python3 app.py            # Starts server and opens browser
    python3 app.py --no-open  # Starts server without opening browser
    python3 app.py 9000       # Use a custom port
"""

import sys
import os
import json
import webbrowser
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

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
    generate_random_valid_scenario,
)
from validation import validate_scenario


def _safety_result_to_dict(result):
    """Convert a SafetyResult (with new CheckDetail fields) to a JSON-safe dict."""
    steps_data = []
    for s in result.steps:
        checks_data = []
        for proc_checks in s.checks:
            checks_data.append([{
                "process_index": c.process_index,
                "process_name": c.process_name,
                "resource_index": c.resource_index,
                "resource_name": c.resource_name,
                "need_value": c.need_value,
                "work_value": c.work_value,
                "satisfied": c.satisfied,
            } for c in proc_checks])
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
            "description": s.description,
            "checks": checks_data,
            "skipped_processes": s.skipped_processes,
        })
    return {
        "is_safe": result.is_safe,
        "safe_sequence": result.safe_sequence,
        "safe_sequence_indices": result.safe_sequence_indices,
        "unfinished_processes": result.unfinished_processes,
        "unfinished_indices": result.unfinished_indices,
        "unfinished_details": result.unfinished_details,
        "steps": steps_data,
        "initial_available": result.initial_available,
        "final_work": result.final_work,
        "summary_title": result.summary_title,
        "summary_message": result.summary_message,
        "educational_note": result.educational_note,
    }


class AppHandler(BaseHTTPRequestHandler):
    """Handles GET (page + presets) and POST (algorithm runs)."""

    def log_message(self, fmt, *args):
        pass  # Silence default logging

    def _json_response(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html_response(self, html_bytes):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_bytes)))
        self.end_headers()
        self.wfile.write(html_bytes)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            html_path = os.path.join(BASE_DIR, "static", "index.html")
            if os.path.exists(html_path):
                with open(html_path, "rb") as f:
                    self._html_response(f.read())
            else:
                self.send_error(404, "index.html not found in static/")
            return

        if path == "/api/preset/safe":
            p = get_classic_safe_preset()
            p["process_names"] = ["Chrome", "Spotify", "VS Code", "Zoom", "Netflix"]
            p["process_icons"] = ["🌐", "🎵", "💻", "📹", "🎬"]
            p["process_colors"] = ["#3b82f6", "#1db954", "#007acc", "#2d8cff", "#e50914"]
            self._json_response(p)
        elif path == "/api/preset/unsafe":
            p = get_classic_unsafe_preset()
            p["process_names"] = ["Photoshop", "Steam", "WhatsApp", "Slack"]
            p["process_icons"] = ["🎨", "🎮", "💬", "📋"]
            p["process_colors"] = ["#31a8ff", "#1b2838", "#25d366", "#4a154b"]
            self._json_response(p)
        elif path == "/api/preset/zero-need":
            self._json_response(get_zero_need_preset())
        elif path.startswith("/api/preset/random"):
            query = urllib.parse.parse_qs(parsed.query)
            n = int(query.get("n", [5])[0])
            m = int(query.get("m", [3])[0])
            self._json_response(generate_random_valid_scenario(n, m))
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)
        try:
            req = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            self._json_response({"error": "Invalid JSON"}, 400)
            return

        if path == "/api/validate":
            total = req.get("total", [])
            allocation = req.get("allocation", [])
            maximum = req.get("maximum", [])
            process_names = req.get("process_names")
            resource_names = req.get("resource_names")
            valid, err = validate_scenario(total, allocation, maximum, process_names, resource_names)
            self._json_response({"valid": valid, "error": err})

        elif path == "/api/run-safety":
            total = req.get("total", [])
            allocation = req.get("allocation", [])
            maximum = req.get("maximum", [])
            process_names = req.get("process_names")
            resource_names = req.get("resource_names")

            valid, err = validate_scenario(total, allocation, maximum, process_names, resource_names)
            if not valid:
                self._json_response({"success": False, "error": err}, 400)
                return

            result = run_safety_algorithm(total, allocation, maximum, process_names, resource_names)
            need = calculate_need(allocation, maximum)
            available = calculate_available(total, allocation)

            resp = _safety_result_to_dict(result)
            resp["success"] = True
            resp["need"] = need
            resp["available"] = available
            self._json_response(resp)

        elif path == "/api/simulate-request":
            total = req.get("total", [])
            allocation = req.get("allocation", [])
            maximum = req.get("maximum", [])
            process_index = req.get("process_index", 0)
            request_vector = req.get("request_vector", [])
            process_names = req.get("process_names")
            resource_names = req.get("resource_names")

            res = simulate_resource_request(
                total, allocation, maximum, process_index,
                request_vector, process_names, resource_names
            )

            safety_dict = None
            if res.safety_result:
                safety_dict = _safety_result_to_dict(res.safety_result)

            self._json_response({
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
                "explanation": res.explanation,
            })
        else:
            self.send_error(404)


def main():
    port = 8080
    open_browser = True

    for arg in sys.argv[1:]:
        if arg == "--no-open":
            open_browser = False
        else:
            try:
                port = int(arg)
            except ValueError:
                pass

    server = HTTPServer(("127.0.0.1", port), AppHandler)
    url = f"http://localhost:{port}/"
    print(f"\n  Banker's Algorithm Simulator")
    print(f"  ────────────────────────────")
    print(f"  Running at:  {url}")
    print(f"  Stop with:   Ctrl+C\n")

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
