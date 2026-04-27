from domain.rules import manual_review_rules
from domain.rules.rule_models import ManualReviewDecision


def no_manual_review() -> ManualReviewDecision:
    """
    Initial decision contract for manual-review centralization.
    Gate logic remains in legacy processor during this first pass.
    """
    return ManualReviewDecision(requires_manual_review=False)


def evaluate_initial_manual_review(clean, case_data) -> ManualReviewDecision:
    services = clean.get("services", []) or []
    teeth = manual_review_rules.all_teeth_in_services(services)
    units_gt1 = manual_review_rules.has_units_gt1(services)

    if len(teeth) > 1 or units_gt1:
        message = "❌ Multiple units — manual import required"
        detail = f"🦷 Detected teeth: {', '.join(sorted(teeth))}" if teeth else "🦷 EVO reports units > 1"
        return ManualReviewDecision(
            requires_manual_review=True,
            reason_key=manual_review_rules.REASON_MULTI_UNIT,
            message=message,
            detail=detail,
            return_value=message,
        )

    route = (case_data.get("material_hint", {}).get("route") or "").lower()
    if not manual_review_rules.route_is_allowed(route):
        material_hint = manual_review_rules.extract_material_hint_keyword(services)
        if material_hint:
            message = f"❌ Manual import required — material: {material_hint}"
        else:
            message = "❌ Manual import required — unsupported material (not Envision/Adzir)"
        return ManualReviewDecision(
            requires_manual_review=True,
            reason_key=manual_review_rules.REASON_UNSUPPORTED_MATERIAL,
            message=message,
            return_value="❌ Manual import required — material",
        )

    return no_manual_review()


def evaluate_jotform_manual_review(first: str, last: str, matcher) -> ManualReviewDecision:
    if manual_review_rules.is_jotform_manual_case(first, last, matcher):
        message = "🟡 JOTFORM CASE, requires manual import"
        return ManualReviewDecision(
            requires_manual_review=True,
            reason_key=manual_review_rules.REASON_JOTFORM,
            message=message,
            return_value=message,
        )
    return no_manual_review()
