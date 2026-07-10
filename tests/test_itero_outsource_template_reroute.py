"""
iTero + outsource cases use the same templates as non-iTero outsource; designer iTero unchanged.

Run:
  python -m unittest tests.test_itero_outsource_template_reroute -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _folder_from_path(path: str) -> str:
    return os.path.basename(os.path.dirname(path))


def _base_itero_case(**kwargs) -> dict:
    case = {
        "doctor": "Generic Lakeside Dental",
        "material": "adz multilayer",
        "has_study": False,
        "signature": False,
        "scanner": "itero",
        "shade_usable": True,
        "is_ai": False,
        "is_anterior": False,
        "shade": "A1",
        "material_hint": {"route": "regular", "material": "adz"},
    }
    case.update(kwargs)
    return case


def _clear_caches() -> None:
    from infrastructure.config.delivery_mode_runtime import clear_delivery_mode_cache
    from infrastructure.config.shade_override_runtime import clear_shade_override_cache

    clear_delivery_mode_cache()
    clear_shade_override_cache()


class _Env:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir

    def __enter__(self):
        self._prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
        os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = self._base_dir
        _clear_caches()
        return self

    def __exit__(self, *exc):
        if self._prev is None:
            os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
        else:
            os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = self._prev
        _clear_caches()
        return False


def _write_rules(
    folder: Path,
    *,
    designer_doctor_names: list[str] | None = None,
    shade_markers: list[str] | None = None,
) -> None:
    doc = {
        "unified_version": 1,
        "delivery_modes": {
            "version": 1,
            "enabled": True,
            "designer_doctor_names": list(designer_doctor_names or []),
        },
        "shade_overrides": {
            "version": 1,
            "enabled": True,
            "non_argen_shade_markers": list(shade_markers or ["C3", "A4"]),
            "rules": [],
        },
    }
    with (folder / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(doc, f, sort_keys=False)


class TestIteroOutsourceTemplateReroute(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self._rules_dir = Path(self._td.name)
        _write_rules(self._rules_dir)
        self._env = _Env(str(self._rules_dir))
        self._env.__enter__()

    def tearDown(self) -> None:
        self._env.__exit__(None, None, None)
        self._td.cleanup()

    def _select_folder(self, case_data: dict) -> str:
        from domain.decisions.template_selector import select_template_path

        with patch("builtins.print"):
            return _folder_from_path(select_template_path(case_data))

    def test_outsource_itero_adzir_anterior_uses_reg(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                is_anterior=True,
                material="adz multilayer",
                material_hint={"route": "regular", "material": "adz"},
            )
        )
        self.assertEqual(folder, "reg_adzir_anterior")

    def test_outsource_itero_adzir_study_uses_reg(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                has_study=True,
                material="adz multilayer",
                material_hint={"route": "regular", "material": "adz"},
            )
        )
        self.assertEqual(folder, "reg_adzir_study")

    def test_outsource_itero_envision_anterior_uses_reg(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                is_anterior=True,
                material="envision multilayer",
                material_hint={"route": "regular", "material": "envision"},
            )
        )
        self.assertEqual(folder, "reg_envision_anterior")

    def test_outsource_itero_envision_study_uses_reg(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                has_study=True,
                material="envision multilayer",
                material_hint={"route": "regular", "material": "envision"},
            )
        )
        self.assertEqual(folder, "reg_envision_study")

    def test_designer_itero_study_keeps_itero_template(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                has_study=True,
                shade="C3",
                material="envision multilayer",
                material_hint={"route": "regular", "material": "envision"},
            )
        )
        self.assertEqual(folder, "itero_envision_study")

    def test_designer_doctor_itero_anterior_keeps_itero_template(self) -> None:
        _write_rules(
            self._rules_dir,
            designer_doctor_names=["Jane Designer"],
            shade_markers=[],
        )
        _clear_caches()

        folder = self._select_folder(
            _base_itero_case(
                doctor="Jane Designer DDS",
                is_anterior=True,
                material="adz multilayer",
                material_hint={"route": "regular", "material": "adz"},
            )
        )
        self.assertEqual(folder, "itero_adzir_anterior")

    def test_outsource_itero_emax_uses_reg_emax(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                material="emax",
                is_anterior=True,
                material_hint={"route": "emax", "material": "emax"},
            )
        )
        self.assertEqual(folder, "reg_emax_ant")

    def test_outsource_itero_posterior_adzir_uses_itero_outsource_template(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                material="adz multilayer",
                material_hint={"route": "argen_adzir", "material": "adz"},
            )
        )
        self.assertEqual(folder, "itero_outsource_adzir")

    def test_outsource_itero_posterior_envision_uses_itero_outsource_template(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                material="envision multilayer",
                material_hint={"route": "argen_envision", "material": "envision"},
            )
        )
        self.assertEqual(folder, "itero_outsource_envision")

    def test_outsource_itero_posterior_envision_differs_from_trios(self) -> None:
        from domain.decisions.template_selector import select_template_path

        case = _base_itero_case(
            material="envision multilayer",
            material_hint={"route": "argen_envision", "material": "envision"},
        )
        trios_case = dict(case, scanner="trios")
        with patch("builtins.print"):
            itero_folder = _folder_from_path(select_template_path(case))
            trios_folder = _folder_from_path(select_template_path(trios_case))
        self.assertEqual(itero_folder, "itero_outsource_envision")
        self.assertEqual(trios_folder, "ai_envision_model")

    def test_designer_itero_posterior_keeps_ai_envision(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                shade="C3",
                material="envision multilayer",
                material_hint={"route": "argen_envision", "material": "envision"},
            )
        )
        self.assertEqual(folder, "ai_envision")

    def test_non_itero_outsource_study_unchanged(self) -> None:
        folder = self._select_folder(
            _base_itero_case(
                scanner="3shape",
                has_study=True,
                material="envision multilayer",
                material_hint={"route": "regular", "material": "envision"},
            )
        )
        self.assertEqual(folder, "reg_envision_study")


if __name__ == "__main__":
    unittest.main()
