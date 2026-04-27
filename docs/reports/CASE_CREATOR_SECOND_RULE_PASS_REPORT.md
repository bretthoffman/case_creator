CASE CREATOR SECOND RULE PASS REPORT

## 1. Summary of changes

This pass centralized the manual-review decision family while preserving existing behavior:

- Added `domain/rules/manual_review_rules.py` with pure manual-review predicates/constants.
- Expanded `domain/decisions/manual_review_selector.py` to evaluate manual-review gates in the same runtime order as before:
  1) multi-unit gate
  2) unsupported material/route gate
  3) Jotform gate (separate selector call path in scan-error handling)
- Updated `case_processor_final_clean.py` to delegate manual-review checks to the selector with minimal changes.
- Kept exact legacy log message strings and early-return return values.
- Extended `ManualReviewDecision` in `domain/rules/rule_models.py` with `return_value` to preserve exact legacy return semantics.

## 2. Files modified

Created:
- `domain/rules/manual_review_rules.py`
- `CASE_CREATOR_SECOND_RULE_PASS_REPORT.md`

Modified:
- `domain/decisions/manual_review_selector.py`
- `domain/rules/rule_models.py`
- `case_processor_final_clean.py`

## 3. Logic moved

### Old location: `case_processor_final_clean.py` (inside `process_case`)
- Inline multi-unit gate logic:
  - tooth extraction from services
  - units > 1 detection
  - manual-return/log behavior
- Inline unsupported route/material allowlist gate:
  - allowed route check
  - material hint keyword extraction loop
  - manual-return/log behavior

### New locations
- `domain/rules/manual_review_rules.py`
  - `all_teeth_in_services(...)`
  - `has_units_gt1(...)`
  - `route_is_allowed(...)`
  - `extract_material_hint_keyword(...)`
  - `is_jotform_manual_case(...)`
  - `ALLOWED_ROUTES`, `MATERIAL_HINT_KEYWORDS`, reason-key constants

- `domain/decisions/manual_review_selector.py`
  - `evaluate_initial_manual_review(clean, case_data)` (ordered multi-unit then unsupported-material/route)
  - `evaluate_jotform_manual_review(first, last, matcher)`
  - `no_manual_review()`

- `domain/rules/rule_models.py`
  - `ManualReviewDecision.return_value` field added for exact legacy return-value parity.

## 4. Compatibility strategy

- `case_processor_final_clean.process_case(...)` now delegates to selector methods but keeps outward behavior unchanged:
  - same log messages
  - same message order
  - same early-return timing
  - same return values (`"❌ Manual import required — material"` preserved exactly for unsupported route path)
- Jotform behavior remains in the same scan-error branch; only predicate/decision evaluation moved.
- No changes made to template selection, destination routing, scanner mechanics, naming/suffix behavior, or log text strings.

## 5. Validation performed

1. **Compile/import validation**
- Ran:
  - `python3 -m compileall case_processor_final_clean.py domain/rules/manual_review_rules.py domain/decisions/manual_review_selector.py domain/rules/rule_models.py`
- Result: success.

2. **Import smoke check**
- Imported:
  - `case_processor_final_clean`
  - `domain.rules.manual_review_rules`
  - `domain.decisions.manual_review_selector`
- Result: success; no circular import issues observed.

3. **Focused parity assertions for representative cases**
- Multi-unit manual-review outcome:
  - `requires_manual_review=True`
  - message `❌ Multiple units — manual import required`
  - detail `🦷 Detected teeth: ...`
  - return value matches legacy behavior.
- Unsupported material/route manual-review outcome:
  - `requires_manual_review=True`
  - message with material keyword (e.g., `gold`)
  - return value preserved as `❌ Manual import required — material`.
- Jotform manual-review outcome:
  - `requires_manual_review=True`
  - message and return value `🟡 JOTFORM CASE, requires manual import`.
- No-manual-review pass-through:
  - `requires_manual_review=False`.
- Result: all assertions passed.

## 6. Risks or limitations

- End-to-end processor execution was not replayed across full production fixtures in this pass; validation focused on centralized manual-review logic and import safety.
- Jotform gate still depends on filesystem-backed matcher behavior at runtime (unchanged from current architecture).
- Manual-review decision model now includes `return_value`; future passes should keep this contract stable until full processor decomposition is complete.

## 7. Recommended next pass

Safest next pass:

1. Centralize **route/destination pure rule primitives** only (not destination selector execution yet), likely into:
   - `domain/rules/routing_rules.py`
2. Keep current processor destination control flow and log labels unchanged by using thin wrappers.
3. Add focused parity checks for:
   - template filename -> route key mapping,
   - Serbia/designer label outcomes,
   - AI route behavior preservation.

This continues low-risk rule extraction without touching template precedence or scanner mechanics.

