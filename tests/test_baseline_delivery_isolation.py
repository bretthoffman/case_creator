"""
Baseline validation: the live delivery decision (outsource vs designer) is driven ONLY by
delivery_modes.designer_doctor_names and shade_overrides.non_argen_shade_markers. Legacy families
(doctor_overrides, routing_overrides, argen_modes) must not affect delivery, and the shipped
canonical baseline must default to outsource unless an exclusion value matches.

Run:
  python -m unittest tests.test_baseline_delivery_isolation -v
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

CANONICAL_DIR = _REPO_ROOT / "business_rules" / "v1"


def _clear_caches() -> None:
    from infrastructure.config.delivery_mode_runtime import clear_delivery_mode_cache
    from infrastructure.config.shade_override_runtime import clear_shade_override_cache

    clear_delivery_mode_cache()
    clear_shade_override_cache()


class _Env:
    """Point runtime config at a directory (temp or canonical) and clear resolver caches."""

    def __init__(self, base_dir: str):
        self._base_dir = base_dir

    def __enter__(self):
        self._prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = self._base_dir
        _clear_caches()
        return self

    def __exit__(self, *exc):
        if self._prev is None:
            os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
        else:
            os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = self._prev
        _clear_caches()
        return False


def _mode(**case):
    from domain.decisions.delivery_mode_selector import resolve_delivery_mode

    return resolve_delivery_mode(case)


class TestLegacyFamiliesDoNotAffectDelivery(unittest.TestCase):
    """Populated legacy families with EMPTY exclusion fields still yield outsource by default."""

    def _write(self, folder: Path, *, designer_doctor_names, shade_markers) -> None:
        doc = {
            "unified_version": 1,
            # Legacy content intentionally populated / turned on:
            "doctor_overrides": {
                "version": 1,
                "enabled": True,
                "rules": [
                    {
                        "id": "legacy_jane_template",
                        "enabled": True,
                        "match": {"contains_all": ["jane"]},
                        "action": {"template_override_key": "ai_envision"},
                    }
                ],
            },
            "routing_overrides": {
                "version": 1,
                "enabled": True,
                "template_family_route_overrides": [
                    {"family_key": "ai", "destination_key": "argen"}
                ],
            },
            "argen_modes": {
                "version": 1,
                "enabled": True,
                "contact_model_mode": "on",
                "contact_model_design_field": "No",
            },
            "shade_overrides": {
                "version": 1,
                "enabled": True,
                "non_argen_shade_markers": list(shade_markers),
                "rules": [],
            },
            "delivery_modes": {
                "version": 1,
                "enabled": True,
                "designer_doctor_names": list(designer_doctor_names),
            },
        }
        with (folder / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(doc, f, sort_keys=False)

    def test_legacy_populated_but_no_exclusions_is_outsource(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._write(Path(td), designer_doctor_names=[], shade_markers=[])
            with _Env(td):
                # Doctor matches a legacy doctor_overrides rule; routing says ai->argen; argen mode on.
                # None of that changes delivery: still outsource.
                self.assertEqual(_mode(doctor="Jane Doe", shade="A2"), "outsource")
                self.assertEqual(_mode(doctor="Jane Doe", shade="A2", has_study=True), "outsource")

    def test_designer_only_via_exclusion_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            self._write(Path(td), designer_doctor_names=["Jane"], shade_markers=["C3"])
            with _Env(td):
                self.assertEqual(_mode(doctor="Jane Doe", shade="A2"), "designer")  # doctor exclusion
                self.assertEqual(_mode(doctor="Someone", shade="C3"), "designer")  # shade exclusion
                self.assertEqual(_mode(doctor="Someone", shade="A2"), "outsource")  # neither


class TestShippedBaselineDeliveryBehavior(unittest.TestCase):
    """Lock the delivery behavior of the shipped canonical baseline."""

    def test_baseline_defaults_to_outsource(self) -> None:
        with _Env(str(CANONICAL_DIR)):
            # No doctor is excluded by default (designer_doctor_names is empty).
            self.assertEqual(_mode(doctor="Any Doctor", shade="A2"), "outsource")
            self.assertEqual(_mode(doctor="Any Doctor", shade="B1"), "outsource")

    def test_baseline_shade_defaults_c3_a4_go_designer(self) -> None:
        # Documents the shipped default: C3/A4 shades are active designer exclusions.
        with _Env(str(CANONICAL_DIR)):
            self.assertEqual(_mode(doctor="Any Doctor", shade="C3"), "designer")
            self.assertEqual(_mode(doctor="Any Doctor", shade="A4"), "designer")


if __name__ == "__main__":
    unittest.main()
