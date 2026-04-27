"""
Bounded `when` clause evaluation for doctor override rules.

Used by the doctor policy resolver and the live doctor override runtime when
full case_data is available. Special clause ``excludes_modeless_hint_route`` abstains
when the case would use argen_modeless_* templates: contact_model_mode on (eligible
Argen routes) or legacy raw modeless hint (see template_utils.select_template).
"""

from typing import Any, Dict

from domain.rules import template_rules


def _case_uses_argen_modeless_contact_templates(case_data: Dict[str, Any]) -> bool:
    if case_data.get("has_study"):
        return False
    if template_rules.contact_model_argen_on() and template_rules.is_eligible_contact_model_argen_case(
        case_data
    ):
        return True
    return template_rules.normalized_hint_route(case_data) == "modeless"


def evaluate_doctor_when_clause(case_data: Dict[str, Any], clause: Dict[str, Any]) -> bool:
    if "field" in clause:
        field = clause.get("field")
        eq = clause.get("eq")
        if field not in ("has_study", "signature", "shade_usable", "is_anterior"):
            return False
        if not isinstance(eq, bool):
            return False
        return bool(case_data.get(field)) == eq

    if len(clause) != 1:
        return False
    if "excludes_modeless_hint_route" in clause:
        if clause.get("excludes_modeless_hint_route") is not True:
            return False
        return not _case_uses_argen_modeless_contact_templates(case_data)
    if "material_is_adz" in clause:
        want = clause["material_is_adz"]
        if not isinstance(want, bool):
            return False
        return template_rules.is_adz_material(case_data.get("material", "")) == want
    if "scanner_is_itero" in clause:
        want = clause["scanner_is_itero"]
        if not isinstance(want, bool):
            return False
        return template_rules.is_itero_scanner(case_data.get("scanner", "")) == want
    if "non_argen_shade" in clause:
        want = clause["non_argen_shade"]
        if not isinstance(want, bool):
            return False
        return template_rules.is_non_argen_shade(case_data.get("shade", "")) == want
    return False


def evaluate_doctor_when_group(case_data: Dict[str, Any], when: Dict[str, Any]) -> bool:
    if "all" in when:
        clauses = when.get("all") or []
        if not isinstance(clauses, list):
            return False
        return all(evaluate_doctor_when_clause(case_data, c) for c in clauses)
    if "any" in when:
        clauses = when.get("any") or []
        if not isinstance(clauses, list):
            return False
        return any(evaluate_doctor_when_clause(case_data, c) for c in clauses)
    return False
