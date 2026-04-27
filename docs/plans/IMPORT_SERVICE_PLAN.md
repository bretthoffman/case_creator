# Import Service Plan (Thin Wrapper)

## What `import_service.py` wraps

- `import_case_by_id(case_id, log_callback=print)`
  - Directly delegates to frozen backend entrypoint:
    - `case_processor_final_clean.process_case_from_id`

## Why this is safer for future UI work

- It introduces a stable, minimal interface that future UI layers can call.
- It reduces direct UI coupling to core backend module paths.
- It preserves existing backend behavior by forwarding calls unchanged.
- It supports incremental modernization without touching frozen processing internals.

## Exactly what was added

New file: `import_service.py` with:

- `import_case_by_id(case_id, log_callback=print)`
  - thin pass-through to `process_case_from_id`
- `validate_case_id(case_id)`
  - conservative non-empty check only (intentionally permissive)
- `build_case_id(year, case_number)`
  - mirrors current UI assembly logic (`f"{year}-{case_number.strip()}"`)
- `get_app_info()`
  - small placeholder metadata dict for future UI usage

## Relationship to current UI (documented, no broad refactor)

Current Tk UI (`import_gui.pyw`) currently:
- builds case id in `start_import()` as `f"{year}-{case_number.strip()}"`,
- directly calls backend via imported `process_case_from_id`.

`import_service.build_case_id()` intentionally mirrors that current construction behavior.
No broad UI rewiring was done in this step.

## Safety confirmation

- No XML generation logic changed.
- No case processing logic changed.
- No template selection logic changed.
- No scan naming/routing/output naming/placeholder substitution/ID generation changed.
- No backend internals were refactored.

## Limitations / unknowns

- `validate_case_id()` is intentionally permissive to avoid introducing new rejection behavior.
- UI is not yet switched to this service wrapper (by design in this conservative step).
- App version metadata in `get_app_info()` is placeholder until formal versioning is introduced.

