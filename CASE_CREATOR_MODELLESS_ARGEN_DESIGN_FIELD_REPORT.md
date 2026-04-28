# CASE CREATOR MODELLESS ARGEN DESIGN FIELD REPORT

## 1. Summary of changes

Added a new bounded unified-config value, `argen_modes.contact_model_design_field`, and routed it into XML rendering for **only** the two Argen modeless templates:

- `templates/argen_modeless_adzir/argen_modeless_adzir.xml`
- `templates/argen_modeless_envision/argen_modeless_envision.xml`

Those templates now use `{{ARGEN_DESIGN_VALUE}}`, which resolves at runtime to either `"3Shape Automate"` or `"No"` from unified YAML.

Scope is intentionally narrow: non-modeless templates and broader routing/template behavior were not changed.

## 2. Files modified

- `templates/argen_modeless_adzir/argen_modeless_adzir.xml`
- `templates/argen_modeless_envision/argen_modeless_envision.xml`
- `infrastructure/config/business_rule_schemas.py`
- `infrastructure/config/argen_modes_runtime.py`
- `case_processor_final_clean.py`
- `business_rules/v1/case_creator_rules.yaml`
- `business_rules_seed/v1/case_creator_rules.yaml`
- `tests/fixtures/unified_business_rules_baseline.yaml`
- `tests/test_unified_business_rules_config.py`
- `tests/test_argen_modeless_design_field_runtime.py` (new)
- `business_rules/v1/README.md`
- `business_rules/v1/CASE_CREATOR_RULES_EDIT_PROMPT.md`
- `CASE_CREATOR_MODELLESS_ARGEN_DESIGN_FIELD_REPORT.md` (this report)

## 3. Template changes

Updated the Argen modeless custom-data field value line in exactly two templates:

From:
- `<Property name="Value" value="3Shape Automate"/>`

To:
- `<Property name="Value" value="{{ARGEN_DESIGN_VALUE}}"/>`

No other template files were changed. A repo scan confirms `ARGEN_DESIGN_VALUE` appears only in those two XML files.

## 4. YAML/schema changes

### New field

Under `argen_modes`:

- `contact_model_design_field`

### Allowed values (strict)

- `"No"`
- `"3Shape Automate"`

### Validation behavior

- Added `ALLOWED_CONTACT_MODEL_DESIGN_FIELD_VALUES` in schema.
- `validate_argen_modes` now rejects any value outside the two allowed strings.
- Omitted field defaults to `"3Shape Automate"` (explicitly chosen to preserve historical hardcoded template behavior).

### Defaults

- `default_argen_modes()` now includes:
  - `contact_model_design_field: "3Shape Automate"`

## 5. Runtime mapping

Flow now is:

1. Unified YAML is loaded/validated by existing business-rules loader.
2. `infrastructure/config/argen_modes_runtime.py` exposes `resolve_contact_model_design_field()` with bounded fallback default `"3Shape Automate"`.
3. `case_processor_final_clean.generate_final_xml()` checks selected template key.
4. Only when template key is `argen_modeless_adzir` or `argen_modeless_envision`, it injects:
   - `substitutions["ARGEN_DESIGN_VALUE"] = resolve_contact_model_design_field()`
5. Placeholder substitution emits final XML value.

This keeps routing narrowly scoped to modeless Argen templates only.

## 6. Validation performed

### Automated tests run

Command:
- `python3 -m unittest tests.test_unified_business_rules_config tests.test_argen_modeless_design_field_runtime tests.test_unified_canonical_seed_parity -v`

Result:
- **17 tests passed**.

### Coverage from tests/checks

- Schema accepts only `No` / `3Shape Automate` for `contact_model_design_field`.
- Schema rejects unknown values.
- Omitted field defaults to `3Shape Automate`.
- Runtime XML generation for:
  - modeless Adzir resolves to configured value (`No` tested)
  - modeless Envision resolves to omission default (`3Shape Automate` tested)
- Canonical/seed byte parity passed after sync (`scripts/sync_unified_config_seed.py`).
- Repo scan confirms `ARGEN_DESIGN_VALUE` is present only in the two modeless templates.

## 7. Risks or limitations

- Runtime mapping is in `generate_final_xml` and keyed by template folder name; if those two folder names change in the future, this mapping must be updated.
- This pass intentionally does not alter non-modeless template XMLs or broader template-engine behavior.

## 8. Recommended next step

Run a packaged/manual smoke test with two modeless cases (Adzir + Envision):

1. Set `argen_modes.contact_model_design_field: "No"` and confirm XML output value is `No`.
2. Set `"3Shape Automate"` and confirm output.
3. Confirm a non-modeless Argen template output remains unchanged.
