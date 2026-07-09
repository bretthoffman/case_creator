"""
Runtime tests for legacy modeless hint routes: must resolve to non-Argen ai_*_model templates.

Run:
  python -m unittest tests.test_argen_modeless_design_field_runtime -v
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


class TestModelessHintRerouteRuntime(unittest.TestCase):
    def _write_unified(self, folder: Path) -> None:
        doc = {
            "unified_version": 1,
            "doctor_overrides": {"version": 1, "enabled": True, "rules": []},
            "shade_overrides": {
                "version": 1,
                "enabled": True,
                "non_argen_shade_markers": ["C3", "A4"],
                "rules": [],
            },
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
            "argen_modes": {
                "version": 1,
                "enabled": True,
                "contact_model_mode": "off",
                "contact_model_design_field": "No",
            },
        }
        with (folder / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
            yaml.dump(doc, f, sort_keys=False)

    def _base_case_data(self, material: str) -> dict:
        return {
            "case_id": "CASE-123",
            "tooth": "8",
            "doctor": "Test Doctor",
            "material": material,
            "material_hint": {"route": "modeless", "material": material},
            "shade": "",
            "shade_usable": False,
            "has_study": False,
            "scanner": "itero",
            "is_ai": False,
            "is_anterior": False,
            "signature": False,
            "OrderComments": "",
        }

    def test_modeless_adzir_resolves_to_ai_adzir_model(self) -> None:
        from case_processor_final_clean import generate_final_xml
        from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                self._write_unified(tdp)
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
                clear_argen_modes_cache()

                out = tdp / "out_adzir.xml"
                template_dir = generate_final_xml(self._base_case_data("adz"), str(out))
                xml = out.read_text(encoding="utf-8")

            self.assertIn("ai_adzir_model", template_dir.replace("/", os.sep))
            self.assertNotIn("argen", template_dir.lower())
            self.assertNotIn("Argen_Design_Workflow", xml)
            self.assertNotIn("{{ARGEN_DESIGN_VALUE}}", xml)
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_argen_modes_cache()

    def test_modeless_envision_resolves_to_ai_envision_model(self) -> None:
        from case_processor_final_clean import generate_final_xml
        from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                self._write_unified(tdp)
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
                clear_argen_modes_cache()

                out = tdp / "out_envision.xml"
                template_dir = generate_final_xml(self._base_case_data("envision"), str(out))
                xml = out.read_text(encoding="utf-8")

            self.assertIn("ai_envision_model", template_dir.replace("/", os.sep))
            self.assertNotIn("argen", template_dir.lower())
            self.assertNotIn("Argen_Design_Workflow", xml)
            self.assertNotIn("{{ARGEN_DESIGN_VALUE}}", xml)
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_argen_modes_cache()


if __name__ == "__main__":
    unittest.main()
