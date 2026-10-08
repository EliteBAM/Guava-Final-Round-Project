"""
Mock of the firm's conflict-of-interest system (stands in for Litify / Clio contacts in production).
Fake data only. Stdlib only, so it runs anywhere the agent does.

Run:  python mock_api.py [port]          (default 8787)

POST /conflicts/check   {"names": ["Ana Lopez", "John Smith and his employer"]}
                        -> {"status": "clear"} | {"status": "conflict"}
POST /admin/failure     {"mode": "none" | "error" | "timeout" | "malformed"}
                        flips failure injection live, so the demo can trigger each failure path on cue
"""

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# current and former clients, and parties the firm is adverse to on open matters (all fictional)
KNOWN_PARTIES = (
    "john smith",
    "maria gonzalez",
    "sunshine grocers",
    "coastal freight lines",
)

FAILURE_MODES = ("none", "error", "timeout", "malformed")
failure_mode = "none"

# longer than any client timeout, so "timeout" mode always times out
TIMEOUT_SLEEP_SECONDS = 30


def check(names: list[str]) -> str:
    submitted = " | ".join(names).lower()
    return "conflict" if any(party in submitted for party in KNOWN_PARTIES) else "clear"


class Handler(BaseHTTPRequestHandler):
    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def _send(self, status: int, body: bytes, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global failure_mode
        try:
            payload = self._read_json()
        except json.JSONDecodeError:
            self._send(400, b'{"error": "invalid json"}')
            return

        if self.path == "/admin/failure":
            mode = payload.get("mode")
            if mode not in FAILURE_MODES:
                self._send(400, json.dumps({"error": f"mode must be one of {FAILURE_MODES}"}).encode())
                return
            failure_mode = mode
            self._send(200, json.dumps({"mode": failure_mode}).encode())
            return

        if self.path != "/conflicts/check":
            self._send(404, b'{"error": "not found"}')
            return

        if failure_mode == "error":
            self._send(500, b'{"error": "conflict database unavailable"}')
        elif failure_mode == "timeout":
            time.sleep(TIMEOUT_SLEEP_SECONDS)
            try:
                self._send(504, b'{"error": "timeout"}')
            except ConnectionError:
                pass  # expected: the client gave up waiting long ago
        elif failure_mode == "malformed":
            self._send(200, b'{"status": "cle', "application/json")
        else:
            names = [str(n) for n in payload.get("names", [])]
            self._send(200, json.dumps({"status": check(names)}).encode())

    def log_message(self, format, *args):  # same signature as BaseHTTPRequestHandler
        # never log request bodies: they contain prospective clients' names
        sys.stderr.write("mock_api %s %s\n" % (self.command, self.path))


def make_server(port: int = 8787) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    print(f"mock conflict API on http://127.0.0.1:{port}")
    make_server(port).serve_forever()
