"""
Runtime tests for bounded argen_modes.contact_model_design_field substitution in
modeless Argen templates only.

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


class TestArgenModelessDesignFieldRuntime(unittest.TestCase):
    def _write_unified(self, folder: Path, design_value: str) -> None:
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
                "contact_model_design_field": design_value,
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
            "OrderComments": "",
        }

    def test_modeless_adzir_uses_configured_argen_design_value(self) -> None:
        from case_processor_final_clean import generate_final_xml
        from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                self._write_unified(tdp, "No")
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
                clear_argen_modes_cache()

                out = tdp / "out_adzir.xml"
                generate_final_xml(self._base_case_data("adz"), str(out))
                xml = out.read_text(encoding="utf-8")

            self.assertIn('Property name="FieldID" value="Argen_Design_Workflow"', xml)
            self.assertIn('Property name="Value" value="No"', xml)
            self.assertNotIn("{{ARGEN_DESIGN_VALUE}}", xml)
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_argen_modes_cache()

    def test_modeless_envision_uses_default_argen_design_value_when_omitted(self) -> None:
        from case_processor_final_clean import generate_final_xml
        from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache

        prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        try:
            with tempfile.TemporaryDirectory() as td:
                tdp = Path(td)
                # Omit contact_model_design_field to verify historical default.
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
                    },
                }
                with (tdp / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
                    yaml.dump(doc, f, sort_keys=False)
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
                clear_argen_modes_cache()

                out = tdp / "out_envision.xml"
                generate_final_xml(self._base_case_data("envision"), str(out))
                xml = out.read_text(encoding="utf-8")

            self.assertIn('Property name="FieldID" value="Argen_Design_Workflow"', xml)
            self.assertIn('Property name="Value" value="3Shape Automate"', xml)
            self.assertNotIn("{{ARGEN_DESIGN_VALUE}}", xml)
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_argen_modes_cache()


if __name__ == "__main__":
    unittest.main()
