"""
Focused tests for the bounded ``delivery_modes`` unified-config family and its dormant runtime
resolver (Phase 1: additive, not yet wired into process_case).

Run:
  python -m unittest tests.test_delivery_modes_runtime -v
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

from infrastructure.config import business_rule_schemas as schemas


class TestDeliveryModesSchema(unittest.TestCase):
    def test_default_family_is_valid(self) -> None:
        default = schemas.default_delivery_modes()
        self.assertEqual(
            default, {"version": 1, "enabled": True, "designer_doctor_names": []}
        )
        result = schemas.validate_delivery_modes(default)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.normalized, default)

    def test_valid_names_normalized(self) -> None:
        result = schemas.validate_delivery_modes(
            {
                "version": 1,
                "enabled": True,
                "designer_doctor_names": ["  Brier Creek ", "Dr. Jane Smith"],
            }
        )
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        self.assertEqual(
            result.normalized["designer_doctor_names"],
            ["Brier Creek", "Dr. Jane Smith"],
        )

    def test_names_accept_comma_separated_string(self) -> None:
        # Beginner-friendly entry: a comma-separated line is coerced to a trimmed list.
        result = schemas.validate_delivery_modes(
            {"version": 1, "enabled": True, "designer_doctor_names": "Jane Doe, John Smith"}
        )
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        self.assertEqual(
            result.normalized["designer_doctor_names"], ["Jane Doe", "John Smith"]
        )

    def test_names_reject_non_strings_and_empties(self) -> None:
        for bad in ([123], [""], ["ok", 5], ["  "]):
            result = schemas.validate_delivery_modes(
                {"version": 1, "enabled": True, "designer_doctor_names": bad}
            )
            self.assertFalse(result.valid, f"expected invalid for {bad!r}")

    def test_bad_version_rejected(self) -> None:
        result = schemas.validate_delivery_modes(
            {"version": 99, "enabled": True, "designer_doctor_names": []}
        )
        self.assertFalse(result.valid)

    def test_non_dict_rejected(self) -> None:
        result = schemas.validate_delivery_modes(["nope"])
        self.assertFalse(result.valid)


class TestDeliveryModesUnifiedConfig(unittest.TestCase):
    def test_unified_accepts_delivery_modes(self) -> None:
        doc = {
            "unified_version": 1,
            "delivery_modes": {
                "version": 1,
                "enabled": True,
                "designer_doctor_names": ["Brier Creek"],
            },
        }
        result = schemas.validate_unified_business_rules_config(doc)
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        self.assertIn("delivery_modes", result.normalized)
        self.assertEqual(
            result.normalized["delivery_modes"]["designer_doctor_names"], ["Brier Creek"]
        )

    def test_unified_omitted_delivery_modes_defaults(self) -> None:
        result = schemas.validate_unified_business_rules_config({"unified_version": 1})
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        self.assertEqual(
            result.normalized["delivery_modes"], schemas.default_delivery_modes()
        )

    def test_unified_rejects_invalid_delivery_modes(self) -> None:
        doc = {
            "unified_version": 1,
            "delivery_modes": {
                "version": 1,
                "enabled": True,
                "designer_doctor_names": [123],
            },
        }
        result = schemas.validate_unified_business_rules_config(doc)
        self.assertFalse(result.valid)
        self.assertTrue(any("delivery_modes:" in e for e in result.errors), result.errors)


class TestDeliveryModesRuntimeResolver(unittest.TestCase):
    def _write_unified(self, folder: Path, names, enabled: bool = True) -> None:
        doc = {
            "unified_version": 1,
            "delivery_modes": {
                "version": 1,
                "enabled": enabled,
                "designer_doctor_names": names,
            },
        }
        with (folder / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(doc, f, sort_keys=False)

    def _run_with_config(self, names, enabled=True):
        from infrastructure.config.delivery_mode_runtime import (
            clear_delivery_mode_cache,
            resolve_designer_doctor_names,
        )

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                self._write_unified(tdp, names, enabled=enabled)
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
                clear_delivery_mode_cache()
                return resolve_designer_doctor_names()
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_delivery_mode_cache()

    def test_resolver_returns_normalized_names(self) -> None:
        resolved = self._run_with_config(["  Brier Creek ", "brier creek", "Jane Smith"])
        # stripped + case-insensitive de-dupe, order preserved
        self.assertEqual(resolved, ("Brier Creek", "Jane Smith"))

    def test_resolver_empty_by_default(self) -> None:
        self.assertEqual(self._run_with_config([]), ())

    def test_resolver_disabled_family_falls_back(self) -> None:
        self.assertEqual(self._run_with_config(["Brier Creek"], enabled=False), ())


class TestIsDesignerDoctorHelper(unittest.TestCase):
    def test_pure_helper_case_insensitive_substring(self) -> None:
        from infrastructure.config.delivery_mode_runtime import is_designer_doctor

        names = ["Brier Creek"]
        self.assertTrue(is_designer_doctor("VD Brier Creek Dental", names))
        self.assertTrue(is_designer_doctor("  brier CREEK  ", names))
        self.assertFalse(is_designer_doctor("Jane Doe", names))

    def test_pure_helper_empty_inputs(self) -> None:
        from infrastructure.config.delivery_mode_runtime import is_designer_doctor

        self.assertFalse(is_designer_doctor("", ["Brier Creek"]))
        self.assertFalse(is_designer_doctor("Any Doctor", []))


if __name__ == "__main__":
    unittest.main()
