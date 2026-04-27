import re
from typing import List, Tuple

# Conversion table -> final display names
SHADE_CONVERSIONS = {
    # Bleach -> OM
    "bl1": "OM1",
    "bl2": "OM2",
    "bl3": "OM3",
    "bl4": "OM3",
    # 3D Master -> Classic/OM
    "1m1": "OM3",
    "1m2": "A1",
    "2l1.5": "A1",
    "2l2.5": "B2",
    "2m1": "B1",
    "2m2": "A2",
    "2m3": "B2",
    "2r1.5": "A1",
    "2r2.5": "A2",
    "3l1.5": "C2",
    "3l2.5": "A3",
    "3m1": "C1",
    "3m2": "A3",
    "3m3": "B3",
    "3r1.5": "D2",
    "3r2.5": "B3",
    "4l1.5": "D3",
    "4l2.5": "A4",
    "4m1": "D3",
    "4m2": "A3.5",
    "4m3": "A4",
    "4r1.5": "D3",
    "4r2.5": "A4",
    "5m1": "C3",
    "5m2": "A4",
    "5m3": "A4",
}

# Lightest -> darkest order
SHADE_ORDER = [
    "OM1",
    "OM2",
    "OM3",
    "B1",
    "A1",
    "B2",
    "D2",
    "A2",
    "C1",
    "C2",
    "D4",
    "A3",
    "D3",
    "B3",
    "A3.5",
    "B4",
    "C3",
    "A4",
    "C4",
]
SHADE_RANK = {name.upper(): i for i, name in enumerate(SHADE_ORDER)}

VITA_PREFIX_RE = re.compile(r"\b(vita[\s\-]?(classic|3d))\b[:\-]?\s*", re.IGNORECASE)
SEP_RE = re.compile(r"[;,/|]+")
WS_RE = re.compile(r"\s+")


def tokenize_shades(raw: str) -> List[str]:
    return [p.strip() for p in SEP_RE.split(raw or "") if p.strip()]


def strip_all_vita_prefixes(s: str) -> str:
    return VITA_PREFIX_RE.sub("", s or "").strip()


def normalize_case(s: str) -> str:
    s = (s or "").upper()
    s = WS_RE.sub(" ", s).replace(" .", ".").replace(". ", ".").strip()
    return s


def canon_key(s: str) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()


def apply_conversion(s: str) -> str:
    mapped = SHADE_CONVERSIONS.get(canon_key(s))
    return mapped if mapped else s


def best_by_priority(candidates: List[str]) -> str:
    ranked = []
    unknown = []
    for c in candidates:
        key = (c or "").upper().strip()
        if key in SHADE_RANK:
            ranked.append((SHADE_RANK[key], c))
        else:
            unknown.append(c)
    if ranked:
        ranked.sort(key=lambda x: x[0])
        return ranked[0][1]
    return unknown[0] if unknown else ""


def pick_single_shade(raw: str) -> Tuple[str, dict]:
    dbg = {
        "raw": raw,
        "tokens": [],
        "after_strip": [],
        "converted": [],
        "dedup": [],
        "collapsed_duplicates": False,
    }

    tokens = tokenize_shades(raw)
    dbg["tokens"] = tokens

    cleaned = [normalize_case(strip_all_vita_prefixes(t)) for t in tokens if t.strip()]
    dbg["after_strip"] = cleaned

    converted = [normalize_case(apply_conversion(c)) for c in cleaned]
    dbg["converted"] = converted

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

    final = best_by_priority(unique)
    return final, dbg
