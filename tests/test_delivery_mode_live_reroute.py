"""
Live outsource/designer delivery reroute tests.

Covers:
  - default case            -> outsource (Send to AI, zipped)
  - excluded doctor         -> designer  (Send to 1.9, unzipped)
  - excluded shade          -> designer  (Send to 1.9, unzipped)
  - has_study does NOT flip delivery mode by itself
  - retired Abby/VD/Serbia routing no longer controls delivery

Run:
  python -m unittest tests.test_delivery_mode_live_reroute -v
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


def _write_config(folder: Path, designer_doctor_names, shade_markers=("C3", "A4")) -> None:
    doc = {
        "unified_version": 1,
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


class _ConfigEnv:
    """Context manager: point runtime config at a temp unified file and clear caches."""

    def __init__(self, designer_doctor_names, shade_markers=("C3", "A4")):
        self._names = designer_doctor_names
        self._markers = shade_markers

    def __enter__(self):
        self._prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        self._td = tempfile.TemporaryDirectory()
        _write_config(Path(self._td.name), self._names, self._markers)
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


class TestResolveDeliveryMode(unittest.TestCase):
    def _mode(self, **case):
        from domain.decisions.delivery_mode_selector import resolve_delivery_mode

        return resolve_delivery_mode(case)

    def test_default_case_is_outsource(self) -> None:
        with _ConfigEnv(designer_doctor_names=[]):
            self.assertEqual(self._mode(doctor="Jane Doe", shade="A2"), "outsource")

    def test_excluded_doctor_is_designer(self) -> None:
        with _ConfigEnv(designer_doctor_names=["Brier Creek"]):
            self.assertEqual(self._mode(doctor="VD Brier Creek", shade="A2"), "designer")

    def test_excluded_shade_is_designer(self) -> None:
        with _ConfigEnv(designer_doctor_names=[], shade_markers=["C3", "A4"]):
            self.assertEqual(self._mode(doctor="Jane Doe", shade="C3"), "designer")
            # tolerant of vita prefix on the shade string
            self.assertEqual(self._mode(doctor="Jane Doe", shade="Vita Classic - A4"), "designer")

    def test_has_study_does_not_flip_mode(self) -> None:
        with _ConfigEnv(designer_doctor_names=[]):
            self.assertEqual(
                self._mode(doctor="Jane Doe", shade="A2", has_study=True), "outsource"
            )
            self.assertEqual(
                self._mode(doctor="Jane Doe", shade="A2", has_study=False), "outsource"
            )

    def test_retired_abby_vd_do_not_control_delivery(self) -> None:
        # With an empty designer_doctor_names list, the old Abby/VD/Serbia special cases are
        # plain outsource — the retired routing no longer forces designer delivery.
        with _ConfigEnv(designer_doctor_names=[]):
            self.assertEqual(self._mode(doctor="Abby Dew", shade="A2"), "outsource")
            self.assertEqual(self._mode(doctor="VD Brier Creek", shade="A2"), "outsource")
        # They become designer ONLY when explicitly listed in delivery_modes.
        with _ConfigEnv(designer_doctor_names=["Brier Creek"]):
            self.assertEqual(self._mode(doctor="VD Brier Creek", shade="A2"), "designer")


class TestProcessCaseDeliveryWiring(unittest.TestCase):
    """End-to-end mapping: delivery mode -> (target_root, zip) inside process_case."""

    def _run(self, *, doctor, shade, designer_doctor_names):
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
        # Renamed-scan dir with the required PreparationScan.stl the processor checks for.
        renamed_scan_dir = wp / "scans" / "Scans" / "UNN08"
        renamed_scan_dir.mkdir(parents=True)
        (renamed_scan_dir / "PreparationScan.stl").write_bytes(b"stl")
        template_dir = wp / "tpl"
        template_dir.mkdir()
        template_xml = template_dir / "ai_envision.xml"
        template_xml.write_text("<x/>", encoding="utf-8")

        case_data = {
            "case_id": "C1",
            "doctor": doctor,
            "first": "Pat",
            "last": "Ient",
            "tooth": "8",
            "arch": "Upper",
            "shade": shade,
            "scanner": "",
            "is_ai": False,
            "is_anterior": False,
            "OrderComments": "",
            "material_hint": {"route": "regular", "material": "envision"},
        }

        results = {}
        with _ConfigEnv(designer_doctor_names=designer_doctor_names):
            with patch.multiple(
                cpf,
                get_case_detail_clean=lambda *_a, **_k: {},
                build_case_data_from_evo=lambda *_a, **_k: case_data,
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
                result = cpf.process_case("C1", str(folder), log_callback=lambda *_: None)

        results["result"] = result
        results["ai_zips"] = sorted(p.name for p in ai_dir.glob("*.zip"))
        results["ai_dirs"] = sorted(p.name for p in ai_dir.iterdir() if p.is_dir())
        results["designer_zips"] = sorted(p.name for p in designer_dir.glob("*.zip"))
        results["designer_dirs"] = sorted(p.name for p in designer_dir.iterdir() if p.is_dir())
        work.cleanup()
        return results

    def test_default_case_outsource_zipped_send_to_ai(self) -> None:
        r = self._run(doctor="Jane Doe", shade="A2", designer_doctor_names=[])
        self.assertIn(".zip", r["result"])
        self.assertEqual(len(r["ai_zips"]), 1, r)          # zipped into Send to AI
        self.assertEqual(r["ai_dirs"], [])                 # unzipped folder removed
        self.assertEqual(r["designer_zips"], [])           # nothing sent to designer
        self.assertEqual(r["designer_dirs"], [])

    def test_excluded_doctor_designer_unzipped_send_to_1_9(self) -> None:
        r = self._run(doctor="VD Brier Creek", shade="A2", designer_doctor_names=["Brier Creek"])
        self.assertNotIn(".zip", r["result"])
        self.assertEqual(len(r["designer_dirs"]), 1, r)    # unzipped folder in Send to 1.9
        self.assertEqual(r["designer_zips"], [])           # not zipped
        self.assertEqual(r["ai_zips"], [])                 # nothing sent to AI
        self.assertEqual(r["ai_dirs"], [])

    def test_excluded_shade_designer_unzipped_send_to_1_9(self) -> None:
        r = self._run(doctor="Jane Doe", shade="C3", designer_doctor_names=[])
        self.assertNotIn(".zip", r["result"])
        self.assertEqual(len(r["designer_dirs"]), 1, r)
        self.assertEqual(r["ai_zips"], [])
        self.assertEqual(r["ai_dirs"], [])


if __name__ == "__main__":
    unittest.main()
