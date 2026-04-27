"""
Doctor policy resolver for multi-outcome and simple doctor_overrides rules.

Evaluates validated doctor_overrides config against full case_data. The live
template override seam calls this with allow_outcomes gated by env
CASE_CREATOR_DOCTOR_OUTCOMES_LIVE (default off). Inline Abby/VD logic in
template_utils.select_template remains authoritative unless an override key
is returned.
"""

from typing import Any, Dict, List, Literal, NamedTuple, Optional

from domain.rules.doctor_rules import is_abby_dew, is_vd_brier_creek
from domain.decisions.doctor_when_eval import evaluate_doctor_when_group


def _contains_any(haystack: str, needles: List[str]) -> bool:
    if not needles:
        return True
    return any((n or "").strip().lower() in haystack for n in needles)


def _contains_all(haystack: str, needles: List[str]) -> bool:
    if not needles:
        return True
    return all((n or "").strip().lower() in haystack for n in needles)


def rule_matches_doctor(doctor_name: str, match: Dict[str, Any]) -> bool:
    name = (doctor_name or "").strip().lower()
    predicate = match.get("predicate")
    if predicate == "abby_dew":
        if not is_abby_dew(doctor_name):
            return False
    elif predicate == "vd_brier_creek":
        if not is_vd_brier_creek(doctor_name):
            return False
    elif predicate:
        return False

    contains_any = match.get("contains_any") or []
    contains_all = match.get("contains_all") or []
    if contains_any or contains_all:
        if not _contains_any(name, contains_any) or not _contains_all(name, contains_all):
            return False
    elif not predicate:
        return False
    return True


DoctorPolicySource = Optional[Literal["outcomes", "simple"]]


class DoctorPolicyResult(NamedTuple):
    template_key: Optional[str]
    route_label_key: Optional[str]
    source: DoctorPolicySource


def resolve_doctor_policy(
    case_data: Dict[str, Any],
    doctor_cfg: Dict[str, Any],
    *,
    allow_outcomes: bool = True,
) -> DoctorPolicyResult:
    """
    Resolves doctor_overrides to a template folder key and whether it came from
    a multi-outcome rule or a simple action rule.
    """
    if not doctor_cfg.get("enabled", True):
        return DoctorPolicyResult(None, None, None)

    doctor_name = (case_data or {}).get("doctor", "")
    rules: List[Dict[str, Any]] = doctor_cfg.get("rules") or []

    for rule in rules:
        if not rule.get("enabled", True):
            continue
        if not rule_matches_doctor(doctor_name, rule.get("match") or {}):
            continue

        if rule.get("outcomes"):
            if not allow_outcomes:
                continue
            rw = rule.get("when")
            if rw and not evaluate_doctor_when_group(case_data, rw):
                continue
            for outcome in rule.get("outcomes") or []:
                wh = outcome.get("when") or {}
                if not evaluate_doctor_when_group(case_data, wh):
                    continue
                act = outcome.get("action") or {}
                tk = act.get("template_override_key")
                if isinstance(tk, str) and tk.strip():
                    return DoctorPolicyResult(tk.strip(), None, "outcomes")
            continue

        rw = rule.get("when")
        if rw and not evaluate_doctor_when_group(case_data, rw):
            continue
        act = rule.get("action") or {}
        tk = act.get("template_override_key")
        rk = act.get("route_label_override_key")
        if isinstance(tk, str) and tk.strip():
            route_label_key = rk.strip() if isinstance(rk, str) and rk.strip() else None
            return DoctorPolicyResult(tk.strip(), route_label_key, "simple")
        if isinstance(rk, str) and rk.strip():
            return DoctorPolicyResult(None, rk.strip(), "simple")

    return DoctorPolicyResult(None, None, None)


def resolve_doctor_policy_template_key(
    case_data: Dict[str, Any],
    doctor_cfg: Dict[str, Any],
    *,
    allow_outcomes: bool = True,
) -> Optional[str]:
    """
    Returns a template folder key (e.g. ai_adzir) if a rule + outcome matches, else None.
    doctor_cfg should be the normalized doctor_overrides object (effective_config['doctor_overrides']).

    When allow_outcomes is False, rules that define `outcomes` are skipped (simple rules only).
    Live runtime passes allow_outcomes=False unless CASE_CREATOR_DOCTOR_OUTCOMES_LIVE is enabled.
    """
    return resolve_doctor_policy(case_data, doctor_cfg, allow_outcomes=allow_outcomes).template_key


def resolve_doctor_policy_route_label_key(
    case_data: Dict[str, Any],
    doctor_cfg: Dict[str, Any],
    *,
    allow_outcomes: bool = True,
) -> Optional[str]:
    """
    Returns a bounded route-label key (e.g. serbia, ai_designer) if a rule matches, else None.

    This only reads the validated ``route_label_override_key`` value from simple doctor actions.
    Outcomes remain template-only by schema in this phase.
    """
    return resolve_doctor_policy(case_data, doctor_cfg, allow_outcomes=allow_outcomes).route_label_key
