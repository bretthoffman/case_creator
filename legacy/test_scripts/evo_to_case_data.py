# evo_to_case_data.py
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))

from typing import Dict, Any, List, Tuple
import re
# ---- feature toggles ----
DISABLE_MODELESS = True  # set False to re-enable later


# ---------------------------
# Shade utilities (inline)
# ---------------------------

# Conversion table → final display names
_SHADE_CONVERSIONS = {
    # Bleach → OM
    "bl1": "OM1",
    "bl2": "OM2",
    "bl3": "OM3",
    "bl4": "OM3",

    # 3D Master → Classic/OM (per your mapping)
    "1m1":   "OM3",
    "1m2":   "A1",
    "2l1.5": "A1",
    "2l2.5": "B2",
    "2m1":   "B1",
    "2m2":   "A2",
    "2m3":   "B2",
    "2r1.5": "A1",
    "2r2.5": "A2",
    "3l1.5": "C2",
    "3l2.5": "A3",
    "3m1":   "C1",
    "3m2":   "A3",
    "3m3":   "B3",
    "3r1.5": "D2",
    "3r2.5": "B3",
    "4l1.5": "D3",
    "4l2.5": "A4",
    "4m1":   "D3",
    "4m2":   "A3.5",
    "4m3":   "A4",
    "4r1.5": "D3",
    "4r2.5": "A4",
    "5m1":   "C3",
    "5m2":   "A4",
    "5m3":   "A4",
}

# Lightest → darkest order
_SHADE_ORDER = [
    "OM1","OM2","OM3","B1","A1","B2","D2","A2","C1","C2",
    "D4","A3","D3","B3","A3.5","B4","C3","A4","C4",
]
_SHADE_RANK = {name.upper(): i for i, name in enumerate(_SHADE_ORDER)}

# Regex helpers
_VITA_PREFIX_RE = re.compile(r"\b(vita[\s\-]?(classic|3d))\b[:\-]?\s*", re.IGNORECASE)
_SEP_RE = re.compile(r"[;,/|]+")
_WS_RE = re.compile(r"\s+")

def _tokenize_shades(raw: str) -> List[str]:
    return [p.strip() for p in _SEP_RE.split(raw or "") if p.strip()]

def _strip_all_vita_prefixes(s: str) -> str:
    return _VITA_PREFIX_RE.sub("", s or "").strip()

def _normalize_case(s: str) -> str:
    s = (s or "").upper()
    s = _WS_RE.sub(" ", s).replace(" .", ".").replace(". ", ".").strip()
    return s

def _canon_key(s: str) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()

def _apply_conversion(s: str) -> str:
    mapped = _SHADE_CONVERSIONS.get(_canon_key(s))
    return mapped if mapped else s

def _best_by_priority(candidates: List[str]) -> str:
    ranked = []
    unknown = []
    for c in candidates:
        key = (c or "").upper().strip()
        if key in _SHADE_RANK:
            ranked.append((_SHADE_RANK[key], c))
        else:
            unknown.append(c)
    if ranked:
        ranked.sort(key=lambda x: x[0])  # lightest first
        return ranked[0][1]
    return unknown[0] if unknown else ""

def _pick_single_shade(raw: str) -> Tuple[str, dict]:
    """
    Returns (final_shade, debug_info).
    - Splits multiple shades
    - Removes every 'Vita Classic' prefix
    - Converts via mapping (BL/3D Master → OM#/A#/B#/C#/D#)
    - De-duplicates POST-conversion
    - Chooses lightest per _SHADE_ORDER
    """
    dbg = {"raw": raw, "tokens": [], "after_strip": [], "converted": [], "dedup": [], "collapsed_duplicates": False}

    tokens = _tokenize_shades(raw)
    dbg["tokens"] = tokens

    cleaned = [_normalize_case(_strip_all_vita_prefixes(t)) for t in tokens if t.strip()]
    dbg["after_strip"] = cleaned

    converted = [_normalize_case(_apply_conversion(c)) for c in cleaned]
    dbg["converted"] = converted

    # De-dup AFTER conversion (handles 4M1 + 4R1.5 → D3 once)
    seen = set()
    unique = []
    for c in converted:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    dbg["dedup"] = unique

    if len(unique) == 1:
        dbg["collapsed_duplicates"] = len(converted) > 1
        return unique[0], dbg

    if not unique:
        return "", dbg

    final = _best_by_priority(unique)
    return final, dbg

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

def _route_from_services(services: list) -> str:
    """
    Legacy route family:
      - 'argen_envision' if service mentions Envision
      - 'argen_adzir'   if it mentions Adzir/ArgenZ (or 'emax zirconia')
      - 'regular'       otherwise
    """
    route = "regular"
    for s in services or []:
        desc = (s.get("description") or s.get("service_description") or "").lower()
        if "envision" in desc:
            return "argen_envision"
        if any(k in desc for k in ["adzir", "argenz", "emax zirconia"]):
            route = "argen_adzir"
    return route

def _needs_model(services: list) -> bool:
    for s in services or []:
        if "model" in (s.get("description") or s.get("service_description") or "").lower():
            return True
    return False

def _is_modeless_from_services(services: list) -> bool:
    """Detect 'modeless' ONLY from service descriptions."""
    for s in services or []:
        desc = (s.get("description") or s.get("service_description") or "")
        if isinstance(desc, str) and "modeless" in desc.lower():
            return True
    return False

def _material_from_services(services: list) -> str:
    """
    Returns 'adz' or 'envision' by scanning service descriptions.
    Defaults to 'envision' if ambiguous.
    """
    mat = "envision"
    for s in services or []:
        d = (s.get("description") or s.get("service_description") or "").lower()
        if any(k in d for k in ("adzir", "argenz")):
            return "adz"
        if "envision" in d:
            mat = "envision"
    return mat

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
