import unittest

from src.orchestrator import requires_approval, route_task

class OrchestratorTests(unittest.TestCase):
    def test_routes_research(self):
        self.assertEqual(route_task("competitor_analysis"), "research")

    def test_routes_creative(self):
        self.assertEqual(route_task("content_creation"), "creative")

    def test_routes_media_buyer(self):
        self.assertEqual(route_task("campaign_analysis"), "media_buyer")

    def test_routes_sales(self):
        self.assertEqual(route_task("manage_leads"), "sales_crm")

    def test_routes_operations(self):
        self.assertEqual(route_task("profit_report"), "operations")

    def test_sensitive_action_requires_approval(self):
        self.assertTrue(requires_approval("campaign_publishing"))

    def test_normal_task_does_not_require_approval(self):
        self.assertFalse(requires_approval(None))

if __name__ == "__main__":
    unittest.main()
