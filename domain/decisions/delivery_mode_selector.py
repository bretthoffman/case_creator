"""
Live delivery-mode decision: outsource (default) vs designer (exception).

This is the single source of truth for outsource-vs-designer *delivery* (final destination + zip).
It intentionally does NOT depend on template family, has_study, signature, or the retired
Serbia/Abby/VD routing logic.

Designer is chosen ONLY from YAML-managed disqualifiers:
  - doctor names  -> delivery_modes.designer_doctor_names   (via delivery_mode_runtime)
  - shades        -> shade_overrides.non_outsource_shades (via template_rules.is_non_argen_shade)
  - shade text    -> template_utils shade flags (custom / photos in raw EVO shade field)

Everything else is outsource.
"""

from infrastructure.config.delivery_mode_runtime import is_designer_doctor
from domain.rules.template_rules import is_non_argen_shade
from template_utils import shade_routes_to_designer

MODE_OUTSOURCE = "outsource"
MODE_DESIGNER = "designer"


def resolve_delivery_mode(case_data) -> str:
    """
    Return ``"designer"`` when the case is disqualified from outsource by a YAML-managed
    doctor-name or shade exclusion; otherwise ``"outsource"`` (the default for all cases).
    """
    cd = case_data or {}
    doctor = cd.get("doctor", "") or ""
    shade = cd.get("shade", "") or ""

    if is_designer_doctor(doctor):
        return MODE_DESIGNER
    if is_non_argen_shade(shade):
        return MODE_DESIGNER
    if shade_routes_to_designer(cd):
        return MODE_DESIGNER
    return MODE_OUTSOURCE
