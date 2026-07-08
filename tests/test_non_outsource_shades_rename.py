"""
Focused proof for the shade-exclusion field rename:

    shade_overrides.non_argen_shade_markers  ->  shade_overrides.non_outsource_shades

Covers:
  1. the new field name validates and normalizes to ``non_outsource_shades``
  2. the legacy ``non_argen_shade_markers`` alias is still accepted (normalized to the new key)
  3. when BOTH are present, the new name wins and the legacy one is ignored (with a warning)
  4. the canonical + seed YAML use ONLY the new field name, second-from-bottom (directly above
     ``delivery_modes``)
  5. the live delivery decision still treats those shades as designer exclusions, via both the
     new field name AND the legacy alias
  6. the beginner-facing docs (README + edit prompt) teach only the new field name

Run:
  python -m unittest tests.test_non_outsource_shades_rename -v
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

CANONICAL_YAML = _REPO_ROOT / "business_rules" / "v1" / "case_creator_rules.yaml"
SEED_YAML = _REPO_ROOT / "business_rules_seed" / "v1" / "case_creator_rules.yaml"
README = _REPO_ROOT / "business_rules" / "v1" / "README.md"
EDIT_PROMPT = _REPO_ROOT / "business_rules" / "v1" / "CASE_CREATOR_RULES_EDIT_PROMPT.md"

LEGACY_FIELD = "non_argen_shade_markers"
NEW_FIELD = "non_outsource_shades"


class TestSchemaRenameAndAlias(unittest.TestCase):
    def test_new_field_name_normalizes(self) -> None:
        r = schemas.validate_shade_overrides(
            {"version": 1, "enabled": True, NEW_FIELD: ["C3", "A4"], "rules": []}
        )
        self.assertTrue(r.valid, r.errors)
        assert r.normalized is not None
        self.assertIn(NEW_FIELD, r.normalized)
        self.assertNotIn(LEGACY_FIELD, r.normalized)
        self.assertEqual(r.normalized[NEW_FIELD], ["C3", "A4"])

    def test_legacy_alias_still_accepted(self) -> None:
        r = schemas.validate_shade_overrides(
            {"version": 1, "enabled": True, LEGACY_FIELD: ["C3", "A4"], "rules": []}
        )
        self.assertTrue(r.valid, r.errors)
        assert r.normalized is not None
        # Legacy input normalizes onto the canonical new key.
        self.assertEqual(r.normalized[NEW_FIELD], ["C3", "A4"])
        self.assertNotIn(LEGACY_FIELD, r.normalized)
        self.assertTrue(
            any("legacy" in w.lower() for w in r.warnings),
            f"expected a legacy-alias warning, got {r.warnings}",
        )

    def test_both_present_new_name_wins(self) -> None:
        r = schemas.validate_shade_overrides(
            {
                "version": 1,
                "enabled": True,
                NEW_FIELD: ["C3"],
                LEGACY_FIELD: ["ZZ"],
                "rules": [],
            }
        )
        self.assertTrue(r.valid, r.errors)
        assert r.normalized is not None
        self.assertEqual(r.normalized[NEW_FIELD], ["C3"])
        self.assertTrue(
            any("both" in w.lower() for w in r.warnings),
            f"expected a both-present precedence warning, got {r.warnings}",
        )

    def test_default_shape_uses_new_field(self) -> None:
        default = schemas.default_shade_overrides()
        self.assertIn(NEW_FIELD, default)
        self.assertNotIn(LEGACY_FIELD, default)


class TestCanonicalYamlLayout(unittest.TestCase):
    def _assert_layout(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(f"{NEW_FIELD}:", text, f"{path} should use the new field name")
        self.assertNotIn(
            f"{LEGACY_FIELD}:", text, f"{path} must not use the legacy field name"
        )
        doc = yaml.safe_load(text)
        top_keys = [k for k in doc.keys() if k != "unified_version"]
        # Shade block must be the second-from-bottom family, directly above delivery_modes.
        self.assertEqual(
            top_keys[-2:],
            ["shade_overrides", "delivery_modes"],
            f"unexpected tail ordering in {path}: {top_keys}",
        )
        self.assertIn(NEW_FIELD, doc["shade_overrides"])

    def test_canonical_layout(self) -> None:
        self._assert_layout(CANONICAL_YAML)

    def test_seed_layout(self) -> None:
        self._assert_layout(SEED_YAML)

    def test_canonical_and_seed_identical(self) -> None:
        self.assertEqual(
            CANONICAL_YAML.read_text(encoding="utf-8"),
            SEED_YAML.read_text(encoding="utf-8"),
        )


class TestLiveDeliveryUsesRenamedField(unittest.TestCase):
    """The live outsource-vs-designer decision still treats these shades as designer exclusions."""

    def _resolve_mode_with_shade_config(self, field_name: str) -> str:
        from domain.decisions.delivery_mode_selector import resolve_delivery_mode
        from infrastructure.config.delivery_mode_runtime import clear_delivery_mode_cache
        from infrastructure.config.shade_override_runtime import clear_shade_override_cache

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                doc = {
                    "unified_version": 1,
                    "shade_overrides": {
                        "version": 1,
                        "enabled": True,
                        field_name: ["C3"],
                        "rules": [],
                    },
                    "delivery_modes": {
                        "version": 1,
                        "enabled": True,
                        "designer_doctor_names": [],
                    },
                }
                Path(td, "case_creator_rules.yaml").write_text(
                    yaml.dump(doc, sort_keys=False), encoding="utf-8"
                )
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = td
                clear_shade_override_cache()
                clear_delivery_mode_cache()
                return resolve_delivery_mode({"doctor": "Nobody Special", "shade": "C3"})
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_shade_override_cache()
            clear_delivery_mode_cache()

    def test_new_field_routes_shade_to_designer(self) -> None:
        self.assertEqual(self._resolve_mode_with_shade_config(NEW_FIELD), "designer")

    def test_legacy_alias_still_routes_shade_to_designer(self) -> None:
        self.assertEqual(self._resolve_mode_with_shade_config(LEGACY_FIELD), "designer")


class TestBeginnerDocsTeachNewName(unittest.TestCase):
    def test_readme_uses_new_field_only(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn(NEW_FIELD, text)
        self.assertNotIn(LEGACY_FIELD, text)

    def test_edit_prompt_uses_new_field_only(self) -> None:
        text = EDIT_PROMPT.read_text(encoding="utf-8")
        self.assertIn(NEW_FIELD, text)
        self.assertNotIn(LEGACY_FIELD, text)


if __name__ == "__main__":
    unittest.main()
