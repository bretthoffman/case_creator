"""
Loader: case_creator_rules.yaml is the sole live source; missing/invalid → schema defaults.

Run from repo root:
  python -m unittest tests.test_business_rule_loader_dual_read -v
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infrastructure.config import business_rule_loader as loader
from infrastructure.config import business_rule_schemas as schemas

V1 = _REPO_ROOT / "business_rules" / "v1"
ARCHIVE = _REPO_ROOT / "business_rules" / "archive" / "v1_split_backup"
FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "unified_business_rules_baseline.yaml"


def _schema_defaults_effective() -> dict:
    return {
        "doctor_overrides": schemas.default_doctor_overrides(),
        "shade_overrides": schemas.default_shade_overrides(),
        "routing_overrides": schemas.default_routing_overrides(),
        "argen_modes": schemas.default_argen_modes(),
    }


def _archived_split_merged_document() -> dict:
    doc: dict = {"unified_version": 1}
    for fam in schemas.SUPPORTED_FAMILIES:
        p = ARCHIVE / f"{fam}.yaml"
        doc[fam] = yaml.safe_load(p.read_text(encoding="utf-8"))
    return doc


def _write_unified_from_archive(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    doc = _archived_split_merged_document()
    with (dest / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
        yaml.dump(
            doc,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


class TestBusinessRuleLoaderUnifiedOnly(unittest.TestCase):
    def test_bundled_seed_default_path_exists_in_repo(self) -> None:
        seed_path = loader._resolve_bundled_seed_path()
        self.assertTrue(seed_path.is_file(), f"missing bundled seed file at {seed_path}")
        doc = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
        self.assertIsInstance(doc, dict)
        self.assertEqual(doc.get("unified_version"), 1)

    def test_shipped_v1_uses_unified_matches_archived_baseline(self) -> None:
        v1_preview = loader.load_business_rule_config_preview(override_base_dir=str(V1))
        self.assertEqual(v1_preview.rules_load_source, "unified")
        self.assertTrue(
            (v1_preview.unified_file_path or "").endswith("case_creator_rules.yaml"),
        )
        self.assertFalse(v1_preview.has_errors)
        self.assertEqual(v1_preview.unified_validation_errors, [])

        merged = _archived_split_merged_document()
        vr = schemas.validate_unified_business_rules_config(merged)
        self.assertTrue(vr.valid, vr.errors)
        assert vr.normalized is not None
        self.assertEqual(v1_preview.effective_config, vr.normalized)

    def test_seeded_unified_file_on_disk_validates(self) -> None:
        path = V1 / "case_creator_rules.yaml"
        self.assertTrue(path.is_file(), "expected case_creator_rules.yaml")
        raw = path.read_text(encoding="utf-8")
        self.assertIn("CASE CREATOR — BUSINESS RULES", raw)
        doc = yaml.safe_load(raw)
        result = schemas.validate_unified_business_rules_config(doc)
        self.assertTrue(result.valid, result.errors)
        assert result.normalized is not None
        preview = loader.load_business_rule_config_preview(override_base_dir=str(V1))
        self.assertEqual(result.normalized, preview.effective_config)

    def test_no_unified_file_uses_defaults_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / ".placeholder").write_text("", encoding="utf-8")
            preview = loader.load_business_rule_config_preview(override_base_dir=str(base))
        self.assertEqual(preview.rules_load_source, "defaults")
        self.assertIsNone(preview.unified_file_path)
        self.assertTrue(preview.has_errors)
        self.assertEqual(preview.effective_config, _schema_defaults_effective())

    def test_invalid_unified_uses_defaults_and_logs_warning(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "case_creator_rules.yaml").write_text(
                "unified_version: 999\n", encoding="utf-8"
            )
            with self.assertLogs("infrastructure.config.business_rule_loader", level="WARNING") as cm:
                preview = loader.load_business_rule_config_preview(override_base_dir=str(base))
        self.assertEqual(preview.rules_load_source, "defaults")
        self.assertTrue(preview.unified_file_path.endswith("case_creator_rules.yaml"))
        self.assertTrue(preview.unified_validation_errors)
        self.assertTrue(preview.has_errors)
        self.assertEqual(preview.effective_config, _schema_defaults_effective())
        self.assertTrue(any("defaults" in entry.lower() for entry in cm.output), cm.output)

    def test_malformed_unified_yaml_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "case_creator_rules.yaml").write_text(
                "{ not: valid yaml [[[\n", encoding="utf-8"
            )
            preview = loader.load_business_rule_config_preview(override_base_dir=str(base))
        self.assertEqual(preview.rules_load_source, "defaults")
        self.assertTrue(preview.unified_validation_errors)
        self.assertTrue(preview.has_errors)

    def test_fixture_unified_matches_archive_baseline_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            shutil.copy(FIXTURE, base / "case_creator_rules.yaml")
            a = loader.load_business_rule_config_preview(override_base_dir=str(base))
        with tempfile.TemporaryDirectory() as td2:
            base2 = Path(td2)
            _write_unified_from_archive(base2)
            b = loader.load_business_rule_config_preview(override_base_dir=str(base2))
        self.assertEqual(a.rules_load_source, "unified")
        self.assertEqual(a.effective_config, b.effective_config)

    def test_case_creator_rules_yml_used_when_yaml_absent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            shutil.copy(FIXTURE, base / "case_creator_rules.yml")
            preview = loader.load_business_rule_config_preview(override_base_dir=str(base))
        self.assertEqual(preview.rules_load_source, "unified")
        self.assertTrue(preview.unified_file_path.endswith("case_creator_rules.yml"))

    def test_yaml_preferred_when_both_unified_names_exist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "case_creator_rules.yaml").write_text(
                "unified_version: 1\n", encoding="utf-8"
            )
            full = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
            with (base / "case_creator_rules.yml").open("w", encoding="utf-8") as f:
                yaml.dump(full, f, sort_keys=False)
            preview = loader.load_business_rule_config_preview(override_base_dir=str(base))
        self.assertEqual(preview.rules_load_source, "unified")
        self.assertTrue(preview.unified_file_path.endswith("case_creator_rules.yaml"))
        self.assertEqual(
            preview.effective_config["doctor_overrides"],
            schemas.default_doctor_overrides(),
        )
        self.assertTrue(any("Multiple unified" in w for w in preview.warnings))

    def test_source_mode_runtime_paths_still_repo_local(self) -> None:
        paths = loader.resolve_unified_runtime_paths(override_base_dir=str(V1))
        self.assertEqual(paths.mode, "override")
        self.assertEqual(Path(paths.base_dir), V1)
        self.assertEqual(Path(paths.live_unified_path), V1 / "case_creator_rules.yaml")
        self.assertIsNone(paths.bundled_seed_path)

    def test_frozen_mode_runtime_paths_use_external_and_bundled_seed(self) -> None:
        with tempfile.TemporaryDirectory() as appdata, tempfile.TemporaryDirectory() as bundled:
            seed_path = Path(bundled) / "business_rules_seed" / "v1"
            seed_path.mkdir(parents=True, exist_ok=True)
            shutil.copy(V1 / "case_creator_rules.yaml", seed_path / "case_creator_rules.yaml")

            paths = loader.resolve_unified_runtime_paths(
                force_frozen_windows=True,
                local_appdata_override=appdata,
                bundled_root_override=bundled,
            )
            self.assertEqual(paths.mode, "frozen_windows")
            self.assertEqual(
                Path(paths.live_unified_path),
                Path(appdata) / "CaseCreator" / "business_rules" / "v1" / "case_creator_rules.yaml",
            )
            assert paths.bundled_seed_path is not None
            self.assertEqual(
                Path(paths.bundled_seed_path),
                Path(bundled) / "business_rules_seed" / "v1" / "case_creator_rules.yaml",
            )

    def test_frozen_first_run_seeds_external_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as appdata, tempfile.TemporaryDirectory() as bundled:
            seed_dir = Path(bundled) / "business_rules_seed" / "v1"
            seed_dir.mkdir(parents=True, exist_ok=True)
            seeded_doc = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
            seeded_doc["unified_version"] = 1
            with (seed_dir / "case_creator_rules.yaml").open("w", encoding="utf-8") as f:
                yaml.dump(seeded_doc, f, sort_keys=False)

            with patch("infrastructure.config.business_rule_loader._is_frozen_windows", return_value=True):
                with patch.dict("os.environ", {"LOCALAPPDATA": appdata}, clear=False):
                    preview = loader.load_business_rule_config_preview()

            live = Path(appdata) / "CaseCreator" / "business_rules" / "v1" / "case_creator_rules.yaml"
            self.assertTrue(live.is_file())
            self.assertEqual(preview.rules_load_source, "unified")
            self.assertFalse(preview.has_errors)

    def test_frozen_existing_external_file_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as appdata, tempfile.TemporaryDirectory() as bundled:
            external = Path(appdata) / "CaseCreator" / "business_rules" / "v1"
            external.mkdir(parents=True, exist_ok=True)
            existing = {
                "unified_version": 1,
                "doctor_overrides": {"version": 1, "enabled": True, "rules": []},
                "shade_overrides": {
                    "version": 1,
                    "enabled": True,
                    "non_argen_shade_markers": ["ZZ"],
                    "rules": [],
                },
                "routing_overrides": {
                    "version": 1,
                    "enabled": True,
                    "template_family_route_overrides": [],
                },
                "argen_modes": {"version": 1, "enabled": True, "contact_model_mode": "off"},
            }
            live = external / "case_creator_rules.yaml"
            with live.open("w", encoding="utf-8") as f:
                yaml.dump(existing, f, sort_keys=False)
            before = live.read_text(encoding="utf-8")

            seed_dir = Path(bundled) / "business_rules_seed" / "v1"
            seed_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(FIXTURE, seed_dir / "case_creator_rules.yaml")

            with patch("infrastructure.config.business_rule_loader._is_frozen_windows", return_value=True):
                with patch.dict("os.environ", {"LOCALAPPDATA": appdata}, clear=False):
                    preview = loader.load_business_rule_config_preview()

            after = live.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertEqual(preview.rules_load_source, "unified")
            self.assertEqual(
                preview.effective_config["shade_overrides"]["non_argen_shade_markers"],
                ["ZZ"],
            )

    def test_frozen_seed_failure_uses_defaults_with_errors(self) -> None:
        with tempfile.TemporaryDirectory() as appdata:
            with patch("infrastructure.config.business_rule_loader._is_frozen_windows", return_value=True):
                with patch.dict("os.environ", {"LOCALAPPDATA": appdata}, clear=False):
                    with patch(
                        "infrastructure.config.business_rule_loader._resolve_bundled_seed_path",
                        return_value=Path(appdata) / "missing_seed" / "case_creator_rules.yaml",
                    ):
                        preview = loader.load_business_rule_config_preview()
            self.assertEqual(preview.rules_load_source, "defaults")
            self.assertTrue(preview.has_errors)
            self.assertTrue(preview.unified_validation_errors)
            self.assertEqual(preview.effective_config, _schema_defaults_effective())


if __name__ == "__main__":
    unittest.main()
