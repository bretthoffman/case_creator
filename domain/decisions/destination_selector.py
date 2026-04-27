from typing import Any, Dict, Optional

from domain.rules import routing_rules
from domain.rules.rule_models import DestinationDecision
from infrastructure.config.doctor_override_runtime import resolve_doctor_route_label_override_key
from infrastructure.config.routing_override_runtime import resolve_destination_key


def _is_label_compatible_with_template_family(template_path_or_name: str, route_label_key: str) -> bool:
    """
    Prevent impossible label/template combinations:
    - Argen templates only accept argen label.
    - Study/anterior accept designer|serbia.
    - AI accepts ai_designer|ai_serbia.
    """
    if routing_rules.is_argen_template(template_path_or_name):
        return route_label_key == routing_rules.LABEL_ARGEN
    if routing_rules.is_study_template(template_path_or_name) or routing_rules.is_anterior_template(
        template_path_or_name
    ):
        return route_label_key in {routing_rules.LABEL_DESIGNER, routing_rules.LABEL_SERBIA}
    if routing_rules.is_ai_template(template_path_or_name):
        return route_label_key in {routing_rules.LABEL_AI_DESIGNER, routing_rules.LABEL_AI_SERBIA}
    return False


def select_destination(
    template_path_or_name: str,
    doctor_name: str,
    case_data: Optional[Dict[str, Any]] = None,
) -> DestinationDecision:
    """
    Thin compatibility shell over centralized routing primitives.
    Returns route categories/labels only; processor keeps ownership of absolute path execution.
    """
    destination_key = resolve_destination_key(template_path_or_name)
    route_label_key = routing_rules.route_label_for_template(template_path_or_name, doctor_name)
    override_label = resolve_doctor_route_label_override_key(doctor_name, case_data=case_data)
    if isinstance(override_label, str) and _is_label_compatible_with_template_family(
        template_path_or_name, override_label
    ):
        route_label_key = override_label
    is_ai_alias_to_designer = routing_rules.is_ai_template(template_path_or_name)
    return DestinationDecision(
        destination_key=destination_key,
        route_label_key=route_label_key,
        is_ai_alias_to_designer=is_ai_alias_to_designer,
    )
