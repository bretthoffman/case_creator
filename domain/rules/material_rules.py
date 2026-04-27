from typing import Any, Dict, List

ADZ_ROUTE_KEYWORDS = ("adzir", "argenz", "emax zirconia")
ADZ_MATERIAL_KEYWORDS = ("adzir", "argenz")

# Preserve existing default semantics from evo_to_case_data.
DISABLE_MODELESS_DEFAULT = True


def route_from_services(services: List[Dict[str, Any]]) -> str:
    """
    Legacy route family:
      - 'argen_envision' if service mentions Envision
      - 'argen_adzir' if it mentions Adzir/ArgenZ (or 'emax zirconia')
      - 'regular' otherwise
    """
    route = "regular"
    for s in services or []:
        desc = (s.get("description") or s.get("service_description") or "").lower()
        if "envision" in desc:
            return "argen_envision"
        if any(k in desc for k in ADZ_ROUTE_KEYWORDS):
            route = "argen_adzir"
    return route


def needs_model(services: List[Dict[str, Any]]) -> bool:
    for s in services or []:
        if "model" in (s.get("description") or s.get("service_description") or "").lower():
            return True
    return False


def is_modeless_from_services(services: List[Dict[str, Any]]) -> bool:
    """Detect 'modeless' ONLY from service descriptions."""
    for s in services or []:
        desc = (s.get("description") or s.get("service_description") or "")
        if isinstance(desc, str) and "modeless" in desc.lower():
            return True
    return False


def material_from_services(services: List[Dict[str, Any]]) -> str:
    """
    Returns 'adz' or 'envision' by scanning service descriptions.
    Defaults to 'envision' if ambiguous.
    """
    mat = "envision"
    for s in services or []:
        d = (s.get("description") or s.get("service_description") or "").lower()
        if any(k in d for k in ADZ_MATERIAL_KEYWORDS):
            return "adz"
        if "envision" in d:
            mat = "envision"
    return mat
