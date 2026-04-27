from functools import lru_cache
from typing import Dict

from domain.rules import routing_rules
from infrastructure.config.business_rule_loader import load_business_rule_config_preview

BASELINE_FAMILY_DESTINATION_MAP: Dict[str, str] = {
    "argen": routing_rules.DEST_ARGEN,
    "study": routing_rules.DEST_1_9,
    "anterior": routing_rules.DEST_1_9,
    "ai": routing_rules.DEST_1_9,
}


def infer_template_family_key(template_path_or_name: str) -> str:
    """
    Keep precedence consistent with existing destination classification semantics.
    """
    name = routing_rules.template_filename(template_path_or_name)
    if routing_rules.is_argen_template(name):
        return "argen"
    if routing_rules.is_study_template(name):
        return "study"
    if routing_rules.is_anterior_template(name):
        return "anterior"
    if routing_rules.is_ai_template(name):
        return "ai"
    raise ValueError(f"Unrecognized template family for routing override: {name}")


@lru_cache(maxsize=1)
def _cached_preview():
    return load_business_rule_config_preview()


def clear_routing_override_cache():
    _cached_preview.cache_clear()


def resolve_destination_key(template_path_or_name: str) -> str:
    """
    Live in this pass:
    - routing_overrides.template_family_route_overrides only.

    Labels, path execution, and any advanced routing DSL remain non-live.
    """
    family_key = infer_template_family_key(template_path_or_name)
    baseline = BASELINE_FAMILY_DESTINATION_MAP[family_key]

    try:
        preview = _cached_preview()
        cfg = (preview.effective_config or {}).get("routing_overrides") or {}
        if not cfg.get("enabled", True):
            return baseline

        overrides = cfg.get("template_family_route_overrides") or []
        if not isinstance(overrides, list):
            return baseline

        # Deterministic order: first matching entry wins.
        for entry in overrides:
            if not isinstance(entry, dict):
                continue
            if entry.get("family_key") != family_key:
                continue
            destination_key = entry.get("destination_key")
            if destination_key in (routing_rules.DEST_ARGEN, routing_rules.DEST_1_9):
                return destination_key
        return baseline
    except Exception:
        return baseline
