from typing import Any, Dict, List

ADZ_ROUTE_KEYWORDS = ("adzir", "argenz", "emax zirconia")
ADZ_MATERIAL_KEYWORDS = ("adzir", "argenz")

# Preserve existing default semantics from evo_to_case_data.
DISABLE_MODELESS_DEFAULT = True


def is_emax_zirconia(description: str) -> bool:
    return "emax zirconia" in (description or "").lower()


def is_ips_emax(description: str) -> bool:
    """IPS e.max / lithium disilicate — not ArgenZ e.max zirconia."""
    desc = (description or "").lower()
    if is_emax_zirconia(desc):
        return False
    if "lithium disilicate" in desc:
        return True
    if "ips e.max" in desc or "ips emax" in desc:
        return True
    if "e.max" in desc:
        return True
    if "emax" in desc:
        return True
    return False


def route_from_services(services: List[Dict[str, Any]]) -> str:
    """
    Legacy route family:
      - 'argen_envision' if service mentions Envision
      - 'argen_adzir' if it mentions Adzir/ArgenZ (or 'emax zirconia')
      - 'emax' for IPS e.max / lithium disilicate (non-zirconia)
      - 'regular' otherwise
    """
    route = "regular"
    saw_ips_emax = False
    for s in services or []:
        desc = (s.get("description") or s.get("service_description") or "").lower()
        if "envision" in desc:
            return "argen_envision"
        if any(k in desc for k in ADZ_ROUTE_KEYWORDS):
            route = "argen_adzir"
        if is_ips_emax(desc):
            saw_ips_emax = True
    if saw_ips_emax and route == "regular":
        return "emax"
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
    Returns 'adz', 'emax', or 'envision' by scanning service descriptions.
    Defaults to 'envision' if ambiguous.
    """
    mat = "envision"
    for s in services or []:
        d = (s.get("description") or s.get("service_description") or "").lower()
        if any(k in d for k in ADZ_MATERIAL_KEYWORDS):
            return "adz"
        if is_ips_emax(d):
            return "emax"
        if "envision" in d:
            mat = "envision"
    return mat
