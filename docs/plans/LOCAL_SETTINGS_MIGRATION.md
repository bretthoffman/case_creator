# Local Settings Migration (Machine Paths Only)

## What was externalized

The following **machine-specific path settings** are now eligible for override through `local_settings.json`:

- `EVIDENT_PATH`
- `EVOLUTION_DROP_PATH`
- `TRIOS_SCAN_ROOT`
- `SIGNATURE_DOCTORS_PATH`
- `TEMPLATE_DIR`
- `JOTFORM_PATH`
- `CC_IMPORTED_ROOT`

Implementation details:
- `config.py` still defines the same variable names used by the rest of the app.
- Each value now uses `get_setting("<KEY>", <existing_hardcoded_default>)`.
- Override is applied only when a non-empty value exists in `local_settings.json`.

## What was intentionally left hardcoded

These were not externalized in this change:

- `EV_INT_BASE`, `EVO_USER`, `EVO_PASS`, `EVO_TIMEOUT`, `EVO_VERIFY_SSL`
- `IMG_USER`, `IMG_PASS`
- `DEBUG_MODE`
- Derived paths:
  - `SEND_TO_AI_PATH`
  - `SEND_TO_ARGEN_PATH`
  - `SEND_TO_1_9_PATH`
  - `FAILED_IMPORT_PATH`

Reason:
- Goal was limited to machine-specific filesystem path drift only.
- Core runtime behavior and non-path configuration were intentionally not changed.

## Why this is safe

- No XML generation logic was modified.
- No case processing logic was modified.
- No template selection, scan naming, output naming, routing, substitution, or ID generation logic was modified.
- Existing defaults in `config.py` are preserved exactly.
- `local_settings.py` fails gracefully:
  - missing file -> defaults used,
  - malformed JSON -> defaults used,
  - non-object JSON -> defaults used.

## Behavior when `local_settings.json` is absent

Behavior remains unchanged from previous state:
- all path settings resolve to the same hardcoded defaults that existed before this migration.

## Risks / unknowns

- If a machine is launched from the nested duplicate tree instead of the root tree, that tree's `config.py` may not use this overlay yet.
- Incorrect values in `local_settings.json` can still route input/output to wrong folders (same class of risk as any path edit).
- A non-string JSON value for a path key is accepted by `get_setting`; this is intentional minimalism but could cause runtime issues if invalid types are provided.

