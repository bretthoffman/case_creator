"""EMax material detection, manual-review acceptance, and template routing."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _base_case(*, is_anterior: bool, has_study: bool = False) -> dict:
    return {
        "material": "emax",
        "has_study": has_study,
        "scanner": "",
        "shade_usable": True,
        "signature": False,
        "is_ai": False,
        "is_anterior": is_anterior,
        "doctor": "Test Doctor",
        "shade": "A2",
        "material_hint": {"route": "emax", "material": "emax"},
    }


class TestEmaxMaterialRules(unittest.TestCase):
    def test_ips_emax_route(self) -> None:
        from domain.rules import material_rules

        services = [{"description": "IPS e.max Crown #8"}]
        self.assertEqual(material_rules.route_from_services(services), "emax")
        self.assertEqual(material_rules.material_from_services(services), "emax")

    def test_lithium_disilicate_route(self) -> None:
        from domain.rules import material_rules

        services = [{"description": "Lithium Disilicate single crown"}]
        self.assertEqual(material_rules.route_from_services(services), "emax")

    def test_emax_zirconia_stays_adzir(self) -> None:
        from domain.rules import material_rules

        services = [{"description": "EMax Zirconia crown"}]
        self.assertEqual(material_rules.route_from_services(services), "argen_adzir")
        self.assertNotEqual(material_rules.material_from_services(services), "emax")


class TestEmaxManualReview(unittest.TestCase):
    def test_emax_route_allowed(self) -> None:
        from domain.rules import manual_review_rules

        self.assertTrue(manual_review_rules.route_is_allowed("emax"))

    def test_emax_case_not_manual_review(self) -> None:
        from domain.decisions.manual_review_selector import evaluate_initial_manual_review

        clean = {
            "services": [
                {
                    "description": "IPS e.max Crown",
                    "units": 1,
                    "toothlist": [{"tooth_num": "8"}],
                }
            ]
        }
        case_data = {
            "material_hint": {"route": "emax", "material": "emax"},
            "is_anterior": True,
        }
        decision = evaluate_initial_manual_review(clean, case_data)
        self.assertFalse(decision.requires_manual_review)


class TestEmaxTemplateRouting(unittest.TestCase):
    def _folder(self, case_data: dict) -> str:
        from template_utils import select_template

        with patch("builtins.print"):
            path = select_template(case_data)
        return os.path.basename(os.path.dirname(path))

    def test_anterior_routes_to_reg_emax_ant(self) -> None:
        self.assertEqual(self._folder(_base_case(is_anterior=True)), "reg_emax_ant")

    def test_posterior_routes_to_reg_emax_post(self) -> None:
        self.assertEqual(self._folder(_base_case(is_anterior=False)), "reg_emax_post")

    def test_anterior_study_routes_to_reg_emax_ant_study(self) -> None:
        self.assertEqual(
            self._folder(_base_case(is_anterior=True, has_study=True)),
            "reg_emax_ant_study",
        )

    def test_posterior_study_routes_to_reg_emax_post_study(self) -> None:
        self.assertEqual(
            self._folder(_base_case(is_anterior=False, has_study=True)),
            "reg_emax_post_study",
        )


class TestEmaxMapMaterialToXml(unittest.TestCase):
    def test_anterior_material_label(self) -> None:
        from template_utils import map_material_to_xml

        value = map_material_to_xml(
            {
                "material": "emax",
                "is_anterior": True,
                "material_hint": {"route": "emax"},
            }
        )
        self.assertEqual(value, "EMax Anterior")

    def test_posterior_material_label(self) -> None:
        from template_utils import map_material_to_xml

        value = map_material_to_xml(
            {
                "material": "emax",
                "is_anterior": False,
                "material_hint": {"route": "emax"},
            }
        )
        self.assertEqual(value, "EMax Posterior")


if __name__ == "__main__":
    unittest.main()
