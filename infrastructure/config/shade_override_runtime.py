from functools import lru_cache
from typing import Iterable, Tuple

from infrastructure.config.business_rule_loader import load_business_rule_config_preview


def _normalize_markers(values: Iterable[str]) -> Tuple[str, ...]:
    normalized = []
    seen = set()
    for raw in values or []:
        marker = str(raw).strip().upper()
        if not marker:
            continue
        if marker in seen:
            continue
        seen.add(marker)
        normalized.append(marker)
    return tuple(normalized)


@lru_cache(maxsize=1)
def _cached_preview():
    return load_business_rule_config_preview()


def clear_shade_override_cache():
    _cached_preview.cache_clear()


def resolve_non_argen_shade_markers(default_markers: Iterable[str]) -> Tuple[str, ...]:
    """
    Live in this pass:
    - shade_overrides.non_argen_shade_markers only.

    Any error/missing/invalid path falls back to provided defaults.
    """
    defaults = _normalize_markers(default_markers)
    try:
        preview = _cached_preview()
        cfg = (preview.effective_config or {}).get("shade_overrides") or {}
        if not cfg.get("enabled", True):
            return defaults
        markers = cfg.get("non_argen_shade_markers")
        if not isinstance(markers, list):
            return defaults
        resolved = _normalize_markers(markers)
        return resolved if resolved else defaults
    except Exception:
        return defaults
