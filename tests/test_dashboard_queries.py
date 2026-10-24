import json
import os
import unittest

class TestDashboardQueries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard_path = os.path.join(
            os.path.dirname(__file__), "..", "grafana", "dashboards", "working-dashboard.json"
        )
        with open(cls.dashboard_path, "r", encoding="utf-8") as f:
            cls.dashboard = json.load(f)

    def test_json_validity(self):
        self.assertIn("panels", self.dashboard)
        self.assertGreater(len(self.dashboard["panels"]), 0)

    def test_gauge_cost_metric_does_not_use_increase(self):
        """Verify claude_code_cost_usage_USD_total (a gauge) does not use increase()."""
        for panel in self.dashboard["panels"]:
            title = panel.get("title", "")
            for target in panel.get("targets", []):
                expr = target.get("expr", "")
                if "claude_code_cost_usage_USD_total" in expr:
                    self.assertNotIn(
                        "increase(claude_code_cost_usage_USD_total",
                        expr,
                        f"Panel '{title}' incorrectly uses increase() on gauge metric claude_code_cost_usage_USD_total"
                    )

    def test_cost_expressions_conformity(self):
        """Verify expected cost queries in panels."""
        expr_by_title = {}
        for panel in self.dashboard["panels"]:
            title = panel.get("title", "")
            for target in panel.get("targets", []):
                expr_by_title[title] = target.get("expr", "")

        self.assertEqual(expr_by_title.get("Total Cost"), "sum(claude_code_cost_usage_USD_total)")
        self.assertEqual(expr_by_title.get("Active Users"), "count(count by (user_id)(claude_code_cost_usage_USD_total > 0))")
        self.assertEqual(expr_by_title.get("Cost by Model"), "sum by (model)(claude_code_cost_usage_USD_total)")
        self.assertEqual(expr_by_title.get("Cost by User"), "sum by (user_id)(claude_code_cost_usage_USD_total)")

if __name__ == "__main__":
    unittest.main()
