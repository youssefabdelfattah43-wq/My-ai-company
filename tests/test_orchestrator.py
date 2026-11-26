import unittest

from src.orchestrator import (
    APPROVAL_ACTIONS,
    requires_approval,
    route_task,
)


class OrchestratorTests(unittest.TestCase):
    def test_routes_all_agent_domains(self):
        expected = {
            "competitor_analysis": "research",
            "content_creation": "creative",
            "campaign_analysis": "media_buyer",
            "manage_leads": "sales_crm",
            "profit_report": "operations",
        }
        for task_type, agent_id in expected.items():
            with self.subTest(task_type=task_type):
                self.assertEqual(route_task(task_type), agent_id)

    def test_unknown_task_type_is_rejected(self):
        with self.assertRaises(ValueError):
            route_task("delete_everything")

    def test_every_sensitive_action_requires_approval(self):
        for action in APPROVAL_ACTIONS:
            with self.subTest(action=action):
                self.assertTrue(requires_approval(action))

    def test_non_sensitive_or_missing_action_does_not_require_approval(self):
        self.assertFalse(requires_approval(None))
        self.assertFalse(requires_approval("read_ad_reports"))


if __name__ == "__main__":
    unittest.main()
