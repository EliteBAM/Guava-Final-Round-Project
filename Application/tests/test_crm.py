"""
CRM client tests, against a stub server on a free local port. Pure: no guava import.
"""

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import crm  # noqa: E402


class StubCrm(BaseHTTPRequestHandler):
    status = 201
    requests: list[dict] = []

    def do_PUT(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        StubCrm.requests.append({"path": self.path, "key": self.headers["X-API-Key"], "body": json.loads(body)})
        self.send_response(StubCrm.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, format, *args):  # same signature as BaseHTTPRequestHandler
        pass


class TestCrmClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), StubCrm)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{cls.server.server_port}/api/v1"
        cls.env = mock.patch.dict(os.environ, {"CRM_API_URL": url, "CRM_API_KEY": "test-key"})
        cls.env.start()

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        StubCrm.requests.clear()
        StubCrm.status = 201

    def test_puts_the_record_by_call_id(self):
        record = {"disposition": "pending_signature"}
        self.assertEqual("ok", crm.upsert_pnc("call/1", "Ana Lopez", "Rear-ended.", record))
        sent = StubCrm.requests[0]
        self.assertEqual("/api/v1/pncs/call%2F1", sent["path"])  # the call ID can't escape its path segment
        self.assertEqual("test-key", sent["key"])
        self.assertEqual({"name": "Ana Lopez", "summary": "Rear-ended.", "record": record}, sent["body"])

    def test_long_text_is_cut_to_the_crm_limits(self):
        crm.upsert_pnc("call-1", "A" * 300, "B" * 6000, {})
        body = StubCrm.requests[0]["body"]
        self.assertEqual((200, 5000), (len(body["name"]), len(body["summary"])))

    def test_rejection_is_an_error(self):
        StubCrm.status = 400
        self.assertEqual("error", crm.upsert_pnc("call-1", "Ana", "", {}))

    def test_unreachable_crm_is_an_error(self):
        with mock.patch.dict(os.environ, {"CRM_API_URL": "http://127.0.0.1:9/api/v1"}):
            self.assertEqual("error", crm.upsert_pnc("call-1", "Ana", "", {}, timeout=2))


if __name__ == "__main__":
    unittest.main()
