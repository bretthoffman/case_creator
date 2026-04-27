"""
Post–split-retirement: effective config and resolver behavior vs archived split baseline.

Run: python -m unittest tests.test_unified_retirement_equivalence -v
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

V1 = _REPO_ROOT / "business_rules" / "v1"
ARCHIVE = _REPO_ROOT / "business_rules" / "archive" / "v1_split_backup"


class TestUnifiedRetirementEquivalence(unittest.TestCase):
    def test_runtime_resolvers_match_effective_config_baseline(self) -> None:
        """Resolvers read the same fields as an archived-split merge would normalize to."""
        from infrastructure.config.argen_modes_runtime import (
            clear_argen_modes_cache,
            resolve_contact_model_mode,
        )
        from infrastructure.config.business_rule_loader import load_business_rule_config_preview
        from infrastructure.config import business_rule_schemas as schemas
        from infrastructure.config.doctor_override_runtime import (
            clear_doctor_override_cache,
            resolve_doctor_template_override_key,
        )
        from infrastructure.config.routing_override_runtime import (
            clear_routing_override_cache,
            resolve_destination_key,
        )
        from infrastructure.config.shade_override_runtime import (
            clear_shade_override_cache,
            resolve_non_argen_shade_markers,
        )

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(V1)
            for fn in (
                clear_doctor_override_cache,
                clear_shade_override_cache,
                clear_routing_override_cache,
                clear_argen_modes_cache,
            ):
                fn()

            preview = load_business_rule_config_preview()
            self.assertEqual(preview.rules_load_source, "unified")
            eff = preview.effective_config

            merged = {"unified_version": 1}
            for fam in schemas.SUPPORTED_FAMILIES:
                merged[fam] = yaml.safe_load((ARCHIVE / f"{fam}.yaml").read_text(encoding="utf-8"))
            vr = schemas.validate_unified_business_rules_config(merged)
            self.assertTrue(vr.valid, vr.errors)
            assert vr.normalized is not None
            self.assertEqual(eff, vr.normalized)

            self.assertEqual(resolve_contact_model_mode(), eff["argen_modes"]["contact_model_mode"])
            self.assertEqual(
                resolve_non_argen_shade_markers(()),
                tuple(x.upper() for x in eff["shade_overrides"]["non_argen_shade_markers"]),
            )
            self.assertEqual(
                resolve_destination_key("something_ai_envision_study.xyz"),
                "1_9",
            )
            case = {
                "doctor": "Abby Dew",
                "material": "adz multilayer",
                "has_study": False,
                "signature": False,
                "is_anterior": False,
                "shade_usable": False,
                "scanner": "itero",
                "material_hint": {"route": "argen_adzir", "material": "adz"},
            }
            os.environ["CASE_CREATOR_DOCTOR_OUTCOMES_LIVE"] = "1"
            clear_doctor_override_cache()
            key = resolve_doctor_template_override_key(case["doctor"], case)
            self.assertEqual(key, "ai_adzir")
        finally:
            os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_doctor_override_cache()
            clear_shade_override_cache()
            clear_routing_override_cache()
            clear_argen_modes_cache()

    def test_invalid_unified_no_silent_live_rules(self) -> None:
        """Broken unified file must not imply archived split content is still active."""
        from infrastructure.config.business_rule_loader import load_business_rule_config_preview
        from infrastructure.config import business_rule_schemas as schemas

        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "case_creator_rules.yaml").write_text("unified_version: 999\n", encoding="utf-8")
            preview = load_business_rule_config_preview(override_base_dir=str(p))
        self.assertEqual(preview.rules_load_source, "defaults")
        self.assertTrue(preview.has_errors)
        self.assertEqual(
            preview.effective_config["doctor_overrides"],
            schemas.default_doctor_overrides(),
        )


if __name__ == "__main__":
    unittest.main()
