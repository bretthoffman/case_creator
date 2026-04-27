from typing import Any, Dict, Iterable, Optional, Set

ALLOWED_ROUTES = ("argen_envision", "argen_adzir", "modeless")
MATERIAL_HINT_KEYWORDS = ("emax", "lithium disilicate", "gold", "alloy", "pfm", "full cast")

REASON_MULTI_UNIT = "multi_unit"
REASON_UNSUPPORTED_MATERIAL = "unsupported_material"
REASON_JOTFORM = "jotform_manual"


def all_teeth_in_services(services: Iterable[Dict[str, Any]]) -> Set[str]:
    teeth: Set[str] = set()
    for service in services or []:
        for tooth in (service.get("toothlist") or []):
            num = (tooth.get("tooth_num") or "").strip()
            if num:
                teeth.add(num)
    return teeth


def has_units_gt1(services: Iterable[Dict[str, Any]]) -> bool:
    return any((service.get("units") or 0) > 1 for service in services or [])


def route_is_allowed(route: str) -> bool:
    return (route or "").lower() in ALLOWED_ROUTES


def extract_material_hint_keyword(services: Iterable[Dict[str, Any]]) -> Optional[str]:
    for service in services or []:
        desc = (service.get("description") or "")
        desc_lower = desc.lower()
        for keyword in MATERIAL_HINT_KEYWORDS:
            if keyword in desc_lower:
                return keyword
    return None


def is_jotform_manual_case(first: str, last: str, matcher) -> bool:
    return bool(matcher(first, last))
