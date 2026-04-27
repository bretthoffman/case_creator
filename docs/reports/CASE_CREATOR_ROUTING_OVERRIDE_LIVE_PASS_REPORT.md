CASE CREATOR ROUTING OVERRIDE LIVE PASS REPORT

## 1. Summary of changes

This pass made **routing override config** live in the narrowest supported way:
- live source: validated `routing_overrides.json` from existing loader foundation.
- live effect: template-family -> destination-key override only.
- live integration seam: `domain/decisions/destination_selector.py`.

No label override behavior, path override behavior, or advanced routing DSL is live in this pass.

## 2. Files modified

Created:
- `infrastructure/config/routing_override_runtime.py`
- `CASE_CREATOR_ROUTING_OVERRIDE_LIVE_PASS_REPORT.md`

Modified:
- `domain/decisions/destination_selector.py`

## 3. Live integration point

Runtime flow for routing overrides in this pass:

1. `destination_selector.select_destination(...)` now calls `resolve_destination_key(template_path_or_name)`.
2. `resolve_destination_key(...)` in `infrastructure/config/routing_override_runtime.py`:
   - infers template family key (`argen` / `study` / `anterior` / `ai`) using baseline classification precedence,
   - starts from baseline family->destination mapping,
   - reads validated `routing_overrides` effective config,
   - applies first matching valid family override to destination key.
3. `route_label_key` continues to be derived from baseline `routing_rules.route_label_for_template(...)` (not config-driven).

Processor ownership remains unchanged:
- processor still maps destination keys to absolute path constants,
- processor still owns filesystem output flow and packaging behavior.

## 4. Supported live behavior

Live now:
- `routing_overrides.template_family_route_overrides` affects destination key resolution for supported family keys.

Not live in this pass:
- route label overrides from config,
- Serbia/designer label overrides,
- raw path overrides,
- doctor-based routing override config,
- zip behavior override config.

Already live from earlier passes:
- doctor template override key (narrow)
- shade non-argen marker override (narrow)

## 5. Fallback behavior

Baseline behavior is preserved when:
- routing override file is missing,
- routing override file is malformed,
- routing override file is invalid,
- routing override file is valid but no family override applies,
- routing override values are unsupported.

Fallback details:
- per-family defaults retained by loader on read/validation failure,
- routing runtime resolver falls back to baseline family mapping on any runtime issue,
- label behavior always remains baseline in this pass.

## 6. Validation performed

1. **Compile/import checks**
- Compiled:
  - `routing_override_runtime.py`
  - `destination_selector.py`
- Import smoke passed for:
  - `case_processor_final_clean`
  - `select_destination`
  - `resolve_destination_key`

2. **Focused live behavior scenarios**
- no routing config -> baseline destination key.
- malformed routing config -> baseline destination key.
- invalid routing config -> baseline destination key.
- valid config reproducing baseline mapping -> unchanged destination keys.
- valid config changing supported mapping (`argen -> 1_9`) -> destination key changed accordingly.
- label outputs remained baseline under changed routing config.
- confirmed processor path constants remain the same and still used.

All checks passed.

## 7. Risks or limitations

- Routing runtime preview is cached (`lru_cache`), so config edits require restart (or explicit cache clear) to take effect immediately.
- Current override application uses first matching family override deterministically; no advanced conflict strategy beyond file order is implemented (intentional simplicity).
- Full end-to-end production fixture replay was not run; targeted scenario checks were performed.

## 8. Recommended next pass

Safest next pass:

1. Keep doctor + shade + routing live as-is.
2. Add low-risk diagnostics/status exposure for effective business-rule load state in existing operational surfaces.
3. Then enable the next family in narrow mode (recommended: constrained `argen_modes` toggles), with strict validation and per-family fallback semantics matching current guardrails.

