"""
Comma-separated entry parsing for the two designer-exclusion fields, aligned with the helper text
shown to beginners:

  doctor  -> delivery_modes.designer_doctor_names   Example: Jane Doe   Multiple: Jane Doe, John Smith, Pat Lee
  shade   -> shade_overrides.non_outsource_shades   Example: C3        Multiple: C3, A4, A3.5

Both fields accept a comma-separated string OR a YAML list; spaces are trimmed and empty entries
dropped. YAML list entry remains supported and the effective config stays a list.

Run:
  python -m unittest tests.test_exclusion_field_csv_entry -v
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


class TestDoctorFieldCsvEntry(unittest.TestCase):
    def _norm(self, value):
        r = schemas.validate_delivery_modes(
            {"version": 1, "enabled": True, "designer_doctor_names": value}
        )
        self.assertTrue(r.valid, r.errors)
        assert r.normalized is not None
        return r.normalized["designer_doctor_names"]

    def test_single_value(self) -> None:
        self.assertEqual(self._norm("Jane Doe"), ["Jane Doe"])

    def test_multiple_matches_helper_example(self) -> None:
        self.assertEqual(
            self._norm("Jane Doe, John Smith, Pat Lee"),
            ["Jane Doe", "John Smith", "Pat Lee"],
        )

    def test_spaces_trimmed_and_empties_dropped(self) -> None:
        self.assertEqual(self._norm("  Jane Doe , , John Smith ,  "), ["Jane Doe", "John Smith"])

    def test_yaml_list_still_supported(self) -> None:
        self.assertEqual(self._norm(["Jane Doe", "John Smith"]), ["Jane Doe", "John Smith"])

    def test_empty_string_is_empty_list(self) -> None:
        self.assertEqual(self._norm(""), [])

    def test_bad_list_still_rejected(self) -> None:
        r = schemas.validate_delivery_modes(
            {"version": 1, "enabled": True, "designer_doctor_names": ["ok", 5]}
        )
        self.assertFalse(r.valid)


class TestShadeFieldCsvEntry(unittest.TestCase):
    def _norm(self, value):
        r = schemas.validate_shade_overrides(
            {"version": 1, "enabled": True, "non_outsource_shades": value, "rules": []}
        )
        self.assertTrue(r.valid, r.errors)
        assert r.normalized is not None
        return r.normalized["non_outsource_shades"]

    def test_single_value(self) -> None:
        self.assertEqual(self._norm("C3"), ["C3"])

    def test_multiple_matches_helper_example(self) -> None:
        self.assertEqual(self._norm("C3, A4, A3.5"), ["C3", "A4", "A3.5"])

    def test_spaces_trimmed_and_empties_dropped(self) -> None:
        self.assertEqual(self._norm(" C3 , A4 ,, A3.5 "), ["C3", "A4", "A3.5"])

    def test_yaml_list_still_supported(self) -> None:
        self.assertEqual(self._norm(["C3", "A4"]), ["C3", "A4"])

    def test_bad_list_still_rejected(self) -> None:
        r = schemas.validate_shade_overrides(
            {"version": 1, "enabled": True, "non_outsource_shades": [123], "rules": []}
        )
        self.assertFalse(r.valid)


class TestUnifiedAcceptsCsvEntry(unittest.TestCase):
    def test_unified_accepts_comma_strings_for_both_fields(self) -> None:
        doc = {
            "unified_version": 1,
            "shade_overrides": {
                "version": 1,
                "enabled": True,
                "non_outsource_shades": "C3, A4, A3.5",
                "rules": [],
            },
            "delivery_modes": {
                "version": 1,
                "enabled": True,
                "designer_doctor_names": "Jane Doe, John Smith, Pat Lee",
            },
        }
        result = schemas.validate_unified_business_rules_config(doc)
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        self.assertEqual(
            result.normalized["delivery_modes"]["designer_doctor_names"],
            ["Jane Doe", "John Smith", "Pat Lee"],
        )
        self.assertEqual(
            result.normalized["shade_overrides"]["non_outsource_shades"],
            ["C3", "A4", "A3.5"],
        )


class TestCsvEntryResolvesLive(unittest.TestCase):
    """Comma-separated YAML entry flows through the live resolvers to the same values."""

    def test_end_to_end_from_comma_entry(self) -> None:
        from infrastructure.config.delivery_mode_runtime import (
            clear_delivery_mode_cache,
            is_designer_doctor,
            resolve_designer_doctor_names,
        )
        from infrastructure.config.shade_override_runtime import (
            clear_shade_override_cache,
            resolve_non_argen_shade_markers,
        )

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                doc = {
                    "unified_version": 1,
                    "shade_overrides": {
                        "version": 1,
                        "enabled": True,
                        # Beginner types a comma line directly in the YAML.
                        "non_outsource_shades": "C3, A4, A3.5",
                        "rules": [],
                    },
                    "delivery_modes": {
                        "version": 1,
                        "enabled": True,
                        "designer_doctor_names": "Jane Doe, John Smith, Pat Lee",
                    },
                }
                Path(td, "case_creator_rules.yaml").write_text(
                    yaml.dump(doc, sort_keys=False), encoding="utf-8"
                )
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = td
                clear_delivery_mode_cache()
                clear_shade_override_cache()

                self.assertEqual(
                    resolve_designer_doctor_names(), ("Jane Doe", "John Smith", "Pat Lee")
                )
                # shade markers are uppercased by the live resolver
                self.assertEqual(resolve_non_argen_shade_markers(()), ("C3", "A4", "A3.5"))
                # case-insensitive substring match still works
                self.assertTrue(is_designer_doctor("Dr. John Smith, DDS"))
                self.assertFalse(is_designer_doctor("Someone Else"))
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            from infrastructure.config.delivery_mode_runtime import clear_delivery_mode_cache
            from infrastructure.config.shade_override_runtime import clear_shade_override_cache

            clear_delivery_mode_cache()
            clear_shade_override_cache()


if __name__ == "__main__":
    unittest.main()
