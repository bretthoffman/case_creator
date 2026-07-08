"""
Bounded runtime resolver for the ``delivery_modes`` unified-config family.

DORMANT PASS: nothing here is called from ``process_case`` yet. This module exposes the
normalized ``designer_doctor_names`` list and a pure, case-insensitive matching helper that the
NEXT pass will use to decide outsource (default) vs designer (exception) delivery mode.

Reuse note: shade-based designer disqualification is intentionally handled by the existing live
``shade_overrides.non_outsource_shades`` behavior (see
``infrastructure.config.shade_override_runtime`` / ``domain.rules.template_rules.is_non_argen_shade``)
and is NOT duplicated in this family.
"""

from functools import lru_cache
from typing import Iterable, Optional, Tuple

from infrastructure.config.business_rule_loader import load_business_rule_config_preview


def _normalize_names(values: Iterable[str]) -> Tuple[str, ...]:
    """Strip, drop empties, and de-duplicate case-insensitively while preserving order/casing."""
    normalized = []
    seen = set()
    for raw in values or []:
        if not isinstance(raw, str):
            continue
        name = raw.strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(name)
    return tuple(normalized)


@lru_cache(maxsize=1)
def _cached_preview():
    return load_business_rule_config_preview()


def clear_delivery_mode_cache():
    _cached_preview.cache_clear()


def resolve_designer_doctor_names(default_names: Iterable[str] = ()) -> Tuple[str, ...]:
    """
    Live read of ``delivery_modes.designer_doctor_names`` (validated config only).

    Returns a normalized tuple of doctor-name substrings that will, in the future live pass, force
    a case into designer mode instead of the default outsource mode. Any error / missing / invalid
    / disabled path falls back to ``default_names`` (normally empty).
    """
    defaults = _normalize_names(default_names)
    try:
        preview = _cached_preview()
        cfg = (preview.effective_config or {}).get("delivery_modes") or {}
        if not cfg.get("enabled", True):
            return defaults
        names = cfg.get("designer_doctor_names")
        if not isinstance(names, list):
            return defaults
        resolved = _normalize_names(names)
        return resolved if resolved else defaults
    except Exception:
        return defaults


def is_designer_doctor(doctor_name: str, designer_names: Optional[Iterable[str]] = None) -> bool:
    """
    Pure, case-insensitive substring match helper (repo convention, cf.
    ``domain.decisions.doctor_policy_resolver._contains_any``).

    Returns True when ``doctor_name`` contains any configured designer substring. When
    ``designer_names`` is None the live config is read via ``resolve_designer_doctor_names``.

    NOTE: intentionally NOT yet wired into ``process_case``; the reroute is a later pass.
    """
    name = (doctor_name or "").strip().lower()
    if not name:
        return False
    names = (
        resolve_designer_doctor_names()
        if designer_names is None
        else _normalize_names(designer_names)
    )
    return any(substr.lower() in name for substr in names)
