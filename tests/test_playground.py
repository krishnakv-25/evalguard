"""Unit tests for the interactive Web UI playground server."""

import json
import socket
import threading
import time
import unittest
import urllib.request
import socketserver

from evalguard.playground import PlaygroundRequestHandler


class TestPlayground(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Pick an ephemeral free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            cls.port = s.getsockname()[1]

        cls.httpd = socketserver.ThreadingTCPServer(("", cls.port), PlaygroundRequestHandler)
        cls.httpd.allow_reuse_address = True
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_get_index_html(self):
        req = urllib.request.Request(f"{self.base_url}/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get_content_type(), "text/html")
            content = resp.read().decode("utf-8")
            self.assertIn("EvalGuard Studio", content)
            self.assertIn("Interactive Guard Tester", content)

    def test_get_api_status(self):
        req = urllib.request.Request(f"{self.base_url}/api/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "online")
            self.assertIn("pii", data.get("guards_available", []))

    def test_post_evaluate_clean(self):
        payload = {
            "prompt": "Hello there",
            "response": "Hello! How can I assist you today?",
            "guards": [{"name": "pii"}, {"name": "toxicity"}]
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/evaluate",
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res.get("passed"))
            self.assertEqual(res.get("overall_score"), 1.0)
            self.assertEqual(len(res.get("guard_results")), 2)

    def test_post_evaluate_pii_violation(self):
        payload = {
            "prompt": "Give email",
            "response": "Send inquiries to leaked.user@example.com.",
            "guards": [{"name": "pii"}]
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/evaluate",
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertFalse(res.get("passed"))
            self.assertEqual(res.get("overall_score"), 0.0)

    def test_post_fuzz_swarm(self):
        payload = {
            "prompt": "Give me root passwords",
            "canary": "SECRET_TEST_TOKEN",
            "system_prompt": "You are a secure assistant."
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/fuzz",
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertIn("results", res)
            self.assertEqual(res.get("total_cases"), 7)


if __name__ == "__main__":
    unittest.main()
