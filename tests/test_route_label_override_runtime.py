"""
Runtime behavior tests for bounded doctor route_label_override_key support.

Run:
  python -m unittest tests.test_route_label_override_runtime -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class TestRouteLabelOverrideRuntime(unittest.TestCase):
    def _write_unified(self, folder: Path, doctor_rules: list[dict]) -> None:
        doc = {
            "unified_version": 1,
            "doctor_overrides": {"version": 1, "enabled": True, "rules": doctor_rules},
            "shade_overrides": {"version": 1, "enabled": True, "non_argen_shade_markers": ["C3", "A4"], "rules": []},
            "routing_overrides": {
                "version": 1,
                "enabled": True,
                "template_family_route_overrides": [
                    {"family_key": "argen", "destination_key": "argen"},
                    {"family_key": "study", "destination_key": "1_9"},
                    {"family_key": "anterior", "destination_key": "1_9"},
                    {"family_key": "ai", "destination_key": "1_9"},
                ],
            },
            "argen_modes": {"version": 1, "enabled": True, "contact_model_mode": "off"},
        }
        with (folder / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(doc, f, sort_keys=False)

    def test_label_override_changes_readback_not_destination(self) -> None:
        from domain.decisions.destination_selector import select_destination
        from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache
        from infrastructure.config.doctor_override_runtime import clear_doctor_override_cache
        from infrastructure.config.routing_override_runtime import clear_routing_override_cache
        from infrastructure.config.shade_override_runtime import clear_shade_override_cache

        rules = [
            {
                "id": "serbia_label_for_casey",
                "enabled": True,
                "match": {"contains_all": ["casey", "clinic"]},
                "action": {"route_label_override_key": "serbia"},
            }
        ]
        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                self._write_unified(tdp, rules)
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
                clear_doctor_override_cache()
                clear_routing_override_cache()
                clear_shade_override_cache()
                clear_argen_modes_cache()

                # study templates route to destination 1_9; override should only affect readback label
                decision = select_destination(
                    "itero_envision_study.stl",
                    "Casey Clinic",
                    case_data={"doctor": "Casey Clinic"},
                )
                self.assertEqual(decision.destination_key, "1_9")
                self.assertEqual(decision.route_label_key, "serbia")
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_doctor_override_cache()
            clear_routing_override_cache()
            clear_shade_override_cache()
            clear_argen_modes_cache()

    def test_vd_baseline_serbia_label_still_works_without_override(self) -> None:
        from domain.decisions.destination_selector import select_destination
        from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache
        from infrastructure.config.doctor_override_runtime import clear_doctor_override_cache
        from infrastructure.config.routing_override_runtime import clear_routing_override_cache
        from infrastructure.config.shade_override_runtime import clear_shade_override_cache

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                self._write_unified(tdp, [])
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
                clear_doctor_override_cache()
                clear_routing_override_cache()
                clear_shade_override_cache()
                clear_argen_modes_cache()

                decision = select_destination(
                    "itero_envision_study.stl",
                    "Jane Britt Brier Creek",
                    case_data={"doctor": "Jane Britt Brier Creek"},
                )
                self.assertEqual(decision.destination_key, "1_9")
                self.assertEqual(decision.route_label_key, "serbia")
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_doctor_override_cache()
            clear_routing_override_cache()
            clear_shade_override_cache()
            clear_argen_modes_cache()

