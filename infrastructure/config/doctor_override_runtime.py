from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from config import doctor_outcomes_live_enabled
from domain.decisions.doctor_policy_resolver import (
    DoctorPolicySource,
    resolve_doctor_policy,
)
from domain.rules import routing_rules
from infrastructure.config.business_rule_loader import load_business_rule_config_preview


@lru_cache(maxsize=1)
def _cached_preview():
    return load_business_rule_config_preview()


def clear_doctor_override_cache():
    _cached_preview.cache_clear()


def resolve_doctor_template_override_with_source(
    doctor_name: str,
    case_data: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[str], DoctorPolicySource]:
    """
    Like resolve_doctor_template_override_key but also returns whether the key came from
    ``outcomes`` vs a simple ``action`` rule (or None if no match).
    """
    try:
        preview = _cached_preview()
        cfg = (preview.effective_config or {}).get("doctor_overrides") or {}
        if not cfg.get("enabled", True):
            return None, None

        cd: Dict[str, Any] = dict(case_data) if case_data is not None else {}
        if doctor_name and not cd.get("doctor"):
            cd["doctor"] = doctor_name

        allow_outcomes = doctor_outcomes_live_enabled()
        result = resolve_doctor_policy(cd, cfg, allow_outcomes=allow_outcomes)
        return result.template_key, result.source
    except Exception:
        return None, None


def resolve_doctor_template_override_key(
    doctor_name: str,
    case_data: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Live doctor override resolution (validated config only).

    - Simple rules (`action.template_override_key` only): always evaluated when matched.
    - Multi-outcome rules (`outcomes[]`): evaluated only when
      `doctor_outcomes_live_enabled()` is true (env CASE_CREATOR_DOCTOR_OUTCOMES_LIVE).

    When case_data is None, a minimal dict with `doctor` is used; rule-level `when` clauses
    see missing fields as falsy.
    """
    key, _ = resolve_doctor_template_override_with_source(doctor_name, case_data)
    return key


def resolve_doctor_route_label_override_key(
    doctor_name: str,
    case_data: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Live doctor route-label override resolution (validated config only).

    Route-label overrides are bounded to known label keys and are intentionally independent
    from ``destination_key`` routing. They support readback/UI label changes such as
    designer->serbia while the destination remains ``1_9``.
    """
    try:
        preview = _cached_preview()
        cfg = (preview.effective_config or {}).get("doctor_overrides") or {}
        if not cfg.get("enabled", True):
            return None

        cd: Dict[str, Any] = dict(case_data) if case_data is not None else {}
        if doctor_name and not cd.get("doctor"):
            cd["doctor"] = doctor_name

        allow_outcomes = doctor_outcomes_live_enabled()
        result = resolve_doctor_policy(cd, cfg, allow_outcomes=allow_outcomes)
        rk = result.route_label_key
        if isinstance(rk, str) and rk in {
            routing_rules.LABEL_ARGEN,
            routing_rules.LABEL_DESIGNER,
            routing_rules.LABEL_SERBIA,
            routing_rules.LABEL_AI_DESIGNER,
            routing_rules.LABEL_AI_SERBIA,
        }:
            return rk
        return None
    except Exception:
        return None
