from functools import lru_cache

from infrastructure.config.business_rule_loader import load_business_rule_config_preview
from infrastructure.config.business_rule_schemas import (
    ALLOWED_CONTACT_MODEL_DESIGN_FIELD_VALUES,
    ALLOWED_CONTACT_MODEL_MODES,
)

BASELINE_CONTACT_MODEL_MODE = "off"
BASELINE_CONTACT_MODEL_DESIGN_FIELD = "3Shape Automate"


@lru_cache(maxsize=1)
def _cached_preview():
    return load_business_rule_config_preview()


def clear_argen_modes_cache():
    _cached_preview.cache_clear()


def resolve_contact_model_mode() -> str:
    """
    Returns ``off`` or ``on`` from validated ``argen_modes.contact_model_mode``.
    Legacy three-value YAML is normalized at validation time.
    """
    try:
        preview = _cached_preview()
        cfg = (preview.effective_config or {}).get("argen_modes") or {}
        if not cfg.get("enabled", True):
            return BASELINE_CONTACT_MODEL_MODE
        mode = cfg.get("contact_model_mode")
        if isinstance(mode, str) and mode in ALLOWED_CONTACT_MODEL_MODES:
            return mode
        return BASELINE_CONTACT_MODEL_MODE
    except Exception:
        return BASELINE_CONTACT_MODEL_MODE


def resolve_contact_model_design_field() -> str:
    """
    Returns the bounded Argen modeless design field value from
    ``argen_modes.contact_model_design_field``.
    Allowed values: ``No`` or ``3Shape Automate``.
    """
    try:
        preview = _cached_preview()
        cfg = (preview.effective_config or {}).get("argen_modes") or {}
        if not cfg.get("enabled", True):
            return BASELINE_CONTACT_MODEL_DESIGN_FIELD
        value = cfg.get("contact_model_design_field")
        if isinstance(value, str) and value in ALLOWED_CONTACT_MODEL_DESIGN_FIELD_VALUES:
            return value
        return BASELINE_CONTACT_MODEL_DESIGN_FIELD
    except Exception:
        return BASELINE_CONTACT_MODEL_DESIGN_FIELD
