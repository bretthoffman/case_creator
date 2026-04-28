# CASE CREATOR FIRST-RUN RULES SEED FIX REPORT

## 1. Summary of changes

This pass fixes first-run frozen/packaged unified-rules seeding by hardening bundled-seed path resolution while preserving the existing external app-data root behavior.

The loader now still targets:
- `%LOCALAPPDATA%\\CaseCreator\\business_rules\\v1\\case_creator_rules.yaml`

and now resolves the bundled seed more robustly across frozen layouts (including one-folder layouts where bundled data may be adjacent to the executable rather than only under `_MEIPASS`).

Seeding behavior remains conservative:
- create `business_rules\\v1` when missing,
- seed `case_creator_rules.yaml` only when missing,
- never overwrite an existing external rules file,
- never touch `local_settings.json` or `admin_settings.json`.

## 2. Files modified

- `infrastructure/config/business_rule_loader.py`
- `tests/test_business_rule_loader_dual_read.py`
- `CASE_CREATOR_FIRST_RUN_RULES_SEED_FIX_REPORT.md` (this report)

## 3. Root cause

The frozen seeding flow depended on `_resolve_bundled_seed_path()` returning a single `_MEIPASS`-based path when `_MEIPASS` existed. On some packaged layouts, the bundled seed may not live at that exact `_MEIPASS` location, causing seed discovery failure and therefore preventing first-run creation of the external unified rules file.

The app-data target itself (`%LOCALAPPDATA%\\CaseCreator\\business_rules\\v1`) was already correct; the brittle bundled-seed lookup was the main failure point.

## 4. Fix applied

### Loader change

In `infrastructure/config/business_rule_loader.py`, `_resolve_bundled_seed_path()` now checks candidate locations in order:
1. `_MEIPASS/business_rules_seed/v1/case_creator_rules.yaml` (if `_MEIPASS` exists),
2. `<directory of sys.executable>/business_rules_seed/v1/case_creator_rules.yaml`,
3. repo project-root fallback (source/dev).

It returns the first existing file; if none exist, it returns the first candidate for diagnostics.

No business-rule schema/semantics changed.

### Existing conservative seeding behavior retained

Frozen mode still:
- reuses `%LOCALAPPDATA%\\CaseCreator` root,
- creates only needed directories (`business_rules\\v1`),
- seeds only when unified file is missing,
- does not overwrite existing unified file,
- does not touch existing settings JSON files.

## 5. Validation performed

Executed:
- `python3 -m unittest tests.test_business_rule_loader_dual_read -v`

Result: **all tests passed**.

Validation coverage includes:
- frozen runtime path targets `%LOCALAPPDATA%\\CaseCreator\\business_rules\\v1\\case_creator_rules.yaml`,
- first-run seeds when external unified file is missing,
- existing external `case_creator_rules.yaml` is not overwritten,
- existing `%LOCALAPPDATA%\\CaseCreator` root is reused,
- existing `local_settings.json` remains unchanged,
- existing `admin_settings.json` remains unchanged,
- source/dev override path behavior remains unchanged,
- bundled-seed fallback resolves from executable-adjacent location when `_MEIPASS` path is missing.

## 6. Remaining risks or limitations

- This pass does not add new UI-specific logic; it ensures loader seeding is reliable when the loader is invoked.
- If future packaging changes move bundled data to a new, non-standard location, `_resolve_bundled_seed_path()` may need an additional candidate.

## 7. Recommended next step

Retest on the target Windows packaged machine:
1. Keep existing `%LOCALAPPDATA%\\CaseCreator\\local_settings.json` and `admin_settings.json` in place.
2. Remove only `%LOCALAPPDATA%\\CaseCreator\\business_rules\\v1\\case_creator_rules.yaml`.
3. Launch packaged app and confirm the unified rules file is auto-seeded.
4. Confirm both settings files remain byte-for-byte unchanged.
