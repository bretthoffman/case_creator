CASE CREATOR YAML CONFIG MIGRATION REPORT

## 1. Summary of changes

Migrated editable exposed business-rule files to YAML as the preferred format and added self-documenting comment headers.

What was migrated:
- loader now supports YAML parsing and prefers YAML over JSON when both exist.
- editable files now provided as YAML:
  - `doctor_overrides`
  - `shade_overrides`
  - `routing_overrides`
  - `argen_modes`
- top-of-file instruction notes were added to each editable YAML file, including restart-required guidance.

Live behavior remains:
- doctor template override key behavior,
- shade non-argen marker override behavior,
- routing family -> destination-key override behavior,
- argen contact_model_mode behavior.

## 2. Files modified

Created:
- `business_rules/v1/doctor_overrides.yaml`
- `business_rules/v1/shade_overrides.yaml`
- `business_rules/v1/routing_overrides.yaml`
- `business_rules/v1/argen_modes.yaml`
- `CASE_CREATOR_YAML_CONFIG_MIGRATION_REPORT.md`

Modified:
- `infrastructure/config/business_rule_loader.py`
- `infrastructure/config/business_rule_schemas.py`
- `requirements.txt`

## 3. Loader and format changes

### YAML support
- Added YAML parsing via `yaml.safe_load`.
- Added `PyYAML==6.0.3` to `requirements.txt`.

### Discovery and precedence
- `business_rule_schemas` now defines per-family candidate filenames:
  - YAML first (`.yaml`, then `.yml`), JSON last (compatibility fallback).
- Loader chooses the first existing candidate deterministically.
- If multiple files exist for a family, loader uses the preferred one and records a warning.

### Compatibility/fallback behavior
- YAML is preferred source of truth.
- JSON remains supported as fallback compatibility.
- Parsing/validation errors still trigger per-family defaults exactly as before.

## 4. Editable file structure

Editable YAML files now in:
- `business_rules/v1/doctor_overrides.yaml`
- `business_rules/v1/shade_overrides.yaml`
- `business_rules/v1/routing_overrides.yaml`
- `business_rules/v1/argen_modes.yaml`

Each file now includes:
1. First-line all-caps instruction:
   - `SAVE FILE AND RESTART APP AFTER EDITING FOR THE CHANGES TO TAKE EFFECT`
2. Comment notes describing:
   - what the file controls,
   - expected structure,
   - editable fields,
   - allowed values,
   - matching/ordering notes where relevant,
   - examples and guardrails.

## 5. Behavior compatibility

Existing live behavior was preserved:
- doctor override runtime still reads validated doctor rules and applies only `template_override_key`.
- shade runtime still applies only `non_argen_shade_markers`.
- routing runtime still applies only family -> destination key mapping.
- argen modes runtime still applies only constrained `contact_model_mode`.

Safety behavior preserved:
- missing/malformed/invalid files fallback to defaults per family.
- no startup/import crash path introduced.
- no new config families became live.

## 6. Validation performed

1. **Compile/import checks**
- Compiled updated loader/schema/runtime modules successfully.
- Import smoke passed for core runtime and config runtime modules.

2. **Behavior/fallback checks**
- Missing YAML files -> baseline behavior/defaults.
- Malformed YAML -> safe fallback/defaults.
- Invalid YAML schema -> safe fallback/defaults.
- Valid YAML -> reproduces existing live behavior for:
  - doctor overrides,
  - shade markers,
  - routing destination keys,
  - argen contact mode.

3. **YAML precedence checks**
- When both YAML and JSON exist for a family:
  - YAML file selected,
  - deterministic warning emitted,
  - runtime uses YAML-derived effective config.

4. **Instruction note checks**
- Confirmed restart-required all-caps header and explanatory comments are present in each editable YAML file.

## 7. Risks or limitations

- Runtime override resolvers remain cache-backed (`lru_cache`), so edits require restart (or explicit cache clear), which is intentional for this pass.
- JSON compatibility remains; this is useful for migration, but can cause operator confusion if both formats are edited simultaneously (warning is emitted).
- No hot reload behavior in this pass.

## 8. Recommended next pass

Safest next pass:

1. Add lightweight diagnostics/status surfacing for effective config source and validation state (e.g., indicating YAML/JSON source used and warnings).
2. Keep current live families unchanged.
3. Optionally define a future deprecation window for JSON compatibility once YAML usage is stable in deployments.

