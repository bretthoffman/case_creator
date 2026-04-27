CASE CREATOR FOURTH RULE PASS REPORT

## 1. Summary of changes

This pass added a thin destination decision shell that composes existing routing primitives, while preserving processor ownership of actual destination execution.

Changes made:
- Created `domain/decisions/destination_selector.py`.
- Added a minimal `DestinationDecision` model to `domain/rules/rule_models.py`.
- Updated `case_processor_final_clean.py` to call `select_destination(...)` for:
  - `destination_key`
  - `route_label_key`
  - AI alias flag
- Kept absolute destination-path mapping, output placement, and log text emission in processor.

## 2. Files modified

Created:
- `domain/decisions/destination_selector.py`
- `CASE_CREATOR_FOURTH_RULE_PASS_REPORT.md`

Modified:
- `domain/rules/rule_models.py`
- `case_processor_final_clean.py`

## 3. Logic moved

### Old composed decision logic location
- `case_processor_final_clean.py` directly composed:
  - destination key classification (via `routing_rules.destination_key_for_template`)
  - route label classification (via `routing_rules.route_label_for_template`)
  - AI alias check (via `routing_rules.is_ai_template`)

### New composed decision shell location
- `domain/decisions/destination_selector.py`
  - `select_destination(template_path_or_name, doctor_name)` now composes the above three primitive outputs and returns a structured decision.

### What did not move
- Absolute path constants and destination root application remained in `case_processor_final_clean.py`.
- Output folder creation and packaging flow remained in processor.
- Log text emission remained in processor.

## 4. Compatibility strategy

- The selector returns only decision keys/categories, not paths.
- Processor still maps destination key to the same path constants:
  - `DEST_ARGEN` -> `SEND_TO_ARGEN_PATH`
  - `DEST_1_9` -> `SEND_TO_1_9_PATH`
- Processor still emits the exact same route/debug log strings.
- AI alias debug behavior is preserved by checking selector’s `is_ai_alias_to_designer`.
- No changes were made to template precedence, scanner flow, manual-review flow, naming/suffix flow, settings, or packaging behavior.

## 5. Validation performed

1. **Compile checks**
- Ran:
  - `python3 -m compileall domain/decisions/destination_selector.py domain/rules/rule_models.py case_processor_final_clean.py`
- Result: passed.

2. **Import/circular check**
- Imported:
  - `case_processor_final_clean`
  - `domain.decisions.destination_selector.select_destination`
- Result: passed; no circular import issues observed.

3. **Focused selector parity checks**
- Argen template classification:
  - destination key `DEST_ARGEN`
  - label key `LABEL_ARGEN`
- AI template classification:
  - destination key `DEST_1_9`
  - label key `LABEL_AI_DESIGNER`
  - AI alias flag `True`
- Study/anterior designer classification:
  - destination key `DEST_1_9`
  - label key `LABEL_DESIGNER`
- Serbia outcomes:
  - study -> `LABEL_SERBIA`
  - ai -> `LABEL_AI_SERBIA`
- Processor key->path mapping expectation:
  - `DEST_ARGEN` / `DEST_1_9` constants intact
  - destination path constants still used in processor.

All checks passed.

## 6. Risks or limitations

- Full end-to-end processing runs across production fixture sets were not executed in this pass; checks were focused on selector parity and import safety.
- Destination execution ownership remains in processor by design; this is intentional for safety but leaves some coupling in place.
- `DestinationDecision` is intentionally minimal; future passes should avoid expanding it in ways that alter runtime semantics.

## 7. Recommended next pass

Safest next pass:

1. Centralize **naming/suffix pure primitives** into `domain/rules/naming_rules.py` (small, pure helper extraction only).
2. Keep processor ownership of output path execution and file operations unchanged.
3. Add parity checks for:
   - Argen/iTero suffix behavior,
   - final case-id formatting behavior,
   - unchanged route + naming interaction outcomes.

This continues low-risk rule-layer extraction without touching scanner mechanics, template precedence, or packaging flow.

