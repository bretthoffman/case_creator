import os

from config import TEMPLATE_DIR
from infrastructure.config.argen_modes_runtime import resolve_contact_model_mode
from infrastructure.config.shade_override_runtime import resolve_non_argen_shade_markers

NON_ARGEN_SHADE_MARKERS = ("C3", "A4")
ARGEN_ROUTE_KEYS = ("argen_envision", "argen_adzir")


def is_non_argen_shade(shade: str) -> bool:
    if not shade:
        return False
    shade_upper = shade.upper()
    effective_markers = resolve_non_argen_shade_markers(NON_ARGEN_SHADE_MARKERS)
    return any(marker in shade_upper for marker in effective_markers)


def is_itero_scanner(scanner: str) -> bool:
    return "itero" in (scanner or "").lower()


def is_adz_material(material: str) -> bool:
    return "adz" in (material or "").lower()


def normalized_hint_route(case_data) -> str:
    return (case_data.get("material_hint", {}).get("route") or "").lower()


def effective_argen_hint_route(hint_route: str, material: str) -> str:
    """
    Returns the normalized Argen route hint from case data without transforming it.

    Legacy three-way contact_model_mode hint rewriting (always_with / always_without /
    legacy_default) is no longer applied here. Contact-model on/off is handled directly
    in template_utils.select_template via contact_model_argen_on() and
    is_eligible_contact_model_argen_case(). This function remains for call-site
    compatibility and doctor_when_eval (excludes_modeless_hint_route).
    """
    del material  # unused; kept for API compatibility
    return (hint_route or "").lower()


def contact_model_argen_on() -> bool:
    """True when argen_modes.contact_model_mode is ``on`` (contact-model Argen templates)."""
    return resolve_contact_model_mode() == "on"


def is_eligible_contact_model_argen_case(case_data) -> bool:
    """
    True when material_hint.route is an Argen family (argen_adzir, argen_envision, modeless).
    Non-Argen routes are unchanged by contact-model mode.
    """
    r = normalized_hint_route(case_data)
    return r in ARGEN_ROUTE_KEYS or r == "modeless"


def build_template_path(folder: str) -> str:
    filename = f"{folder}.xml"
    return os.path.join(TEMPLATE_DIR, folder, filename)
