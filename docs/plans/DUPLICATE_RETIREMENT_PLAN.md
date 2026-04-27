# Duplicate Tree Retirement Plan (Conservative)

## Canonical Tree Confirmation

Recommended canonical tree:
- `/Users/bretthoffman/Documents/3shape_case_importer` (root tree)

Reason:
- Current launcher behavior points to this root path.
- Root is now where machine-specific local overlay support was added (`local_settings.py` + `local_settings.example.json` + updated `config.py`).
- Keeping one canonical tree reduces configuration drift risk without changing core processing behavior.

## Why the Nested Tree Should Be Retired

Nested legacy duplicate:
- `/Users/bretthoffman/Documents/3shape_case_importer/3shape_case_importer`

Why retire:
- It was historically used to absorb machine-specific path drift.
- Path drift is now being addressed through local settings overlays in the root tree.
- Keeping both trees increases the chance of accidental out-of-sync edits and unclear runtime source-of-truth.

Retirement should remain a **manual, reversible** process.

## Direct Reference Inspection Findings

A targeted scan was run for direct references to the nested path/imports.

Findings:
- No direct imports of nested package path found:
  - no `import 3shape_case_importer...`
  - no `from 3shape_case_importer...`
- No runtime code references to nested filesystem path were found.
- Launcher files (`launch_importer.bat`) set:
  - `PROJECT_DIR=C:\Users\brett\Documents\3shape_case_importer`
  - then run `import_gui.pyw` from that project root.

Important caveat:
- This does **not** prove external shortcuts/scheduled tasks on every machine are correct.
- Manual launches from nested paths are still possible if operators run them directly.

## What to Back Up First (Before Any Rename/Removal)

1. Full backup of root tree.
2. Full backup of nested tree.
3. Snapshot of current output folders (`cc imported cases` structure) if feasible.
4. Snapshot of machine launch targets:
   - desktop/start-menu shortcut targets,
   - scheduled tasks/services/scripts.
5. Copy of any machine-local `local_settings.json` used in production.

## Safe Soft-Retirement Steps (Manual)

1. Confirm machine uses root launcher target.
2. Confirm root `local_settings.json` is present/correct (if overrides are needed).
3. Run smoke import(s) from root launcher and verify outputs.
4. Create timestamped archive/backup of nested tree.
5. **Soft-retire by rename** (manual operation), not delete:
   - e.g. `3shape_case_importer` -> `3shape_case_importer__retired_candidate`
6. Re-run same smoke import set from root launcher.
7. Monitor for a stabilization window.
8. Only after stable window, consider final deletion of retired candidate backup copy.

## Verification Checklist (Before and After Rename)

Before rename:
- Root launcher opens app successfully.
- Import pipeline runs for representative case types.
- Output destinations and filenames match current expected behavior.
- No operator workflow is launching nested paths directly.

After rename:
- App still launches from root.
- Same representative imports succeed.
- Output XML/files/folders remain consistent with baseline expectations.
- No missing-module/path errors.

## Rollback Plan

If anything fails after soft-retirement rename:
1. Restore original nested folder name immediately.
2. Re-run root launcher and verify app is operational.
3. Re-check launch targets and any hardcoded external scripts/shortcuts.
4. Pause retirement and document exact failing machine/workflow.

Rollback is fast because no hard deletion occurs during soft-retirement.

## Explicit Non-Changes

This plan intentionally does **not**:
- change XML generation logic,
- change case processing/template selection/scan naming/routing/substitution/ID generation logic,
- rewrite imports,
- delete files automatically,
- perform broad cleanup refactors.

