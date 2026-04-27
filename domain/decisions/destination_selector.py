from domain.rules import routing_rules
from domain.rules.rule_models import DestinationDecision
from infrastructure.config.routing_override_runtime import resolve_destination_key


def select_destination(template_path_or_name: str, doctor_name: str) -> DestinationDecision:
    """
    Thin compatibility shell over centralized routing primitives.
    Returns route categories/labels only; processor keeps ownership of absolute path execution.
    """
    destination_key = resolve_destination_key(template_path_or_name)
    route_label_key = routing_rules.route_label_for_template(template_path_or_name, doctor_name)
    is_ai_alias_to_designer = routing_rules.is_ai_template(template_path_or_name)
    return DestinationDecision(
        destination_key=destination_key,
        route_label_key=route_label_key,
        is_ai_alias_to_designer=is_ai_alias_to_designer,
    )
