"""
Offline / flag parity harness: template_utils.select_template vs doctor_policy_resolver
and live resolve_doctor_template_override_key flag behavior.

Run: python tests/doctor_policy_parity_harness.py
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ABBY = "Abby Dew"
VD = "Jane Britt Brier Creek"


def _folder_from_select(case_data: dict) -> str:
    from template_utils import select_template

    p = select_template(case_data)
    return os.path.basename(os.path.dirname(p))


def _base_case(doctor: str, **kwargs) -> dict:
    d = {
        "doctor": doctor,
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
    d.update(kwargs)
    return d


def _offline_fixture_text() -> str:
    return (_REPO_ROOT / "tests" / "fixtures" / "doctor_policy_abby_vd_offline.yaml").read_text(
        encoding="utf-8"
    )


def _argen_modes_yaml(contact_model_mode: str) -> str:
    # Quote so YAML 1.1 does not treat on/off as booleans.
    return (
        "version: 1\nenabled: true\n"
        f'contact_model_mode: "{contact_model_mode}"\n'
    )


@contextmanager
def _business_rules_dir(*files: Tuple[str, str]) -> Iterator[Path]:
    """
    Temp dir with a single ``case_creator_rules.yaml`` built from legacy (filename, content) pairs.
    Sets CASE_CREATOR_BUSINESS_RULES_DIR.
    """
    from infrastructure.config import business_rule_schemas as _schemas
    from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache
    from infrastructure.config.doctor_override_runtime import clear_doctor_override_cache
    from infrastructure.config.routing_override_runtime import clear_routing_override_cache
    from infrastructure.config.shade_override_runtime import clear_shade_override_cache

    filename_to_family = {
        n: fam for fam, names in _schemas.FAMILY_FILE_CANDIDATES.items() for n in names
    }

    prev = os.environ.get("CASE_CREATOR_BUSINESS_RULES_DIR")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        doc: Dict[str, Any] = {"unified_version": 1}
        for name, content in files:
            fam = filename_to_family.get(name)
            if fam is None:
                raise ValueError(
                    f"_business_rules_dir: unsupported filename {name!r} "
                    "(expected doctor_overrides.yaml, argen_modes.yaml, etc.)."
                )
            doc[fam] = yaml.safe_load(content)
        unified_body = yaml.dump(
            doc,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )
        (tdp / "case_creator_rules.yaml").write_text(unified_body, encoding="utf-8")
        os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
        clear_doctor_override_cache()
        clear_argen_modes_cache()
        clear_routing_override_cache()
        clear_shade_override_cache()
        try:
            yield tdp
        finally:
            if prev is None:
                os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
            else:
                os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = prev
            clear_doctor_override_cache()
            clear_argen_modes_cache()
            clear_routing_override_cache()
            clear_shade_override_cache()


def _load_offline_fixture() -> dict:
    path = _REPO_ROOT / "tests" / "fixtures" / "doctor_policy_abby_vd_offline.yaml"
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    from infrastructure.config import business_rule_schemas as schemas

    result = schemas.validate_doctor_overrides(raw)
    assert result.valid, result.errors
    assert result.normalized is not None
    return result.normalized


def _parity_rows() -> List[Dict[str, Any]]:
    from domain.decisions.doctor_policy_resolver import resolve_doctor_policy_template_key

    offline_cfg = _load_offline_fixture()
    rows: List[Dict[str, Any]] = []

    # (name, case_builder, mode)  mode: match | no_policy
    scenarios: List[Tuple[str, Callable[[], dict], str]] = [
        ("abby_adz_explicit", lambda: _base_case(ABBY), "match"),
        ("abby_envision_explicit", lambda: _base_case(
            ABBY,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
        ), "match"),
        ("abby_non_argen_itero_adz", lambda: _base_case(
            ABBY,
            scanner="itero",
            shade="C3",
        ), "match"),
        ("abby_envision_non_argen_itero", lambda: _base_case(
            ABBY,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
            scanner="itero",
            shade="C3",
        ), "match"),
        ("vd_adz_non_itero", lambda: _base_case(VD), "match"),
        ("vd_envision_non_itero", lambda: _base_case(
            VD,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
        ), "match"),
        ("vd_adz_itero_non_argen", lambda: _base_case(
            VD,
            scanner="itero",
            shade="C3",
        ), "match"),
        ("vd_envision_itero_non_argen", lambda: _base_case(
            VD,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
            scanner="itero",
            shade="C3",
        ), "match"),
        # Code-owned branches: fixture top-level when excludes these (rule abstains)
        ("abby_anterior_adz_itero", lambda: _base_case(
            ABBY,
            is_anterior=True,
            scanner="itero",
            material="adz multilayer",
        ), "no_policy"),
        ("abby_has_study_itero_adz", lambda: _base_case(
            ABBY,
            has_study=True,
            scanner="itero",
            material="adz multilayer",
        ), "no_policy"),
        ("abby_signature_itero_adz", lambda: _base_case(
            ABBY,
            signature=True,
            scanner="itero",
            material="adz multilayer",
        ), "no_policy"),
        ("vd_has_study_reg_adz", lambda: _base_case(
            VD,
            has_study=True,
            scanner="3shape",
            material="adz multilayer",
        ), "no_policy"),
        ("abby_modeless_adz", lambda: _base_case(
            ABBY,
            material_hint={"route": "modeless", "material": "adz"},
        ), "no_policy"),
        ("vd_modeless_adz", lambda: _base_case(
            VD,
            material_hint={"route": "modeless", "material": "adz"},
        ), "no_policy"),
        ("abby_adz_shade_unusable_itero", lambda: _base_case(
            ABBY,
            shade_usable=False,
            scanner="itero",
        ), "match"),
        ("abby_envision_shade_unusable_itero", lambda: _base_case(
            ABBY,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
            shade_usable=False,
            scanner="itero",
        ), "match"),
        ("abby_adz_shade_unusable_non_itero", lambda: _base_case(
            ABBY,
            shade_usable=False,
            scanner="3shape",
        ), "match"),
        ("abby_envision_shade_unusable_non_itero", lambda: _base_case(
            ABBY,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
            shade_usable=False,
            scanner="3shape",
        ), "match"),
        # iTero + Argen-usable shade (template branches before non-Argen C3/A4)
        ("abby_adz_argen_shade_itero", lambda: _base_case(
            ABBY,
            scanner="itero",
            shade="A1",
        ), "match"),
        ("abby_envision_argen_shade_itero", lambda: _base_case(
            ABBY,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
            scanner="itero",
            shade="A1",
        ), "match"),
        ("abby_non_argen_itero_adz_A4", lambda: _base_case(
            ABBY,
            scanner="itero",
            shade="A4",
        ), "match"),
        ("vd_envision_non_argen_itero_A4", lambda: _base_case(
            VD,
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
            scanner="itero",
            shade="A4",
        ), "match"),
        # Anterior / study / signature: fixture top-level when abstains (no over-apply)
        ("vd_anterior_adz_itero", lambda: _base_case(
            VD,
            is_anterior=True,
            scanner="itero",
            material="adz multilayer",
        ), "no_policy"),
        ("abby_anterior_envision_itero", lambda: _base_case(
            ABBY,
            is_anterior=True,
            scanner="itero",
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
        ), "no_policy"),
        ("vd_signature_itero_adz", lambda: _base_case(
            VD,
            signature=True,
            scanner="itero",
            material="adz multilayer",
        ), "no_policy"),
        ("vd_signature_itero_envision", lambda: _base_case(
            VD,
            signature=True,
            scanner="itero",
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
        ), "no_policy"),
        ("abby_has_study_itero_envision", lambda: _base_case(
            ABBY,
            has_study=True,
            scanner="itero",
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
        ), "no_policy"),
        ("vd_has_study_itero_envision", lambda: _base_case(
            VD,
            has_study=True,
            scanner="itero",
            material="envision something",
            material_hint={"route": "argen_envision", "material": "envision"},
        ), "no_policy"),
        ("vd_abstain_has_study_signature_adz", lambda: _base_case(
            VD,
            has_study=True,
            signature=True,
            scanner="3shape",
            material="adz multilayer",
        ), "no_policy"),
        # Non-Abby/VD doctor: predicates do not match — policy must stay silent
        ("abstain_non_predicate_doctor_argen_adz", lambda: _base_case(
            "Generic Lakeside Dental",
        ), "no_policy"),
    ]

    for name, builder, mode in scenarios:
        case = builder()
        auth = _folder_from_select(case)
        pol = resolve_doctor_policy_template_key(case, offline_cfg, allow_outcomes=True)
        if mode == "match":
            ok = pol == auth
        else:
            ok = pol is None
        rows.append(
            {
                "group": "parity_offline_fixture",
                "scenario": name,
                "mode": mode,
                "authoritative": auth,
                "policy": pol,
                "match": ok,
            }
        )

    return rows


def _argen_parity_rows() -> List[Dict[str, Any]]:
    """
    Abby/VD slices under contact_model_mode on/off (direct template selection seam).
    Policy column uses the offline fixture (disk); authoritative column uses temp unified rules (argen_modes only).
    """
    from domain.decisions.doctor_policy_resolver import resolve_doctor_policy_template_key

    offline_cfg = _load_offline_fixture()
    rows: List[Dict[str, Any]] = []
    scenarios: List[Tuple[str, str, Callable[[], dict], str]] = [
        (
            "argen_contact_on_abby_adz_argen_hint",
            "on",
            lambda: _base_case(ABBY),
            "no_policy",
        ),
        (
            "argen_contact_on_vd_adz_argen_hint",
            "on",
            lambda: _base_case(VD),
            "no_policy",
        ),
        (
            "argen_contact_off_abby_modeless_hint_adz",
            "off",
            lambda: _base_case(
                ABBY,
                material_hint={"route": "modeless", "material": "adz"},
            ),
            "no_policy",
        ),
        (
            "argen_contact_off_vd_modeless_hint_adz",
            "off",
            lambda: _base_case(
                VD,
                material_hint={"route": "modeless", "material": "adz"},
            ),
            "no_policy",
        ),
        (
            "argen_contact_on_abby_envision_argen_hint",
            "on",
            lambda: _base_case(
                ABBY,
                material="envision something",
                material_hint={"route": "argen_envision", "material": "envision"},
            ),
            "no_policy",
        ),
        (
            "argen_contact_on_vd_envision_argen_hint",
            "on",
            lambda: _base_case(
                VD,
                material="envision something",
                material_hint={"route": "argen_envision", "material": "envision"},
            ),
            "no_policy",
        ),
        (
            "argen_contact_off_abby_modeless_envision",
            "off",
            lambda: _base_case(
                ABBY,
                material="envision something",
                material_hint={"route": "modeless", "material": "envision"},
            ),
            "no_policy",
        ),
        (
            "argen_contact_off_vd_modeless_envision",
            "off",
            lambda: _base_case(
                VD,
                material="envision something",
                material_hint={"route": "modeless", "material": "envision"},
            ),
            "no_policy",
        ),
    ]

    for name, argen_mode, builder, mode in scenarios:
        case = builder()
        with _business_rules_dir(("argen_modes.yaml", _argen_modes_yaml(argen_mode))):
            auth = _folder_from_select(case)
            pol = resolve_doctor_policy_template_key(case, offline_cfg, allow_outcomes=True)
        if mode == "match":
            ok = pol == auth
        else:
            ok = pol is None
        rows.append(
            {
                "group": "parity_argen_modes",
                "scenario": name,
                "argen_mode": argen_mode,
                "mode": mode,
                "authoritative": auth,
                "policy": pol,
                "match": ok,
            }
        )

    return rows


def _snapshot_parity_rows() -> List[Dict[str, Any]]:
    """
    Optional real-case-style snapshots: YAML case_data blobs vs select_template + offline policy.
    Safe: no network, no PHI; fixtures live under tests/fixtures/.
    """
    from domain.decisions.doctor_policy_resolver import resolve_doctor_policy_template_key

    path = _REPO_ROOT / "tests" / "fixtures" / "doctor_policy_case_snapshots.yaml"
    if not path.exists():
        return []

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1:
        return [
            {
                "group": "snapshots",
                "scenario": "snapshots_invalid_or_missing_version",
                "authoritative": None,
                "policy": None,
                "match": False,
            }
        ]

    offline_cfg = _load_offline_fixture()
    rows: List[Dict[str, Any]] = []
    for item in raw.get("snapshots") or []:
        cid = item.get("id") or "unknown"
        mode = item.get("mode") or "match"
        case = item.get("case")
        if not isinstance(case, dict):
            rows.append(
                {
                    "group": "snapshots",
                    "scenario": cid,
                    "authoritative": None,
                    "policy": "invalid_case",
                    "match": False,
                }
            )
            continue
        auth = _folder_from_select(case)
        pol = resolve_doctor_policy_template_key(case, offline_cfg, allow_outcomes=True)
        if mode == "match":
            ok = pol == auth
        else:
            ok = pol is None
        rows.append(
            {
                "group": "snapshots",
                "scenario": cid,
                "mode": mode,
                "authoritative": auth,
                "policy": pol,
                "match": ok,
            }
        )

    return rows


def _observability_rows() -> List[Dict[str, Any]]:
    """Log line fires only when flag on, source is outcomes, and override differs from baseline."""
    from domain.decisions.template_selector import select_template_path
    from domain.decisions import template_selector as ts_mod

    mismatch_doctor = "Acme Override Lab"
    mismatch_yaml = """version: 1
enabled: true
rules:
  - id: outcomes_force_envision
    enabled: true
    match:
      contains_all: ["acme", "override", "lab"]
    when:
      all:
        - { field: has_study, eq: false }
    outcomes:
      - when:
          all:
            - { material_is_adz: true }
        action:
          template_override_key: ai_envision
"""
    case = _base_case(mismatch_doctor)
    rows: List[Dict[str, Any]] = []

    def _run_captured(callable_: Callable[[], None]) -> List[str]:
        messages: List[str] = []

        class _Cap(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                messages.append(record.getMessage())

        cap = _Cap()
        cap.setLevel(logging.INFO)
        ts_mod._LOGGER.addHandler(cap)
        ts_mod._LOGGER.setLevel(logging.INFO)
        try:
            callable_()
        finally:
            ts_mod._LOGGER.removeHandler(cap)
        return messages

    with _business_rules_dir(
        ("argen_modes.yaml", _argen_modes_yaml("off")),
        ("doctor_overrides.yaml", mismatch_yaml),
    ):
        from infrastructure.config.argen_modes_runtime import clear_argen_modes_cache
        from infrastructure.config.doctor_override_runtime import clear_doctor_override_cache
        from infrastructure.config.routing_override_runtime import clear_routing_override_cache
        from infrastructure.config.shade_override_runtime import clear_shade_override_cache

        os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
        clear_doctor_override_cache()
        msgs_off = _run_captured(lambda: select_template_path(dict(case)))
        rows.append(
            {
                "group": "observability",
                "scenario": "outcomes_override_log_flag_off",
                "authoritative": None,
                "policy": not any("case_creator_doctor_outcomes_override" in m for m in msgs_off),
                "match": not any("case_creator_doctor_outcomes_override" in m for m in msgs_off),
            }
        )

        os.environ["CASE_CREATOR_DOCTOR_OUTCOMES_LIVE"] = "1"
        clear_doctor_override_cache()
        msgs_on = _run_captured(lambda: select_template_path(dict(case)))
        logged = any("case_creator_doctor_outcomes_override" in m for m in msgs_on)
        rows.append(
            {
                "group": "observability",
                "scenario": "outcomes_override_log_flag_on",
                "authoritative": None,
                "policy": logged,
                "match": logged,
            }
        )

        simple_only = """version: 1
enabled: true
rules:
  - id: simple_only_acme
    enabled: true
    match:
      contains_all: ["acme", "dental", "group"]
    action:
      template_override_key: ai_envision
"""
        br_dir = Path(os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"])
        unified_path = br_dir / "case_creator_rules.yaml"
        doc_u = yaml.safe_load(unified_path.read_text(encoding="utf-8"))
        doc_u["doctor_overrides"] = yaml.safe_load(simple_only)
        unified_path.write_text(
            yaml.dump(
                doc_u,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            ),
            encoding="utf-8",
        )
        clear_doctor_override_cache()
        clear_argen_modes_cache()
        clear_routing_override_cache()
        clear_shade_override_cache()
        cd_simple = _base_case("Acme Dental Group")
        msgs_simple = _run_captured(lambda: select_template_path(dict(cd_simple)))
        rows.append(
            {
                "group": "observability",
                "scenario": "simple_override_flag_on_no_outcomes_log",
                "authoritative": None,
                "policy": not any("case_creator_doctor_outcomes_override" in m for m in msgs_simple),
                "match": not any("case_creator_doctor_outcomes_override" in m for m in msgs_simple),
            }
        )

    os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
    from infrastructure.config.doctor_override_runtime import clear_doctor_override_cache

    clear_doctor_override_cache()
    return rows


def _flag_rows() -> List[Dict[str, Any]]:
    from infrastructure.config.doctor_override_runtime import (
        clear_doctor_override_cache,
        resolve_doctor_template_override_key,
    )

    rows: List[Dict[str, Any]] = []
    fixture_text = _offline_fixture_text()
    case = _base_case(ABBY)

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        doc_flag = {
            "unified_version": 1,
            "doctor_overrides": yaml.safe_load(fixture_text),
        }
        (tdp / "case_creator_rules.yaml").write_text(
            yaml.dump(
                doc_flag,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            ),
            encoding="utf-8",
        )
        os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(tdp)
        clear_doctor_override_cache()

        os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
        clear_doctor_override_cache()
        off_key = resolve_doctor_template_override_key(case["doctor"], case)
        rows.append(
            {
                "group": "flag",
                "scenario": "outcomes_live_env_unset",
                "authoritative": None,
                "policy": off_key,
                "match": off_key is None,
            }
        )

        os.environ["CASE_CREATOR_DOCTOR_OUTCOMES_LIVE"] = "0"
        clear_doctor_override_cache()
        off_key2 = resolve_doctor_template_override_key(case["doctor"], case)
        rows.append(
            {
                "group": "flag",
                "scenario": "outcomes_live_0",
                "authoritative": None,
                "policy": off_key2,
                "match": off_key2 is None,
            }
        )

        os.environ["CASE_CREATOR_DOCTOR_OUTCOMES_LIVE"] = "1"
        clear_doctor_override_cache()
        on_key = resolve_doctor_template_override_key(case["doctor"], case)
        rows.append(
            {
                "group": "flag",
                "scenario": "outcomes_live_1",
                "authoritative": "ai_adzir",
                "policy": on_key,
                "match": on_key == "ai_adzir",
            }
        )

    for k in ("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", "CASE_CREATOR_BUSINESS_RULES_DIR"):
        os.environ.pop(k, None)
    clear_doctor_override_cache()

    return rows


def _simple_override_rows() -> List[Dict[str, Any]]:
    from infrastructure.config import business_rule_schemas as schemas
    from infrastructure.config.doctor_override_runtime import (
        clear_doctor_override_cache,
        resolve_doctor_template_override_key,
    )

    rows: List[Dict[str, Any]] = []
    simple_yaml = """version: 1
enabled: true
rules:
  - id: live_simple_acme
    enabled: true
    match:
      contains_all: ["acme", "dental"]
    action:
      template_override_key: ai_envision
"""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        doc_simple = {"unified_version": 1, "doctor_overrides": yaml.safe_load(simple_yaml)}
        (tdp / "case_creator_rules.yaml").write_text(
            yaml.dump(
                doc_simple,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                width=120,
            ),
            encoding="utf-8",
        )
        os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(td)
        os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
        clear_doctor_override_cache()
        cd = _base_case("Acme Dental Group")
        live_key = resolve_doctor_template_override_key(cd["doctor"], cd)
        simple_valid = schemas.validate_doctor_overrides(yaml.safe_load(simple_yaml))
        rows.append(
            {
                "group": "simple_live",
                "scenario": "contains_all_override_flag_off",
                "authoritative": None,
                "policy": live_key,
                "match": live_key == "ai_envision" and simple_valid.valid,
            }
        )

        os.environ["CASE_CREATOR_DOCTOR_OUTCOMES_LIVE"] = "1"
        clear_doctor_override_cache()
        live_key_on = resolve_doctor_template_override_key(cd["doctor"], cd)
        rows.append(
            {
                "group": "simple_live",
                "scenario": "contains_all_override_flag_on",
                "authoritative": None,
                "policy": live_key_on,
                "match": live_key_on == "ai_envision",
            }
        )

    for k in ("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", "CASE_CREATOR_BUSINESS_RULES_DIR"):
        os.environ.pop(k, None)
    clear_doctor_override_cache()
    return rows


def _production_yaml_seed_rows() -> List[Dict[str, Any]]:
    """Validate seeded production doctor_overrides vs offline fixture when outcomes flag is on."""
    from infrastructure.config import business_rule_schemas as schemas
    from infrastructure.config.doctor_override_runtime import (
        clear_doctor_override_cache,
        resolve_doctor_template_override_key,
    )
    from domain.decisions.doctor_policy_resolver import resolve_doctor_policy_template_key

    rows: List[Dict[str, Any]] = []
    unified_path = _REPO_ROOT / "business_rules" / "v1" / "case_creator_rules.yaml"
    doc = yaml.safe_load(unified_path.read_text(encoding="utf-8"))
    raw = doc["doctor_overrides"]
    v = schemas.validate_doctor_overrides(raw)
    rows.append(
        {
            "group": "production_seed",
            "scenario": "production_unified_doctor_validates",
            "authoritative": None,
            "policy": v.valid,
            "match": bool(v.valid),
        }
    )
    if not v.valid or not v.normalized:
        return rows

    rules = v.normalized.get("rules") or []
    ids = {r.get("id") for r in rules}
    seeded = "abby_dew_multi_outcome" in ids and "vd_brier_creek_multi_outcome" in ids
    rows.append(
        {
            "group": "production_seed",
            "scenario": "multi_outcome_rule_ids_present",
            "authoritative": None,
            "policy": seeded,
            "match": seeded,
        }
    )

    def _outcomes_len(cfg: dict, predicate: str) -> int:
        for r in cfg.get("rules") or []:
            m = r.get("match") or {}
            if m.get("predicate") == predicate:
                return len(r.get("outcomes") or [])
        return 0

    offline_cfg = _load_offline_fixture()
    abby_match = _outcomes_len(v.normalized, "abby_dew") == _outcomes_len(offline_cfg, "abby_dew")
    vd_match = _outcomes_len(v.normalized, "vd_brier_creek") == _outcomes_len(
        offline_cfg, "vd_brier_creek"
    )
    rows.append(
        {
            "group": "production_seed",
            "scenario": "outcome_counts_match_offline_fixture",
            "authoritative": None,
            "policy": abby_match and vd_match,
            "match": abby_match and vd_match,
        }
    )

    preview_path = str(_REPO_ROOT / "business_rules" / "v1")
    try:
        os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = preview_path
        os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
        clear_doctor_override_cache()
        abby_case = _base_case(ABBY)
        off_none = resolve_doctor_template_override_key(abby_case["doctor"], abby_case)
        rows.append(
            {
                "group": "production_seed",
                "scenario": "repo_path_flag_off_abby_no_override",
                "authoritative": None,
                "policy": off_none,
                "match": off_none is None,
            }
        )

        os.environ["CASE_CREATOR_DOCTOR_OUTCOMES_LIVE"] = "1"
        clear_doctor_override_cache()
        parity_cases: List[Tuple[str, Callable[[], dict]]] = [
            ("abby_adz", lambda: _base_case(ABBY)),
            ("vd_adz", lambda: _base_case(VD)),
            (
                "abby_envision",
                lambda: _base_case(
                    ABBY,
                    material="envision something",
                    material_hint={"route": "argen_envision", "material": "envision"},
                ),
            ),
            (
                "abby_non_argen_itero",
                lambda: _base_case(ABBY, scanner="itero", shade="C3"),
            ),
        ]
        for label, builder in parity_cases:
            case = builder()
            prod_key = resolve_doctor_template_override_key(case["doctor"], case)
            fixture_key = resolve_doctor_policy_template_key(
                case, offline_cfg, allow_outcomes=True
            )
            ok = prod_key == fixture_key
            rows.append(
                {
                    "group": "production_seed",
                    "scenario": f"flag_on_same_as_offline_fixture_{label}",
                    "authoritative": fixture_key,
                    "policy": prod_key,
                    "match": ok,
                }
            )
    finally:
        os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
        os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
        clear_doctor_override_cache()

    return rows


def _repo_validate_row() -> Dict[str, Any]:
    from infrastructure.config.business_rule_loader import load_business_rule_config_preview
    from infrastructure.config.doctor_override_runtime import clear_doctor_override_cache

    preview_path = _REPO_ROOT / "business_rules" / "v1"
    os.environ["CASE_CREATOR_BUSINESS_RULES_DIR"] = str(preview_path)
    os.environ.pop("CASE_CREATOR_DOCTOR_OUTCOMES_LIVE", None)
    clear_doctor_override_cache()
    preview = load_business_rule_config_preview(override_base_dir=str(preview_path))
    prod_ok = not any(preview.files[f].errors for f in preview.files)
    os.environ.pop("CASE_CREATOR_BUSINESS_RULES_DIR", None)
    clear_doctor_override_cache()
    return {
        "group": "repo",
        "scenario": "business_rules_v1_loads",
        "authoritative": None,
        "policy": prod_ok,
        "match": bool(prod_ok),
        "mode": "n/a",
    }


def _argen_legacy_migration_row() -> Dict[str, Any]:
    from infrastructure.config import business_rule_schemas as schemas

    raw = {
        "version": 1,
        "enabled": True,
        "contact_model_mode": "always_with_contact_models",
    }
    r = schemas.validate_argen_modes(raw)
    ok = (
        r.valid
        and r.normalized is not None
        and r.normalized.get("contact_model_mode") == "on"
        and any("deprecated" in (w or "").lower() for w in (r.warnings or []))
    )
    return {
        "group": "argen_migration",
        "scenario": "legacy_always_with_normalizes_to_on",
        "authoritative": "on",
        "policy": r.normalized.get("contact_model_mode") if r.normalized else None,
        "match": ok,
    }


def run_parity() -> Dict[str, List[Dict[str, Any]]]:
    rows = (
        _parity_rows()
        + _argen_parity_rows()
        + [_argen_legacy_migration_row()]
        + _snapshot_parity_rows()
        + _observability_rows()
        + _flag_rows()
        + _simple_override_rows()
        + _production_yaml_seed_rows()
        + [_repo_validate_row()]
    )
    return {"rows": rows}


def main() -> int:
    r = run_parity()
    print("CASE CREATOR DOCTOR POLICY PARITY + FLAG HARNESS")
    for row in r["rows"]:
        extra = ""
        if row.get("group") == "parity_argen_modes":
            extra = f" argen_mode={row.get('argen_mode')!r}"
        print(
            f"  [{row.get('group')}] {row['scenario']}: authoritative={row['authoritative']!r} "
            f"policy={row['policy']!r} ok={row['match']}{extra}"
        )
    parity = [x for x in r["rows"] if x.get("group") == "parity_offline_fixture"]
    parity_ok = all(x["match"] for x in parity)
    argen_ok = all(x["match"] for x in r["rows"] if x.get("group") == "parity_argen_modes")
    argen_mig_ok = all(x["match"] for x in r["rows"] if x.get("group") == "argen_migration")
    obs_ok = all(x["match"] for x in r["rows"] if x.get("group") == "observability")
    flag_ok = all(x["match"] for x in r["rows"] if x.get("group") == "flag")
    simple_ok = all(x["match"] for x in r["rows"] if x.get("group") == "simple_live")
    repo_ok = next((x["match"] for x in r["rows"] if x["scenario"] == "business_rules_v1_loads"), False)
    prod_seed = [x for x in r["rows"] if x.get("group") == "production_seed"]
    prod_seed_ok = all(x["match"] for x in prod_seed) if prod_seed else True
    snap = [x for x in r["rows"] if x.get("group") == "snapshots"]
    snap_ok = all(x["match"] for x in snap) if snap else True
    print(f"\nParity (offline fixture): {parity_ok}")
    print(f"Parity (argen_modes temp config): {argen_ok}")
    print(f"Argen legacy YAML migration: {argen_mig_ok}")
    print(f"Parity (case snapshots): {snap_ok} ({len(snap)} rows)")
    print(f"Observability (outcomes override log): {obs_ok}")
    print(f"Flag behavior: {flag_ok}")
    print(f"Simple override (flag off/on): {simple_ok}")
    print(f"Production YAML seed checks: {prod_seed_ok} ({len(prod_seed)} rows)")
    print(f"Repo v1 load: {repo_ok}")
    return (
        0
        if parity_ok
        and argen_ok
        and argen_mig_ok
        and snap_ok
        and obs_ok
        and flag_ok
        and simple_ok
        and prod_seed_ok
        and repo_ok
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
