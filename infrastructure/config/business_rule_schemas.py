from typing import Any, Dict, List

from domain.rules import routing_rules
from infrastructure.config.business_rule_models import ValidationResult

SUPPORTED_FAMILIES = ("doctor_overrides", "shade_overrides", "routing_overrides", "argen_modes")
FAMILY_FILE_CANDIDATES = {
    # YAML is preferred editable source-of-truth, JSON remains fallback-compatible.
    "doctor_overrides": ("doctor_overrides.yaml", "doctor_overrides.yml", "doctor_overrides.json"),
    "shade_overrides": ("shade_overrides.yaml", "shade_overrides.yml", "shade_overrides.json"),
    "routing_overrides": ("routing_overrides.yaml", "routing_overrides.yml", "routing_overrides.json"),
    "argen_modes": ("argen_modes.yaml", "argen_modes.yml", "argen_modes.json"),
}
SCHEMA_VERSION = 1

# Unified editable document (validation-only until the loader supports dual-read).
UNIFIED_ENVELOPE_SCHEMA_VERSION = 1
ALLOWED_UNIFIED_TOP_LEVEL_KEYS = frozenset(
    {"unified_version", "enabled", *SUPPORTED_FAMILIES}
)

ALLOWED_DOCTOR_ACTION_KEYS = {"template_override_key", "route_label_override_key"}
ALLOWED_ROUTE_LABEL_KEYS = {
    routing_rules.LABEL_ARGEN,
    routing_rules.LABEL_DESIGNER,
    routing_rules.LABEL_SERBIA,
    routing_rules.LABEL_AI_DESIGNER,
    routing_rules.LABEL_AI_SERBIA,
}
# Known template keys from current shipped template folders.
KNOWN_TEMPLATE_KEYS = {
    "argen_envision",
    "argen_adzir",
    "argen_modeless_adzir",
    "argen_modeless_envision",
    "ai_envision",
    "ai_envision_model",
    "ai_adzir",
    "ai_adzir_model",
    "itero_adzir_anterior",
    "itero_adzir_study",
    "itero_envision_anterior",
    "itero_envision_study",
    "reg_adzir_anterior",
    "reg_adzir_study",
    "reg_envision_anterior",
    "reg_envision_study",
}

ALLOWED_SHADE_ACTION_KEYS = {"template_family_override_key"}
ALLOWED_TEMPLATE_FAMILY_OVERRIDE_KEYS = {"ai_family", "argen_family"}
ALLOWED_ROUTE_FAMILY_KEYS = {"argen", "ai", "study", "anterior"}
ALLOWED_DESTINATION_KEYS = {routing_rules.DEST_ARGEN, routing_rules.DEST_1_9}
# Live values for argen_modes.contact_model_mode (see validate_argen_modes for legacy migration).
ALLOWED_CONTACT_MODEL_MODES = frozenset({"off", "on"})
ALLOWED_CONTACT_MODEL_DESIGN_FIELD_VALUES = frozenset({"No", "3Shape Automate"})
_LEGACY_CONTACT_MODEL_MODE_MAP = {
    "legacy_default": "off",
    "always_without_contact_models": "off",
    "always_with_contact_models": "on",
}

# --- Expanded doctor override schema (offline / future live; see doctor_policy_resolver) ---
ALLOWED_DOCTOR_MATCH_PREDICATES = frozenset({"abby_dew", "vd_brier_creek"})
ALLOWED_DOCTOR_WHEN_FIELDS = frozenset({"has_study", "signature", "shade_usable", "is_anterior"})
ALLOWED_DOCTOR_WHEN_GROUP_KEYS = frozenset({"all", "any"})
ALLOWED_DOCTOR_SPECIAL_CLAUSE_KEYS = frozenset(
    {
        "material_is_adz",
        "scanner_is_itero",
        "non_argen_shade",
        "excludes_modeless_hint_route",
    }
)
# Outcome actions are restricted to template selection only (no label overrides in outcomes yet).
ALLOWED_DOCTOR_OUTCOME_ACTION_KEYS = frozenset({"template_override_key"})


def _validate_doctor_when_clause(clause: Any, path: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(clause, dict):
        return [f"{path} must be an object."]
    if "field" in clause:
        if set(clause.keys()) != {"field", "eq"}:
            return [f"{path} field-clause must only have keys: field, eq."]
        field = clause.get("field")
        eq = clause.get("eq")
        if not isinstance(field, str) or field not in ALLOWED_DOCTOR_WHEN_FIELDS:
            errors.append(f"{path}.field must be one of {sorted(ALLOWED_DOCTOR_WHEN_FIELDS)}.")
        if not isinstance(eq, bool):
            errors.append(f"{path}.eq must be boolean.")
        return errors
    special = [k for k in ALLOWED_DOCTOR_SPECIAL_CLAUSE_KEYS if k in clause]
    if len(special) == 1 and len(clause) == 1:
        key = special[0]
        val = clause[key]
        if key == "excludes_modeless_hint_route":
            if val is not True:
                errors.append(f"{path}.{key} must be true.")
        elif not isinstance(val, bool):
            errors.append(f"{path}.{key} must be boolean.")
        return errors
    return [f"{path} must be a field/eq clause or a single-boolean key in {sorted(ALLOWED_DOCTOR_SPECIAL_CLAUSE_KEYS)}."]


def _validate_doctor_when_group(when: Any, path: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(when, dict):
        return [f"{path} must be an object."]
    present = [k for k in ALLOWED_DOCTOR_WHEN_GROUP_KEYS if k in when]
    if len(present) != 1:
        errors.append(f"{path} must contain exactly one of: {sorted(ALLOWED_DOCTOR_WHEN_GROUP_KEYS)}.")
        return errors
    key = present[0]
    extra = set(when.keys()) - ALLOWED_DOCTOR_WHEN_GROUP_KEYS
    if extra:
        errors.append(f"{path} has unsupported keys: {sorted(extra)}.")
        return errors
    clauses = when.get(key)
    if not isinstance(clauses, list) or not clauses:
        errors.append(f"{path}.{key} must be a non-empty list.")
        return errors
    for i, clause in enumerate(clauses):
        errors.extend(_validate_doctor_when_clause(clause, f"{path}.{key}[{i}]"))
    return errors


def _validate_doctor_outcomes(outcomes: Any, path: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(outcomes, list):
        return [f"{path} must be a list."]
    for i, item in enumerate(outcomes):
        p = f"{path}[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{p} must be an object.")
            continue
        wh = item.get("when")
        act = item.get("action")
        if wh is None:
            errors.append(f"{p} must include when.")
            continue
        errors.extend(_validate_doctor_when_group(wh, f"{p}.when"))
        if not isinstance(act, dict):
            errors.append(f"{p}.action must be an object.")
            continue
        unknown = set(act.keys()) - ALLOWED_DOCTOR_OUTCOME_ACTION_KEYS
        if unknown:
            errors.append(f"{p}.action has unsupported keys: {sorted(unknown)}.")
            continue
        tk = act.get("template_override_key")
        if not isinstance(tk, str) or tk not in KNOWN_TEMPLATE_KEYS:
            errors.append(f"{p}.action.template_override_key must be a known template key.")
    return errors


def default_doctor_overrides() -> Dict[str, Any]:
    return {"version": SCHEMA_VERSION, "enabled": True, "rules": []}


def default_shade_overrides() -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "enabled": True,
        "non_argen_shade_markers": ["C3", "A4"],
        "rules": [],
    }


def default_routing_overrides() -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "enabled": True,
        "template_family_route_overrides": [],
    }


def default_argen_modes() -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "enabled": True,
        "contact_model_mode": "off",
        # Historical modeless templates emitted this value when hardcoded.
        "contact_model_design_field": "3Shape Automate",
    }


def _require_dict(data: Any, label: str) -> List[str]:
    if isinstance(data, dict):
        return []
    return [f"{label} must be an object."]


def _validate_header(data: Dict[str, Any]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    version = data.get("version")
    if version != SCHEMA_VERSION:
        errors.append(f"version must equal {SCHEMA_VERSION}.")

    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        errors.append("enabled must be boolean when provided.")

    return ValidationResult(valid=not errors, normalized=data, errors=errors, warnings=warnings)


def validate_doctor_overrides(data: Any) -> ValidationResult:
    errors = _require_dict(data, "doctor_overrides")
    if errors:
        return ValidationResult(valid=False, errors=errors)
    header = _validate_header(data)
    errors.extend(header.errors)
    warnings: List[str] = list(header.warnings)

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        errors.append("rules must be a list.")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    seen_ids = set()
    normalized_rules = []
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"rules[{idx}] must be an object.")
            continue
        rid = rule.get("id")
        if not isinstance(rid, str) or not rid.strip():
            errors.append(f"rules[{idx}].id must be a non-empty string.")
            continue
        if rid in seen_ids:
            errors.append(f"duplicate rule id: {rid}")
            continue
        seen_ids.add(rid)

        enabled = rule.get("enabled", True)
        if not isinstance(enabled, bool):
            errors.append(f"rules[{idx}].enabled must be boolean when provided.")
            continue

        match = rule.get("match")
        action = rule.get("action")
        outcomes = rule.get("outcomes")
        rule_when = rule.get("when")

        if not isinstance(match, dict):
            errors.append(f"rules[{idx}].match must be an object.")
            continue

        unknown_match = set(match.keys()) - {"contains_any", "contains_all", "predicate"}
        if unknown_match:
            errors.append(f"rules[{idx}].match has unsupported keys: {sorted(unknown_match)}.")
            continue

        predicate = match.get("predicate")
        if predicate is not None:
            if not isinstance(predicate, str) or predicate not in ALLOWED_DOCTOR_MATCH_PREDICATES:
                errors.append(
                    f"rules[{idx}].match.predicate must be one of {sorted(ALLOWED_DOCTOR_MATCH_PREDICATES)}."
                )
                continue

        contains_any = match.get("contains_any")
        contains_all = match.get("contains_all")
        if predicate is None and contains_any is None and contains_all is None:
            errors.append(
                f"rules[{idx}].match must include predicate and/or contains_any and/or contains_all."
            )
            continue
        bad_match_lists = False
        for key, value in (("contains_any", contains_any), ("contains_all", contains_all)):
            if value is not None:
                if not isinstance(value, list) or not all(isinstance(x, str) and x.strip() for x in value):
                    errors.append(f"rules[{idx}].match.{key} must be a list of non-empty strings.")
                    bad_match_lists = True
        if bad_match_lists:
            continue

        if rule_when is not None:
            we = _validate_doctor_when_group(rule_when, f"rules[{idx}].when")
            if we:
                errors.extend(we)
                continue

        outcomes_list: List[Dict[str, Any]] = []
        if outcomes is not None:
            if not isinstance(outcomes, list):
                errors.append(f"rules[{idx}].outcomes must be a list.")
                continue
            oe = _validate_doctor_outcomes(outcomes, f"rules[{idx}].outcomes")
            if oe:
                errors.extend(oe)
                continue
            outcomes_list = list(outcomes)

        if action is None:
            action = {}
        if not isinstance(action, dict):
            errors.append(f"rules[{idx}].action must be an object.")
            continue

        has_outcomes = bool(outcomes_list)
        if has_outcomes:
            if action:
                errors.append(
                    f"rules[{idx}] with outcomes must use an empty action object (move keys into outcomes)."
                )
                continue
            normalized_action: Dict[str, Any] = {}
        else:
            unknown_action_keys = set(action.keys()) - ALLOWED_DOCTOR_ACTION_KEYS
            if unknown_action_keys:
                errors.append(
                    f"rules[{idx}].action contains unsupported keys: {sorted(unknown_action_keys)}"
                )
                continue
            if not action:
                errors.append(
                    f"rules[{idx}].action must include at least one supported key when outcomes are absent."
                )
                continue

            tk = action.get("template_override_key")
            if tk is not None:
                if not isinstance(tk, str) or tk not in KNOWN_TEMPLATE_KEYS:
                    errors.append(f"rules[{idx}].action.template_override_key must be a known template key.")
                    continue

            rk = action.get("route_label_override_key")
            if rk is not None:
                if not isinstance(rk, str) or rk not in ALLOWED_ROUTE_LABEL_KEYS:
                    errors.append(
                        f"rules[{idx}].action.route_label_override_key must be a known route label key."
                    )
                    continue

            normalized_action = dict(action)

        norm_match: Dict[str, Any] = {
            "contains_any": [x.strip() for x in (contains_any or [])],
            "contains_all": [x.strip() for x in (contains_all or [])],
        }
        if predicate is not None:
            norm_match["predicate"] = predicate

        normalized_rule: Dict[str, Any] = {
            "id": rid.strip(),
            "enabled": enabled,
            "match": norm_match,
            "action": normalized_action,
        }
        if rule_when is not None:
            normalized_rule["when"] = rule_when
        if outcomes_list:
            normalized_rule["outcomes"] = outcomes_list

        normalized_rules.append(normalized_rule)

    normalized = {
        "version": SCHEMA_VERSION,
        "enabled": bool(data.get("enabled", True)),
        "rules": normalized_rules,
    }
    return ValidationResult(valid=not errors, normalized=normalized, errors=errors, warnings=warnings)


def validate_shade_overrides(data: Any) -> ValidationResult:
    errors = _require_dict(data, "shade_overrides")
    if errors:
        return ValidationResult(valid=False, errors=errors)
    header = _validate_header(data)
    errors.extend(header.errors)
    warnings: List[str] = list(header.warnings)

    markers = data.get("non_argen_shade_markers", [])
    if not isinstance(markers, list) or not all(isinstance(x, str) and x.strip() for x in markers):
        errors.append("non_argen_shade_markers must be a list of non-empty strings.")

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        errors.append("rules must be a list.")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    seen_ids = set()
    normalized_rules = []
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"rules[{idx}] must be an object.")
            continue
        rid = rule.get("id")
        if not isinstance(rid, str) or not rid.strip():
            errors.append(f"rules[{idx}].id must be a non-empty string.")
            continue
        if rid in seen_ids:
            errors.append(f"duplicate rule id: {rid}")
            continue
        seen_ids.add(rid)

        enabled = rule.get("enabled", True)
        if not isinstance(enabled, bool):
            errors.append(f"rules[{idx}].enabled must be boolean when provided.")
            continue

        match = rule.get("match")
        action = rule.get("action")
        if not isinstance(match, dict):
            errors.append(f"rules[{idx}].match must be an object.")
            continue
        if not isinstance(action, dict):
            errors.append(f"rules[{idx}].action must be an object.")
            continue

        shade_in = match.get("shade_in")
        if not isinstance(shade_in, list) or not all(isinstance(x, str) and x.strip() for x in shade_in):
            errors.append(f"rules[{idx}].match.shade_in must be a list of non-empty strings.")
            continue

        unknown_action_keys = set(action.keys()) - ALLOWED_SHADE_ACTION_KEYS
        if unknown_action_keys:
            errors.append(f"rules[{idx}].action contains unsupported keys: {sorted(unknown_action_keys)}")
            continue

        tfk = action.get("template_family_override_key")
        if tfk is None:
            errors.append(f"rules[{idx}].action.template_family_override_key is required.")
            continue
        if not isinstance(tfk, str) or tfk not in ALLOWED_TEMPLATE_FAMILY_OVERRIDE_KEYS:
            errors.append(
                f"rules[{idx}].action.template_family_override_key must be one of "
                f"{sorted(ALLOWED_TEMPLATE_FAMILY_OVERRIDE_KEYS)}."
            )
            continue

        normalized_rules.append(
            {
                "id": rid,
                "enabled": enabled,
                "match": {"shade_in": [x.strip() for x in shade_in]},
                "action": {"template_family_override_key": tfk},
            }
        )

    normalized = {
        "version": SCHEMA_VERSION,
        "enabled": bool(data.get("enabled", True)),
        "non_argen_shade_markers": [x.strip() for x in markers] if isinstance(markers, list) else [],
        "rules": normalized_rules,
    }
    return ValidationResult(valid=not errors, normalized=normalized, errors=errors, warnings=warnings)


def validate_routing_overrides(data: Any) -> ValidationResult:
    errors = _require_dict(data, "routing_overrides")
    if errors:
        return ValidationResult(valid=False, errors=errors)
    header = _validate_header(data)
    errors.extend(header.errors)
    warnings: List[str] = list(header.warnings)

    overrides = data.get("template_family_route_overrides", [])
    if not isinstance(overrides, list):
        errors.append("template_family_route_overrides must be a list.")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    normalized_overrides = []
    for idx, entry in enumerate(overrides):
        if not isinstance(entry, dict):
            errors.append(f"template_family_route_overrides[{idx}] must be an object.")
            continue
        family_key = entry.get("family_key")
        destination_key = entry.get("destination_key")
        if not isinstance(family_key, str) or family_key not in ALLOWED_ROUTE_FAMILY_KEYS:
            errors.append(
                f"template_family_route_overrides[{idx}].family_key must be one of "
                f"{sorted(ALLOWED_ROUTE_FAMILY_KEYS)}."
            )
            continue
        if not isinstance(destination_key, str) or destination_key not in ALLOWED_DESTINATION_KEYS:
            errors.append(
                f"template_family_route_overrides[{idx}].destination_key must be one of "
                f"{sorted(ALLOWED_DESTINATION_KEYS)}."
            )
            continue
        normalized_overrides.append({"family_key": family_key, "destination_key": destination_key})

    normalized = {
        "version": SCHEMA_VERSION,
        "enabled": bool(data.get("enabled", True)),
        "template_family_route_overrides": normalized_overrides,
    }
    return ValidationResult(valid=not errors, normalized=normalized, errors=errors, warnings=warnings)


def validate_argen_modes(data: Any) -> ValidationResult:
    errors = _require_dict(data, "argen_modes")
    if errors:
        return ValidationResult(valid=False, errors=errors)
    header = _validate_header(data)
    errors.extend(header.errors)
    warnings: List[str] = list(header.warnings)

    contact_model_mode = data.get("contact_model_mode")
    normalized_mode = "off"
    # YAML 1.1 may parse unquoted on/off as booleans
    if contact_model_mode is True:
        contact_model_mode = "on"
        warnings.append(
            'contact_model_mode parsed as YAML boolean true; use quoted string "on" or "off".'
        )
    elif contact_model_mode is False:
        contact_model_mode = "off"
        warnings.append(
            'contact_model_mode parsed as YAML boolean false; use quoted string "on" or "off".'
        )
    if not isinstance(contact_model_mode, str):
        errors.append("contact_model_mode must be a string (or quoted on/off in YAML).")
    elif contact_model_mode in ALLOWED_CONTACT_MODEL_MODES:
        normalized_mode = contact_model_mode
    elif contact_model_mode in _LEGACY_CONTACT_MODEL_MODE_MAP:
        normalized_mode = _LEGACY_CONTACT_MODEL_MODE_MAP[contact_model_mode]
        warnings.append(
            f"contact_model_mode {contact_model_mode!r} is deprecated; using {normalized_mode!r}. "
            "Update argen_modes.yaml to off or on."
        )
    else:
        errors.append(
            "contact_model_mode must be one of "
            f"{sorted(ALLOWED_CONTACT_MODEL_MODES)} (legacy values "
            f"{sorted(_LEGACY_CONTACT_MODEL_MODE_MAP)} are accepted and normalized)."
        )

    design_field = data.get("contact_model_design_field", "3Shape Automate")
    if not isinstance(design_field, str):
        errors.append("contact_model_design_field must be a string.")
    elif design_field not in ALLOWED_CONTACT_MODEL_DESIGN_FIELD_VALUES:
        errors.append(
            "contact_model_design_field must be one of "
            f"{sorted(ALLOWED_CONTACT_MODEL_DESIGN_FIELD_VALUES)}."
        )

    normalized = {
        "version": SCHEMA_VERSION,
        "enabled": bool(data.get("enabled", True)),
        "contact_model_mode": normalized_mode,
        "contact_model_design_field": design_field,
    }
    return ValidationResult(valid=not errors, normalized=normalized, errors=errors, warnings=warnings)


def validate_unified_business_rules_config(data: Any) -> ValidationResult:
    """
    Validate the unified Case Creator business-rules YAML/JSON document (envelope + families).

    **Runtime:** ``load_business_rule_config_preview`` validates the unified document when
    ``case_creator_rules.yaml`` / ``case_creator_rules.yml`` is present. Per-family YAML files are
    not read at runtime; if the unified file is missing or invalid, the loader uses ``default_*()``
    for every family (see loader docs).

    **Allowed top-level keys** (see ``ALLOWED_UNIFIED_TOP_LEVEL_KEYS``; any other key is an error):

    - ``unified_version`` (**required**): int, must equal ``UNIFIED_ENVELOPE_SCHEMA_VERSION``.
    - ``enabled`` (*optional*): bool. Envelope metadata reserved for a future global kill-switch;
      **no effect** on rule evaluation in this pass.
    - ``doctor_overrides``, ``shade_overrides``, ``routing_overrides``, ``argen_modes`` (*optional
      each*): same root object as the corresponding split file. Each present section is passed to
      the existing ``validate_*`` for that family.

    **Omitted family section:** Treated like an omitted subtree in the unified file: the family is
    filled using ``default_*()`` and a **warning** is recorded. No error is raised for omission alone.

    **Normalized output:** When ``valid``, ``normalized`` is a dict with exactly the four family
    keys, same nested shape as ``BusinessRuleConfigPreview.effective_config``.
    """
    if not isinstance(data, dict):
        return ValidationResult(
            valid=False,
            errors=["Unified business rules config must be a top-level object."],
        )

    unknown = sorted(set(data.keys()) - ALLOWED_UNIFIED_TOP_LEVEL_KEYS)
    if unknown:
        return ValidationResult(
            valid=False,
            errors=[
                "Unknown top-level key(s): "
                f"{unknown}. Allowed: {sorted(ALLOWED_UNIFIED_TOP_LEVEL_KEYS)}."
            ],
        )

    errors: List[str] = []
    warnings: List[str] = []

    if "unified_version" not in data:
        errors.append(f"unified_version is required (integer {UNIFIED_ENVELOPE_SCHEMA_VERSION}).")
    else:
        uv = data["unified_version"]
        if not isinstance(uv, int) or uv != UNIFIED_ENVELOPE_SCHEMA_VERSION:
            errors.append(f"unified_version must be integer {UNIFIED_ENVELOPE_SCHEMA_VERSION}.")

    if "enabled" in data and not isinstance(data["enabled"], bool):
        errors.append("enabled must be boolean when provided.")

    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    validators = {
        "doctor_overrides": validate_doctor_overrides,
        "shade_overrides": validate_shade_overrides,
        "routing_overrides": validate_routing_overrides,
        "argen_modes": validate_argen_modes,
    }
    effective: Dict[str, Dict[str, Any]] = {
        "doctor_overrides": default_doctor_overrides(),
        "shade_overrides": default_shade_overrides(),
        "routing_overrides": default_routing_overrides(),
        "argen_modes": default_argen_modes(),
    }

    for family in SUPPORTED_FAMILIES:
        if family not in data:
            warnings.append(
                f"{family} omitted from unified document; using defaults "
                "(omitted family subtree in unified document)."
            )
            continue
        result = validators[family](data[family])
        warnings.extend(result.warnings)
        if not result.valid:
            errors.extend(f"{family}: {err}" for err in result.errors)
        elif result.normalized is None:
            errors.append(f"{family}: validation produced no normalized payload.")
        else:
            effective[family] = result.normalized

    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    return ValidationResult(valid=True, normalized=effective, errors=[], warnings=warnings)
