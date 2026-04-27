CASE CREATOR FIFTH RULE PASS REPORT

## 1. Summary of changes

This pass centralized naming/suffix **pure rule primitives** into a dedicated rules module while preserving processor ownership of output execution.

Changes made:
- Created `domain/rules/naming_rules.py`.
- Centralized pure naming/suffix behavior:
  - Argen suffix behavior (`os`)
  - iTero suffix behavior (`i`)
  - combined suffix composition order (`osi` when both apply)
  - final case-id formatting with underscore only when suffix is non-empty.
- Updated `case_processor_final_clean.py` to delegate naming/suffix classification to `naming_rules.build_case_naming(...)`.
- Preserved existing behavior where `case_data["case_id"]` is only updated when suffix is present.

## 2. Files modified

Created:
- `domain/rules/naming_rules.py`
- `CASE_CREATOR_FIFTH_RULE_PASS_REPORT.md`

Modified:
- `case_processor_final_clean.py`

## 3. Logic moved

### Old location: `case_processor_final_clean.py`
- Inline suffix composition block:
  - check Argen template -> append `"os"`
  - check iTero scanner -> append `"i"`
  - if suffix exists, append `_{suffix}` to `case_id`
  - update `case_data["case_id"]` only when suffix exists

### New location: `domain/rules/naming_rules.py`
- `build_case_naming(case_id, template_path_or_name, scanner_name)`:
  - returns structured naming decision with:
    - `suffix`
    - `final_case_id`
- `CaseNamingDecision` dataclass
- Constants:
  - `ARGEN_SUFFIX = "os"`
  - `ITERO_SUFFIX = "i"`

## 4. Compatibility strategy

- Processor still owns:
  - destination path application,
  - folder/output creation,
  - packaging/output flow,
  - all logging text emission.
- Delegation change is minimal: processor calls naming helper, then applies same existing mutation behavior.
- Preserved exact suffix order/format semantics:
  - Argen then iTero (`os` + `i` => `osi`).
- Preserved exact conditional `case_data["case_id"]` update behavior (only when suffix exists).
- No log strings changed.

## 5. Validation performed

1. **Compile checks**
- Ran:
  - `python3 -m compileall domain/rules/naming_rules.py case_processor_final_clean.py`
- Result: passed.

2. **Import/circular checks**
- Imported:
  - `case_processor_final_clean`
  - `domain.rules.naming_rules`
- Result: passed; no circular import issues observed.

3. **Focused parity assertions**
- Verified:
  - Argen template naming outcome -> `_os`
  - iTero scanner naming outcome -> `_i`
  - combined Argen + iTero naming outcome -> `_osi`
  - non-argen/non-itero -> unchanged case id
  - final case-id formatting remains unchanged.
- Result: all assertions passed.

## 6. Risks or limitations

- Full end-to-end production fixture replay was not run in this pass; validation focused on naming primitive parity and import safety.
- Some downstream behavior depends on exact case-id mutation timing; current pass preserves existing timing/condition, but future refactors must keep this contract stable.

## 7. Recommended next pass

Safest next pass:

1. Add a thin `domain/decisions/template_selector.py` compatibility shell that delegates to existing template rule primitives without changing precedence ownership yet.
2. Keep `template_utils.select_template` runtime behavior and order exactly unchanged (wrapper/adapter style).
3. Add focused parity checks for representative template selection branches (anterior, modeless hint, signature/non-signature, shade exceptions, iTero/non-iTero).

This continues centralization while avoiding high-risk execution ownership changes.

