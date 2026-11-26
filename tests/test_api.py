import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import api, storage


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_patch = patch.object(storage, "DATA_ROOT", Path(self.tmp.name))
        self.data_patch.start()
        self.addCleanup(self.data_patch.stop)
        self.token_patch = patch.object(api, "TOKEN", "test-secret")
        self.token_patch.start()
        self.addCleanup(self.token_patch.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, path, method="GET", payload=None, token="test-secret"):
        body = json.dumps(payload).encode() if payload is not None else b""
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
            "HTTP_AUTHORIZATION": "Bearer " + token if token else "",
        }
        captured = {}
        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)
        result = b"".join(api.app(environ, start_response))
        return captured["status"], json.loads(result.decode())

    def test_health_is_public(self):
        status, data = self.request("/health", token="")
        self.assertEqual(status, "200 OK")
        self.assertEqual(data["status"], "ok")

    def test_api_requires_bearer_token(self):
        status, data = self.request("/api/si_natural/tasks", token="")
        self.assertEqual(status, "401 Unauthorized")
        self.assertIn("error", data)

    def test_unknown_workspace_is_not_found(self):
        status, _ = self.request("/api/other/tasks")
        self.assertEqual(status, "404 Not Found")

    def test_task_list_is_scoped_to_business(self):
        status, _ = self.request("/api/si_natural/tasks")
        self.assertEqual(status, "200 OK")
        self.assertEqual(storage.list_tasks("paymob_crm"), [])

    def test_create_task_and_sensitive_action_approval(self):
        status, task = self.request(
            "/api/si_natural/tasks",
            method="POST",
            payload={"task_type": "content_creation", "description": "Draft launch post", "action": "campaign_publishing"},
        )
        self.assertEqual(status, "201 Created")
        self.assertEqual(task["status"], "awaiting_approval")
        approvals = self.request("/api/si_natural/approvals")[1]["approvals"]
        self.assertEqual(len(approvals), 1)
        decision_status, decision = self.request(
            f"/api/si_natural/approvals/{task['id']}/decision",
            method="POST",
            payload={"decision": "approved", "note": "CEO approved"},
        )
        self.assertEqual(decision_status, "200 OK")
        self.assertTrue(decision["updated"])

    def test_invalid_task_payload_returns_400(self):
        status, data = self.request(
            "/api/si_natural/tasks",
            method="POST",
            payload={"task_type": [], "description": "bad"},
        )
        self.assertEqual(status, "400 Bad Request")
        self.assertIn("error", data)

    def test_post_without_body_is_rejected(self):
        status, data = self.request("/api/si_natural/tasks", method="POST")
        self.assertEqual(status, "413 Content Too Large")
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
