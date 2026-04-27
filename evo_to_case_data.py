# evo_to_case_data.py
from typing import Dict, Any

from domain.rules import material_rules
from domain.rules import shade_rules

# ---- feature toggles ----
DISABLE_MODELESS = True  # set False to re-enable later

# ---------------------------
# Existing evo → case helpers
# ---------------------------

def _first_shade_raw(services: list) -> str:
    """Grab the first non-empty raw shade string from services.toothlist[]."""
    for s in services or []:
        for t in s.get("toothlist", []):
            shade = (t.get("shades") or "").strip()
            if shade:
                return shade
    return ""

def _first_tooth(services: list) -> str:
    for s in services or []:
        for t in s.get("toothlist", []):
            num = (t.get("tooth_num") or "").strip()
            if num:
                return num
    return ""

def _tokenize_shades(raw: str):
    return shade_rules.tokenize_shades(raw)

def _strip_all_vita_prefixes(s: str) -> str:
    return shade_rules.strip_all_vita_prefixes(s)

def _normalize_case(s: str) -> str:
    return shade_rules.normalize_case(s)

def _canon_key(s: str) -> str:
    return shade_rules.canon_key(s)


def _apply_conversion(s: str) -> str:
    return shade_rules.apply_conversion(s)


def _best_by_priority(candidates):
    return shade_rules.best_by_priority(candidates)


def _pick_single_shade(raw: str):
    return shade_rules.pick_single_shade(raw)


def _route_from_services(services: list) -> str:
    return material_rules.route_from_services(services)


def _needs_model(services: list) -> bool:
    return material_rules.needs_model(services)


def _is_modeless_from_services(services: list) -> bool:
    return material_rules.is_modeless_from_services(services)


def _material_from_services(services: list) -> str:
    return material_rules.material_from_services(services)

# ---------------------------
# Main builder
# ---------------------------

def build_case_data_from_evo(clean: Dict[str, Any]) -> Dict[str, Any]:
    case = clean.get("case", {})
    patient = clean.get("patient", {})
    services = clean.get("services", [])

    # Tooth & Shade (shade locked up front)
    tooth = _first_tooth(services)
    raw_shade = _first_shade_raw(services)
    shade, _shade_dbg = _pick_single_shade(raw_shade)

    # Base route from services (regular / argen_envision / argen_adzir)
    route = _route_from_services(services)
    needs_model = _needs_model(services)

    # Detect modeless strictly from service descriptions
    detected_modeless = _is_modeless_from_services(services)

    # Feature toggle: default to DISABLE_MODELESS=True if not defined at module level
    disable_modeless = bool(globals().get("DISABLE_MODELESS", True))

    # Effective modeless flag (will be False while disabled)
    modeless = detected_modeless and not disable_modeless

    # Material is useful downstream for any Argen decisions
    material = _material_from_services(services)  # 'adz' or 'envision'

    # Only label as 'modeless' if it's enabled, an ARGEN case, AND services indicate modeless
    if modeless and route in ("argen_envision", "argen_adzir"):
        route = "modeless"  # family-level label; template_utils can split using 'material' if re-enabled

    try:
        tooth_num = int(tooth)
        arch = "Upper" if 1 <= tooth_num <= 16 else "Lower"
        is_anterior = (6 <= tooth_num <= 11) or (22 <= tooth_num <= 27)
    except Exception:
        arch = "Upper"
        is_anterior = False

    order_comments = case.get("preferences_text") or ""
    due_date_iso = case.get("delivery_date") or case.get("original_due_date") or ""

    return {
        "case_id": case.get("number", ""),
        "order_id": str(case.get("id") or ""),
        "doctor": f"{clean.get('doctor',{}).get('first_name','')} {clean.get('doctor',{}).get('last_name','')}".strip(),
        "first": patient.get("first_name", "") or "",
        "last": patient.get("last_name", "") or "",
        "received_date": case.get("order_date") or "",
        "due_date": due_date_iso,
        "tooth": tooth,
        "is_anterior": is_anterior,

        # ✅ Shade is finalized here (single, converted, lightest)
        "shade": shade,

        "arch": arch,
        "scanner": "",
        "signature": False,
        "is_ai": False,
        "OrderComments": order_comments,

        # Human-readable (will always be "model" while disabled)
        "model_mode": "modeless" if modeless and route == "modeless" else "model",

        # Hints for downstream selection (template_utils / processor)
        "material_hint": {
            "route": route,        # while disabled: 'argen_envision'/'argen_adzir'/'regular' (never 'modeless')
            "needs_model": needs_model,
            "modeless": modeless,  # False while disabled
            "material": material,  # 'adz' or 'envision'
        },

        # Optional: include debug info if you want to log later
        # "shade_debug": _shade_dbg,
    }
