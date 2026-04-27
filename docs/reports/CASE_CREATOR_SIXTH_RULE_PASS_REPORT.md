CASE CREATOR SIXTH RULE PASS REPORT

## 1. Summary of changes

This pass added a thin template decision shell and routed processor template lookups through it, while preserving existing template-selection behavior and precedence.

Changes made:
- Created `domain/decisions/template_selector.py`.
- Added `select_template_path(case_data)` as a conservative compatibility seam that delegates to the current authoritative `template_utils.select_template(...)`.
- Updated `case_processor_final_clean.py` to use `select_template_path(...)` at both template selection call sites:
  - main processing flow
  - `generate_final_xml(...)` template lookup
- Removed direct `select_template` import from processor (no behavior change, only seam redirection).

## 2. Files modified

Created:
- `domain/decisions/template_selector.py`
- `CASE_CREATOR_SIXTH_RULE_PASS_REPORT.md`

Modified:
- `case_processor_final_clean.py`

## 3. Logic moved

### Old composed template decision location
- `case_processor_final_clean.py` directly invoked `template_utils.select_template(case_data)` in:
  - `process_case(...)`
  - `generate_final_xml(...)`

### New decision shell location
- `domain/decisions/template_selector.py`
  - `select_template_path(case_data)` now serves as the decision seam and delegates to the existing precedence logic.

### Authoritative precedence ownership after this pass
- Still remains in `template_utils.select_template(...)` (intentionally unchanged).

## 4. Compatibility strategy

- Used the safest approach: delegation shell only; no template branch logic moved.
- Preserved exact precedence semantics by keeping `template_utils.select_template(...)` as the behavior-authoritative engine.
- Processor now depends on the seam (`select_template_path`) but receives identical template paths.
- No changes made to downstream routing/destination logic, naming, scanner flow, manual-review flow, logging text, settings, or packaging behavior.
- `template_selector` uses local import inside function to avoid potential circular imports during incremental migration.

## 5. Validation performed

1. **Compile checks**
- Ran:
  - `python3 -m compileall domain/decisions/template_selector.py case_processor_final_clean.py template_utils.py`
- Result: passed.

2. **Import/circular checks**
- Imported:
  - `case_processor_final_clean`
  - `domain.decisions.template_selector.select_template_path`
- Result: passed; no circular import issues observed.

3. **Focused template parity checks (old vs new selector seam)**
- Compared `template_utils.select_template(case_data)` vs `select_template_path(case_data)` across representative scenarios:
  - anterior branch
  - study vs non-study
  - signature vs non-signature
  - Abby/Dew case
  - Brier Creek-related case
  - non-Argen shade exception case
  - iTero vs non-iTero branches
  - modeless hint behavior
- Result: outputs matched in all checked scenarios.

## 6. Risks or limitations

- This pass intentionally does not move precedence logic itself; template behavior remains coupled to `template_utils.select_template(...)`.
- Full end-to-end production fixture replay was not executed in this pass; parity checks were focused on template decision seam equivalence.
- Future passes must preserve exact branch order if/when precedence ownership is moved.

## 7. Recommended next pass

Safest next pass:

1. Introduce a **thin** `domain/rules/template_rules.py` module for pure template decision constants/predicate helpers only.
2. Keep `template_utils.select_template(...)` as authoritative and gradually delegate individual pure predicates/constants to `template_rules`.
3. Continue parity checks ensuring no branch-order drift and no template output changes.

This keeps risk low by centralizing primitives without changing precedence ownership.

