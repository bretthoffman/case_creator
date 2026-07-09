"""
Template routing: legacy argen_* folder keys must resolve to non-Argen templates.

Run:
  python -m unittest tests.test_template_argen_reroute -v
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _folder_from_select(case_data: dict) -> str:
    from template_utils import select_template

    path = select_template(case_data)
    return os.path.basename(os.path.dirname(path))


class TestMapMaterialToXml(unittest.TestCase):
    def test_adz_returns_adzir_for_non_study(self) -> None:
        from template_utils import map_material_to_xml

        value = map_material_to_xml(
            {"material": "adz multilayer", "has_study": False}
        )
        self.assertEqual(value, "Adzir")
        self.assertNotIn("argen", value.lower())

    def test_envision_returns_multi_layer_for_non_study(self) -> None:
        from template_utils import map_material_to_xml

        value = map_material_to_xml(
            {"material": "envision multilayer", "has_study": False}
        )
        self.assertEqual(value, "Multi layer")
        self.assertNotIn("argen", value.lower())

    def test_study_cases_use_same_priority_materials(self) -> None:
        from template_utils import map_material_to_xml

        self.assertEqual(
            map_material_to_xml({"material": "adz", "has_study": True}),
            "Adzir",
        )
        self.assertEqual(
            map_material_to_xml({"material": "envision", "has_study": True}),
            "Multi layer",
        )


class TestArgenTemplateReroute(unittest.TestCase):
    def test_legacy_argen_envision_itero_resolves_to_ai_envision(self) -> None:
        from domain.rules import template_rules

        path = template_rules.build_template_path(
            "argen_envision",
            {"scanner": "itero"},
        )
        self.assertIn(os.path.join("ai_envision", "ai_envision.xml"), path.replace("/", os.sep))
        self.assertNotIn("argen", path.lower())

    def test_legacy_argen_envision_non_itero_resolves_to_ai_envision_model(self) -> None:
        from domain.rules import template_rules

        path = template_rules.build_template_path(
            "argen_envision",
            {"scanner": "3shape"},
        )
        self.assertIn(
            os.path.join("ai_envision_model", "ai_envision_model.xml"),
            path.replace("/", os.sep),
        )
        self.assertNotIn("argen", path.lower())

    def test_legacy_argen_adzir_itero_resolves_to_ai_adzir(self) -> None:
        from domain.rules import template_rules

        path = template_rules.build_template_path(
            "argen_adzir",
            {"scanner": "itero"},
        )
        self.assertIn(os.path.join("ai_adzir", "ai_adzir.xml"), path.replace("/", os.sep))
        self.assertNotIn("argen", path.lower())

    def test_legacy_argen_adzir_non_itero_resolves_to_ai_adzir_model(self) -> None:
        from domain.rules import template_rules

        path = template_rules.build_template_path(
            "argen_adzir",
            {"scanner": "trios"},
        )
        self.assertIn(
            os.path.join("ai_adzir_model", "ai_adzir_model.xml"),
            path.replace("/", os.sep),
        )
        self.assertNotIn("argen", path.lower())

    def test_modeless_legacy_keys_resolve_to_ai_model_templates(self) -> None:
        from domain.rules import template_rules

        for legacy, expected in (
            ("argen_modeless_envision", "ai_envision_model"),
            ("argen_modeless_adzir", "ai_adzir_model"),
        ):
            path = template_rules.build_template_path(legacy, {"scanner": "itero"})
            self.assertIn(
                os.path.join(expected, f"{expected}.xml"),
                path.replace("/", os.sep),
            )
            self.assertNotIn("argen", path.lower())

    def test_generic_argen_hint_adz_itero_selects_ai_adzir(self) -> None:
        folder = _folder_from_select(
            {
                "doctor": "Generic Lakeside Dental",
                "material": "adz multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "itero",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "material_hint": {"route": "argen_adzir", "material": "adz"},
            }
        )
        self.assertEqual(folder, "ai_adzir")

    def test_generic_argen_hint_adz_non_itero_selects_ai_adzir_model(self) -> None:
        folder = _folder_from_select(
            {
                "doctor": "Generic Lakeside Dental",
                "material": "adz multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "3shape",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "material_hint": {"route": "argen_adzir", "material": "adz"},
            }
        )
        self.assertEqual(folder, "ai_adzir_model")

    def test_generic_argen_hint_envision_itero_selects_ai_envision(self) -> None:
        folder = _folder_from_select(
            {
                "doctor": "Generic Lakeside Dental",
                "material": "envision multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "itero",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "material_hint": {"route": "argen_envision", "material": "envision"},
            }
        )
        self.assertEqual(folder, "ai_envision")

    def test_generic_argen_hint_envision_non_itero_selects_ai_envision_model(self) -> None:
        folder = _folder_from_select(
            {
                "doctor": "Generic Lakeside Dental",
                "material": "envision multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "3shape",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "material_hint": {"route": "argen_envision", "material": "envision"},
            }
        )
        self.assertEqual(folder, "ai_envision_model")

    def test_modeless_hint_selects_ai_model_template(self) -> None:
        folder = _folder_from_select(
            {
                "doctor": "Abby Dew",
                "material": "adz multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "3shape",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "material_hint": {"route": "modeless", "material": "adz"},
            }
        )
        self.assertEqual(folder, "ai_adzir_model")

    def test_non_argen_study_route_unchanged(self) -> None:
        folder = _folder_from_select(
            {
                "doctor": "Generic Lakeside Dental",
                "material": "envision multilayer",
                "has_study": True,
                "signature": False,
                "scanner": "3shape",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "material_hint": {"route": "regular", "material": "envision"},
            }
        )
        self.assertEqual(folder, "reg_envision_study")

    def test_doctor_override_argen_key_reroutes_via_build_template_path(self) -> None:
        from domain.decisions.template_selector import select_template_path
        from domain.rules import template_rules

        case = {
            "doctor": "Abby Dew",
            "material": "adz multilayer",
            "has_study": False,
            "signature": False,
            "scanner": "itero",
            "shade_usable": True,
            "is_ai": False,
            "is_anterior": False,
            "shade": "A1",
            "material_hint": {"route": "argen_adzir", "material": "adz"},
        }

        with patch(
            "infrastructure.config.doctor_override_runtime.resolve_doctor_template_override_with_source",
            return_value=("argen_envision", "outcomes"),
        ):
            path = select_template_path(case)

        self.assertEqual(
            path,
            template_rules.build_template_path("ai_envision_model", case),
        )
        self.assertIn("ai_envision_model", path)
        self.assertNotIn("argen", path.lower())

    def test_outsource_itero_generated_xml_matches_trios_models_on(self) -> None:
        from case_processor_final_clean import generate_final_xml

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "itero.xml"
            case = {
                "case_id": "ITERO-001",
                "tooth": "8",
                "doctor": "Generic Lakeside Dental",
                "material": "envision multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "itero",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "OrderComments": "",
                "due_date": "2026-07-09",
                "material_hint": {"route": "argen_envision", "material": "envision"},
            }
            generate_final_xml(case, str(out))
            xml = out.read_text(encoding="utf-8")

        self.assertIn("ModelBuilder", xml)
        self.assertIn("Antagonist model", xml)
        self.assertNotIn("ScanItRestoration", xml)

    def test_designer_itero_generated_xml_preserves_models_off(self) -> None:
        from case_processor_final_clean import generate_final_xml

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "itero_designer.xml"
            case = {
                "case_id": "ITERO-DESIGNER-001",
                "tooth": "8",
                "doctor": "Generic Lakeside Dental",
                "material": "envision multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "itero",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "C3",
                "OrderComments": "",
                "due_date": "2026-07-09",
                "material_hint": {"route": "argen_envision", "material": "envision"},
            }
            generate_final_xml(case, str(out))
            xml = out.read_text(encoding="utf-8")

        self.assertIn("ScanItRestoration", xml)
        self.assertIn('ScanType" value="stAntagonist"', xml)
        self.assertNotIn("ModelBuilder", xml)
        self.assertNotIn("Antagonist model", xml)

    def test_non_itero_generated_xml_enables_models(self) -> None:
        from case_processor_final_clean import generate_final_xml

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "trios.xml"
            case = {
                "case_id": "TRIOS-001",
                "tooth": "8",
                "doctor": "Generic Lakeside Dental",
                "material": "envision multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "3shape",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "OrderComments": "",
                "due_date": "2026-07-09",
                "material_hint": {"route": "argen_envision", "material": "envision"},
            }
            generate_final_xml(case, str(out))
            xml = out.read_text(encoding="utf-8")

        self.assertIn("ModelBuilder", xml)
        self.assertIn("Antagonist model", xml)
        self.assertIn("Multi layer", xml)
        self.assertNotIn("ArgenZ ST Multilayer Pre-Shaded", xml)


    def test_generate_final_xml_uses_non_argen_material_names(self) -> None:
        from case_processor_final_clean import generate_final_xml

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "case.xml"
            case = {
                "case_id": "MAT-001",
                "tooth": "8",
                "doctor": "Generic Lakeside Dental",
                "material": "envision multilayer",
                "has_study": False,
                "signature": False,
                "scanner": "itero",
                "shade_usable": True,
                "is_ai": False,
                "is_anterior": False,
                "shade": "A1",
                "OrderComments": "",
                "due_date": "2026-07-09",
                "material_hint": {"route": "argen_envision", "material": "envision"},
            }
            generate_final_xml(case, str(out))
            xml = out.read_text(encoding="utf-8")

        self.assertIn("Multi layer", xml)
        self.assertNotIn("ArgenZ ST Multilayer Pre-Shaded", xml)
        self.assertNotIn("ArgenZ HT+ Multilayer", xml)


class TestZipUsesNonArgenTemplateFiles(unittest.TestCase):
    def test_itero_zip_preserves_models_off_template(self) -> None:
        import case_processor_final_clean as cpf

        with tempfile.TemporaryDirectory() as td:
            wp = Path(td)
            ai_tpl = _REPO_ROOT / "templates" / "ai_envision"
            self._run_zip_case(cpf, wp, ai_tpl, scanner="itero")

    def test_non_itero_zip_uses_models_on_template(self) -> None:
        import case_processor_final_clean as cpf

        with tempfile.TemporaryDirectory() as td:
            wp = Path(td)
            zips = self._run_zip_case(
                cpf,
                wp,
                _REPO_ROOT / "templates" / "ai_envision_model",
                scanner="trios",
                use_real_xml=True,
            )
            with zipfile.ZipFile(zips[0], "r") as zf:
                case_xml_name = next(
                    n
                    for n in zf.namelist()
                    if n.endswith(".xml") and not n.endswith("Materials.xml")
                )
                with zf.open(case_xml_name) as xf:
                    case_xml = xf.read().decode("utf-8")
            self.assertIn("ModelBuilder", case_xml)
            self.assertIn("Antagonist model", case_xml)

    def _run_zip_case(
        self,
        cpf,
        wp: Path,
        ai_tpl: Path,
        *,
        scanner: str,
        use_real_xml: bool = False,
    ):
        self.assertTrue((ai_tpl / "Materials.xml").is_file())

        case_dir = wp / "case_in"
        case_dir.mkdir()
        (case_dir / "dummy.pdf").write_text("rx", encoding="utf-8")

        renamed_scan_dir = wp / "scans" / "Scans" / "UNN08"
        renamed_scan_dir.mkdir(parents=True)
        (renamed_scan_dir / "PreparationScan.stl").write_bytes(b"stl")

        ai_out = wp / "Send to AI"
        designer_out = wp / "Send to 1.9"
        failed_out = wp / "Failed"
        ai_out.mkdir()
        designer_out.mkdir()
        failed_out.mkdir()

        case_data = {
            "case_id": "ZIP-TEST-001",
            "first": "Test",
            "last": "Patient",
            "doctor": "Generic Lakeside Dental",
            "material": "envision multilayer",
            "has_study": False,
            "signature": False,
            "scanner": scanner,
            "shade_usable": True,
            "is_ai": False,
            "is_anterior": False,
            "shade": "A1",
            "tooth": "8",
            "arch": "Upper",
            "due_date": "2026-07-09",
            "OrderComments": "",
            "material_hint": {"route": "argen_envision", "material": "envision"},
        }

        template_xml = ai_tpl / f"{ai_tpl.name}.xml"
        patches = dict(
            get_case_detail_clean=lambda *_a, **_k: {},
            build_case_data_from_evo=lambda *_a, **_k: dict(case_data),
            evaluate_initial_manual_review=lambda *_a, **_k: SimpleNamespace(
                requires_manual_review=False,
                message=None,
                detail=None,
                return_value=None,
            ),
            rename_scans=lambda *_a, **_k: (False, str(renamed_scan_dir)),
            SEND_TO_AI_PATH=str(ai_out),
            SEND_TO_1_9_PATH=str(designer_out),
            FAILED_IMPORT_PATH=str(failed_out),
        )
        if not use_real_xml:
            patches["select_template_path"] = lambda cd: str(template_xml)
            patches["generate_final_xml"] = lambda cd, out: str(ai_tpl)

        with patch.multiple(cpf, **patches):
            result = cpf.process_case(
                "ZIP-TEST-001",
                str(case_dir),
                log_callback=lambda *_: None,
            )

        self.assertIn(".zip", result)
        zips = list(ai_out.glob("*.zip"))
        self.assertEqual(len(zips), 1)

        with zipfile.ZipFile(zips[0], "r") as zf:
            names = zf.namelist()
            self.assertTrue(any(n.endswith("Materials.xml") for n in names))
            self.assertFalse(any("argen" in n.lower() for n in names))
            materials_entry = next(n for n in names if n.endswith("Materials.xml"))
            with zf.open(materials_entry) as mf:
                zipped_hash = hashlib.sha256(mf.read()).hexdigest()
            with (ai_tpl / "Materials.xml").open("rb") as src:
                source_hash = hashlib.sha256(src.read()).hexdigest()
            self.assertEqual(zipped_hash, source_hash)

        return zips

    def test_zip_includes_non_argen_materials_from_resolved_template_dir(self) -> None:
        import case_processor_final_clean as cpf

        with tempfile.TemporaryDirectory() as td:
            wp = Path(td)
            ai_tpl = _REPO_ROOT / "templates" / "ai_envision"
            self._run_zip_case(cpf, wp, ai_tpl, scanner="itero")


if __name__ == "__main__":
    unittest.main()
