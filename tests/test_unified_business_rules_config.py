"""
Validation-only tests for the unified business-rules document (see validate_unified_business_rules_config).

Run from repo root:
  python -m unittest tests.test_unified_business_rules_config -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infrastructure.config import business_rule_loader as loader
from infrastructure.config import business_rule_schemas as schemas


FIXTURE_PATH = _REPO_ROOT / "tests" / "fixtures" / "unified_business_rules_baseline.yaml"
SPLIT_ARCHIVE = _REPO_ROOT / "business_rules" / "archive" / "v1_split_backup"


class TestUnifiedBusinessRulesConfig(unittest.TestCase):
    def test_imports_no_cycle_with_loader(self) -> None:
        from infrastructure.config.business_rule_schemas import validate_unified_business_rules_config

        self.assertTrue(callable(validate_unified_business_rules_config))

    def test_minimal_unified_valid_defaults_and_warnings(self) -> None:
        result = schemas.validate_unified_business_rules_config({"unified_version": 1})
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        self.assertEqual(
            set(result.normalized.keys()),
            set(schemas.SUPPORTED_FAMILIES),
        )
        for fam in schemas.SUPPORTED_FAMILIES:
            self.assertEqual(result.normalized[fam], getattr(schemas, f"default_{fam}")())
        self.assertEqual(len(result.warnings), len(schemas.SUPPORTED_FAMILIES))
        self.assertTrue(all("omitted" in w for w in result.warnings))

    def test_optional_top_level_enabled_bool(self) -> None:
        result = schemas.validate_unified_business_rules_config(
            {"unified_version": 1, "enabled": False}
        )
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        self.assertEqual(result.normalized["doctor_overrides"], schemas.default_doctor_overrides())

    def test_unknown_top_level_key_rejected(self) -> None:
        result = schemas.validate_unified_business_rules_config(
            {"unified_version": 1, "llm_instructions": "nope"}
        )
        self.assertFalse(result.valid)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Unknown top-level key", result.errors[0])

    def test_unified_version_required(self) -> None:
        result = schemas.validate_unified_business_rules_config({})
        self.assertFalse(result.valid)
        self.assertTrue(any("unified_version is required" in e for e in result.errors))

    def test_unified_version_must_be_current_int(self) -> None:
        bad = schemas.validate_unified_business_rules_config({"unified_version": 2})
        self.assertFalse(bad.valid)
        ok = schemas.validate_unified_business_rules_config({"unified_version": 1})
        self.assertTrue(ok.valid, ok.errors)

    def test_fixture_validates_and_matches_split_preview(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as f:
            raw = f.read()
        doc = yaml.safe_load(raw)
        unified_result = schemas.validate_unified_business_rules_config(doc)
        self.assertTrue(unified_result.valid, unified_result.errors)
        assert unified_result.normalized is not None

        preview = loader.load_business_rule_config_preview(
            override_base_dir=str(_REPO_ROOT / "business_rules" / "v1")
        )
        self.assertFalse(preview.has_errors)
        self.assertEqual(preview.rules_load_source, "unified")
        self.assertTrue(
            (preview.unified_file_path or "").endswith("case_creator_rules.yaml"),
        )
        self.assertEqual(unified_result.normalized, preview.effective_config)

    def test_in_memory_split_merge_matches_preview(self) -> None:
        merged: dict = {"unified_version": 1}
        for family in schemas.SUPPORTED_FAMILIES:
            path = SPLIT_ARCHIVE / f"{family}.yaml"
            with path.open("r", encoding="utf-8") as f:
                merged[family] = yaml.safe_load(f)
        result = schemas.validate_unified_business_rules_config(merged)
        self.assertTrue(result.valid, result.errors)
        preview = loader.load_business_rule_config_preview(
            override_base_dir=str(_REPO_ROOT / "business_rules" / "v1")
        )
        assert result.normalized is not None
        self.assertEqual(preview.rules_load_source, "unified")
        self.assertEqual(result.normalized, preview.effective_config)

    def test_present_invalid_family_fails(self) -> None:
        bad = {
            "unified_version": 1,
            "argen_modes": {"version": 99, "enabled": True, "contact_model_mode": "off"},
        }
        result = schemas.validate_unified_business_rules_config(bad)
        self.assertFalse(result.valid)
        self.assertTrue(any("argen_modes:" in e for e in result.errors))

    def test_doctor_route_label_override_key_allowed(self) -> None:
        doc = {
            "unified_version": 1,
            "doctor_overrides": {
                "version": 1,
                "enabled": True,
                "rules": [
                    {
                        "id": "label_override_ok",
                        "enabled": True,
                        "match": {"contains_all": ["brier", "creek"]},
                        "action": {"route_label_override_key": "serbia"},
                    }
                ],
            },
        }
        result = schemas.validate_unified_business_rules_config(doc)
        self.assertTrue(result.valid, result.errors)

    def test_doctor_route_label_override_key_rejects_unknown(self) -> None:
        doc = {
            "unified_version": 1,
            "doctor_overrides": {
                "version": 1,
                "enabled": True,
                "rules": [
                    {
                        "id": "label_override_bad",
                        "enabled": True,
                        "match": {"contains_all": ["brier", "creek"]},
                        "action": {"route_label_override_key": "serbia_path"},
                    }
                ],
            },
        }
        result = schemas.validate_unified_business_rules_config(doc)
        self.assertFalse(result.valid)
        self.assertTrue(
            any("route_label_override_key must be a known route label key" in e for e in result.errors),
            result.errors,
        )


if __name__ == "__main__":
    unittest.main()
