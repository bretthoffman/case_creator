CASE CREATOR CONFIG LOADER PASS REPORT

## 1. Summary of changes

Added a read-only business-rule config foundation for phase-1 files only:
- discovery logic (source + frozen Windows path conventions),
- JSON parsing,
- schema/semantic validation,
- per-family fallback to defaults,
- structured effective-config preview and diagnostics.

No runtime business behavior was wired to these configs in this pass.

## 2. Files modified

Created:
- `infrastructure/__init__.py`
- `infrastructure/config/__init__.py`
- `infrastructure/config/business_rule_models.py`
- `infrastructure/config/business_rule_schemas.py`
- `infrastructure/config/business_rule_loader.py`
- `CASE_CREATOR_CONFIG_LOADER_PASS_REPORT.md`

Modified:
- None of the existing runtime rule evaluators/processors were modified for live behavior.

## 3. Loader architecture

### Models
- `business_rule_models.py`
  - `ValidationResult`
  - `BusinessRuleFileReport`
  - `BusinessRuleConfigPreview`

### Schemas/validators
- `business_rule_schemas.py`
  - Supported families and filenames:
    - `doctor_overrides.json`
    - `shade_overrides.json`
    - `routing_overrides.json`
  - Per-family defaults:
    - `default_doctor_overrides()`
    - `default_shade_overrides()`
    - `default_routing_overrides()`
  - Per-family validators:
    - `validate_doctor_overrides(...)`
    - `validate_shade_overrides(...)`
    - `validate_routing_overrides(...)`
  - Validation includes:
    - top-level object checks
    - version checks
    - type checks
    - action-key allowlist checks
    - duplicate rule ID checks
    - known key checks (template key / route label key / destination key)

### Loader/discovery
- `business_rule_loader.py`
  - `discover_business_rules_base_dir(...)`
    - source mode: `<repo>/business_rules/v1`
    - frozen Windows mode: `%LOCALAPPDATA%/CaseCreator/business_rules/v1`
    - override base dir for testing
  - `load_business_rule_config_preview(...)`
    - reads each supported file independently
    - validates per family
    - applies per-family fallback defaults when missing/invalid
    - returns structured preview with file-level reports and effective config

## 4. Supported files in this pass

Supported and validated:
- `business_rules/v1/doctor_overrides.json`
- `business_rules/v1/shade_overrides.json`
- `business_rules/v1/routing_overrides.json`

Validation specifics:
- malformed JSON handling
- required top-level object shape
- `version == 1`
- `enabled` boolean type when present
- action key allowlists
- duplicate rule ID detection where rules exist
- constrained known-value checks:
  - known template keys for doctor template overrides
  - known route label keys
  - known destination keys (`argen`, `1_9`)

Not supported/live in this pass:
- `argen_modes.json`
- `template_overrides.json`
- material/manual-review/naming/scanner config files

## 5. Safety/fallback behavior

- Missing file: warning recorded; family defaults used.
- Malformed JSON: error recorded; family defaults used.
- Invalid schema/values: error(s) recorded; family defaults used.
- Per-family fallback behavior (one invalid file does not block others).
- Loader never applies these configs to live business behavior in this pass.
- No startup/import crash path introduced for missing/invalid business-rule files.

## 6. Validation performed

1. **Compile/import checks**
- Compiled:
  - `business_rule_models.py`
  - `business_rule_schemas.py`
  - `business_rule_loader.py`
- Import smoke:
  - imported loader with existing runtime module imports intact.

2. **Scenario checks (focused)**
- all three files missing -> defaults used for all families.
- one malformed file -> defaults used for that family, error captured.
- one invalid-schema file -> defaults used for that family, validation errors captured.
- one valid doctor config -> parsed/normalized/loaded into preview.
- one valid shade config -> parsed/normalized/loaded into preview.
- one valid routing config -> parsed/normalized/loaded into preview.

All checks passed.

3. **Runtime behavior unchanged check (basic)**
- Existing processor imports still work.
- No loader wiring into live rules/processors in this pass.

## 7. Risks or limitations

- Config remains preview-only and not applied (intentional).
- Known template keys are currently hardcoded in schema validator; this may require maintenance if template inventory changes.
- No UI/admin diagnostics surface added in this pass (only model/report-level diagnostics).
- No starter-file generation implemented (intentionally skipped for safety).

## 8. Recommended next pass

Safest next pass:

1. Add a read-only diagnostics hook that can expose loader status safely (e.g., callable status function for existing UI/admin context), still without applying overrides.
2. Add starter-file generation as an opt-in utility only if needed, with strict failure-safe behavior.
3. After that, enable **one** live family first (doctor overrides) behind strict validation and defaults-fallback guardrails, with parity checks proving no change when files are absent.

