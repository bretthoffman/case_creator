"""
Shade substring flags (custom / photos) route cases to designer delivery.

Run:
  python -m unittest tests.test_shade_designer_flags -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _clear_caches() -> None:
    from infrastructure.config.delivery_mode_runtime import clear_delivery_mode_cache
    from infrastructure.config.shade_override_runtime import clear_shade_override_cache

    clear_delivery_mode_cache()
    clear_shade_override_cache()


def _write_config(folder: Path) -> None:
    doc = {
        "unified_version": 1,
        "shade_overrides": {
            "version": 1,
            "enabled": True,
            "non_argen_shade_markers": ["C3", "A4"],
            "rules": [],
        },
        "delivery_modes": {
            "version": 1,
            "enabled": True,
            "designer_doctor_names": [],
        },
    }
    with (folder / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(doc, f, sort_keys=False)


class _ConfigEnv:
    def __enter__(self):
        self._prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        self._td = tempfile.TemporaryDirectory()
        _write_config(Path(self._td.name))
        os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = self._td.name
        _clear_caches()
        return self

    def __exit__(self, *exc):
        if self._prev is None:
            os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
        else:
            os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = self._prev
        self._td.cleanup()
        _clear_caches()
        return False


class TestShadeSubstringDetection(unittest.TestCase):
    def test_custom_case_insensitive_substring(self) -> None:
        import template_utils as tu

        self.assertTrue(tu.shade_field_contains_custom("A1 Custom"))
        self.assertTrue(tu.shade_field_contains_custom("CUSTOMIZATION"))
        self.assertFalse(tu.shade_field_contains_custom("A2"))

    def test_photos_case_insensitive_substring(self) -> None:
        import template_utils as tu

        self.assertTrue(tu.shade_field_contains_photos("See Photos"))
        self.assertTrue(tu.shade_field_contains_photos("PHOTOSHOOT"))
        self.assertFalse(tu.shade_field_contains_photos("A2"))

    def test_apply_flags_respects_toggles(self) -> None:
        import template_utils as tu

        case = {"shade_raw": "A1 Custom, see photos"}
        with patch.object(tu, "FLAG_CUSTOM_SHADE_TO_DESIGNER", True), patch.object(
            tu, "FLAG_PHOTOS_SHADE_TO_DESIGNER", True
        ):
            tu.apply_shade_designer_flags(case)
        self.assertTrue(case["shade_custom"])
        self.assertTrue(case["shade_photos"])

        case2 = {"shade_raw": "A1 Custom, see photos"}
        with patch.object(tu, "FLAG_CUSTOM_SHADE_TO_DESIGNER", False), patch.object(
            tu, "FLAG_PHOTOS_SHADE_TO_DESIGNER", False
        ):
            tu.apply_shade_designer_flags(case2)
        self.assertFalse(case2["shade_custom"])
        self.assertFalse(case2["shade_photos"])

    def test_reason_lines(self) -> None:
        import template_utils as tu

        lines = tu.shade_designer_reason_lines(
            {"shade_custom": True, "shade_photos": True}
        )
        self.assertEqual(lines, ["Custom Shade", "See Photos"])


class TestShadeDesignerDeliveryMode(unittest.TestCase):
    def _mode(self, **case):
        from domain.decisions.delivery_mode_selector import resolve_delivery_mode
        from template_utils import apply_shade_designer_flags

        apply_shade_designer_flags(case)
        return resolve_delivery_mode(case)

    def test_custom_shade_routes_designer(self) -> None:
        with _ConfigEnv():
            self.assertEqual(
                self._mode(doctor="Jane Doe", shade="A2", shade_raw="Vita A1 Custom"),
                "designer",
            )

    def test_photos_shade_routes_designer(self) -> None:
        with _ConfigEnv():
            self.assertEqual(
                self._mode(doctor="Jane Doe", shade="A2", shade_raw="See Photos"),
                "designer",
            )

    def test_normal_shade_stays_outsource(self) -> None:
        with _ConfigEnv():
            self.assertEqual(
                self._mode(doctor="Jane Doe", shade="A2", shade_raw="A2"),
                "outsource",
            )


class TestShadeDesignerProcessWiring(unittest.TestCase):
    def test_custom_shade_designer_unzipped(self) -> None:
        import case_processor_final_clean as cpf

        work = tempfile.TemporaryDirectory()
        wp = Path(work.name)
        folder = wp / "input_case"
        folder.mkdir()
        ai_dir = wp / "Send to AI"
        ai_dir.mkdir()
        designer_dir = wp / "Send to 1.9"
        designer_dir.mkdir()
        failed_dir = wp / "Failed"
        failed_dir.mkdir()
        renamed_scan_dir = wp / "scans" / "Scans" / "UNN08"
        renamed_scan_dir.mkdir(parents=True)
        (renamed_scan_dir / "PreparationScan.stl").write_bytes(b"stl")
        template_dir = wp / "tpl"
        template_dir.mkdir()
        template_xml = template_dir / "ai_envision.xml"
        template_xml.write_text("<x/>", encoding="utf-8")

        case_data = {
            "case_id": "C1",
            "doctor": "Jane Doe",
            "first": "Pat",
            "last": "Ient",
            "tooth": "8",
            "arch": "Upper",
            "shade": "A2",
            "shade_raw": "A2 Custom",
            "scanner": "",
            "is_ai": False,
            "is_anterior": False,
            "OrderComments": "",
            "material_hint": {"route": "regular", "material": "envision"},
        }

        logs = []
        with _ConfigEnv():
            with patch.multiple(
                cpf,
                get_case_detail_clean=lambda *_a, **_k: {},
                build_case_data_from_evo=lambda *_a, **_k: dict(case_data),
                evaluate_initial_manual_review=lambda *_a, **_k: SimpleNamespace(
                    requires_manual_review=False, message=None, detail=None, return_value=None
                ),
                select_template_path=lambda cd: str(template_xml),
                generate_final_xml=lambda cd, out: str(template_dir),
                rename_scans=lambda *_a, **_k: (False, str(renamed_scan_dir)),
                SEND_TO_AI_PATH=str(ai_dir),
                SEND_TO_1_9_PATH=str(designer_dir),
                FAILED_IMPORT_PATH=str(failed_dir),
            ):
                result = cpf.process_case("C1", str(folder), log_callback=logs.append)

        work.cleanup()
        self.assertNotIn(".zip", result)
        self.assertIn("🧑‍🎓 DESIGNER CASE", logs)
        self.assertIn("Custom Shade", logs)


if __name__ == "__main__":
    unittest.main()
