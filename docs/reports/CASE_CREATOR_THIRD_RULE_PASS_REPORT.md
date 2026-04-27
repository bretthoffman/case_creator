CASE CREATOR THIRD RULE PASS REPORT

## 1. Summary of changes

This pass centralized routing/destination **pure policy primitives** into a new rules module while keeping processor ownership of runtime destination execution and output flow.

Changes made:
- Created `domain/rules/routing_rules.py`.
- Moved pure routing/destination classification helpers into `routing_rules`.
- Centralized pure Serbia/designer/AI/Argen label classification helpers.
- Centralized pure template-family-to-destination-key policy helper.
- Centralized pure zip-policy predicate helper (`should_zip_modeless_argen`) with parity-preserving semantics.
- Updated `case_processor_final_clean.py` to delegate to centralized routing helpers while preserving:
  - same destination roots used,
  - same AI reroute behavior,
  - same label/log strings,
  - same zip decision behavior.

## 2. Files modified

Created:
- `domain/rules/routing_rules.py`
- `CASE_CREATOR_THIRD_RULE_PASS_REPORT.md`

Modified:
- `case_processor_final_clean.py`

## 3. Logic moved

### From `case_processor_final_clean.py` -> `domain/rules/routing_rules.py`

1. Template filename classification primitives
- `is_argen_template(...)`
- `is_study_template(...)`
- `is_anterior_template(...)`
- `is_ai_template(...)`
- `template_filename(...)`

2. Destination route-key policy (pure classification)
- `destination_key_for_template(...)`
  - preserves current mapping:
    - argen -> argen destination category
    - study/anterior/ai -> 1.9 destination category

3. Serbia/designer/AI label policy (pure classification)
- `is_serbia_case(...)`
- `route_label_for_template(...)`
  - preserves current label outcomes:
    - argen -> ARGEN label
    - study/anterior -> DESIGNER vs SERBIA
    - ai -> AI_DESIGNER vs AI_SERBIA

4. Zip policy primitive
- `should_zip_modeless_argen(...)`
  - preserves current condition:
    - case route is modeless
    - and (template is argen OR destination category is argen)

### Processor delegation updates
- `case_processor_final_clean.should_zip(...)` now delegates to `routing_rules.should_zip_modeless_argen(...)` via destination key mapping.
- Destination root selection now uses `routing_rules.destination_key_for_template(...)` but still maps keys to existing absolute path constants inside processor.
- Route label logging now uses `routing_rules.route_label_for_template(...)` while preserving exact existing log strings.

## 4. Compatibility strategy

- Kept processor as runtime owner of:
  - absolute destination path constants and selection application,
  - output folder creation and placement,
  - downstream packaging/output flow.
- Used route keys/categories only for policy classification.
- Preserved existing AI reroute debug behavior in processor:
  - still logs `"[route] AI template re-routed to DESIGNER path"` under AI template condition.
- Preserved existing log text exactly:
  - `🏭 ARGEN CASE`
  - `🧑‍🎓 DESIGNER CASE`
  - `🧑‍🎓 SERBIA CASE`
  - `🤖 DESIGNER CASE`
  - `🤖 SERBIA CASE`
- Preserved existing `should_zip(...)` call contract and semantics.

## 5. Validation performed

1. **Syntax/compile checks**
- Ran:
  - `python3 -m compileall case_processor_final_clean.py domain/rules/routing_rules.py`
- Result: passed.

2. **Import smoke checks**
- Imported:
  - `case_processor_final_clean`
  - `domain.rules.routing_rules`
- Result: passed; no circular import issues observed.

3. **Focused routing parity assertions**
- Verified representative cases for:
  - Argen template classification,
  - AI template classification,
  - study/anterior classification,
  - destination key outcomes for argen/ai/study/anterior,
  - Serbia/designer and AI-serbia/AI-designer label outcomes,
  - zip/no-zip parity scenarios for modeless + argen/destination combinations.
- Result: all assertions passed.

## 6. Risks or limitations

- Full end-to-end processor runs across production fixtures were not executed in this pass; validation focused on routing primitive parity and import safety.
- Destination execution ownership is still inside processor (intentional), so some routing behavior remains intertwined with legacy flow until a later thin-selector pass.
- Template precedence logic remains untouched and still coupled to downstream behavior (intentional for safety).

## 7. Recommended next pass

Safest next pass:

1. Add a **thin** `domain/decisions/destination_selector.py` compatibility shell that:
   - consumes template name + doctor name,
   - delegates to existing `routing_rules` primitives,
   - returns destination key + label key only.
2. Update processor to call the selector shell (not changing path execution ownership).
3. Keep all absolute path mapping and filesystem output logic in processor for this pass too.
4. Add focused parity checks confirming selector outputs match current routing behavior exactly.

This keeps risk low by centralizing decision composition without moving execution ownership yet.

