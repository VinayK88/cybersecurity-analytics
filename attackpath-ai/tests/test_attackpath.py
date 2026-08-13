from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from attackpath_ai.core import (  # noqa: E402
    ATTACK_TEMPLATES,
    DEFAULT_THRESHOLD,
    analyze_events,
    generate_synthetic_events,
    rule_detection,
)
from attackpath_ai.visuals import attack_path_svg, confusion_matrix_svg, dashboard_preview_svg, risk_distribution_svg  # noqa: E402


class AttackPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = generate_synthetic_events()
        cls.analysis = analyze_events(cls.events)

    def test_generator_is_deterministic_and_identifiers_are_unique(self):
        self.assertEqual(self.events, generate_synthetic_events())
        self.assertEqual(len(self.events), len({event.event_id for event in self.events}))

    def test_fixture_is_synthetic_and_contains_all_scenarios(self):
        self.assertTrue(all("@" not in event.identity for event in self.events))
        self.assertTrue(all(event.identity.startswith("user-") for event in self.events))
        observed = {event.scenario for event in self.events if event.is_attack}
        self.assertEqual(observed, set(ATTACK_TEMPLATES))

    def test_rule_engine_explains_high_risk_activity(self):
        exfiltration = next(event for event in self.events if event.stage == "Exfiltration")
        score, hits = rule_detection(exfiltration)
        self.assertGreaterEqual(score, 0.5)
        self.assertIn("probable exfiltration", hits)

    def test_hybrid_model_meets_held_out_release_gates(self):
        metrics = self.analysis["test_metrics"]
        self.assertGreaterEqual(metrics["precision"], 0.85)
        self.assertGreaterEqual(metrics["recall"], 0.90)
        self.assertGreaterEqual(metrics["f1"], 0.87)

    def test_paths_are_detected_before_exfiltration(self):
        paths = self.analysis["paths"]
        self.assertEqual(len(paths), 36)
        self.assertTrue(all(path["event_count"] == 6 for path in paths))
        self.assertTrue(all(path["prevented_before_exfiltration"] for path in paths))
        self.assertLessEqual(self.analysis["operational_metrics"]["mean_minutes_to_detect"], 25)

    def test_every_attack_event_maps_to_mitre(self):
        attack_events = [event for event in self.events if event.is_attack]
        self.assertTrue(all(event.mitre_technique.startswith("T") for event in attack_events))

    def test_visuals_are_accessible_svg(self):
        results = self.analysis["results"]
        svgs = [
            risk_distribution_svg(results),
            attack_path_svg(self.analysis["paths"][0]),
            confusion_matrix_svg(self.analysis["test_metrics"]),
            dashboard_preview_svg(self.analysis),
        ]
        for svg in svgs:
            self.assertTrue(svg.startswith("<svg"))
            self.assertIn('role="img"', svg)
            self.assertIn("aria-label", svg)

    def test_public_evaluation_is_json_serializable(self):
        public = {key: value for key, value in self.analysis.items() if key != "results"}
        serialized = json.dumps(public)
        self.assertNotIn("DetectionResult", serialized)
        self.assertIn('"threshold": ' + str(DEFAULT_THRESHOLD), serialized)


if __name__ == "__main__":
    unittest.main()
