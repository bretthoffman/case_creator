# PyInstaller Build Plan (First Windows One-Folder Build)

## Build Goal

Create the first conservative packaged build of the **PySide6 app only** for Windows using PyInstaller in **one-folder** mode.

## Canonical Entrypoint

- Package entrypoint: `pyside6_ui.py`

## Build Mode Choice

- Use: `--onedir` (one-folder)
- Do **not** use one-file for first build

Why one-folder first:
- Easier to verify bundled assets (`templates/`, Excel file).
- Simpler debugging for missing-file/runtime path issues.
- Better fit with current conservative rollout and smoke-testing phase.

## Required Data Assets To Include

Must include in bundled app:
- `templates/` (entire folder/subtree)
- `List of Signature Dr.xlsx`
- `business_rules_seed/v1/case_creator_rules.yaml` — **packaged default** unified rules seed (first-run copy to `%LOCALAPPDATA%`). It must stay identical to the canonical repo file `business_rules/v1/case_creator_rules.yaml`. The Windows build script copies canonical → seed before PyInstaller; developers can run `python3 scripts/sync_unified_config_seed.py` after editing the canonical file.

Windows `--add-data` syntax should use semicolon separator:
- `--add-data "templates;templates"`
- `--add-data "List of Signature Dr.xlsx;."`
- `--add-data "business_rules_seed\\v1\\case_creator_rules.yaml;business_rules_seed\\v1"`

## Hidden Imports / Runtime Import Notes

Likely needed explicitly:
- `openpyxl` (used by `pandas.read_excel(..., engine="openpyxl")`)

PyInstaller usually handles PySide6 and pandas via hooks, but first build should watch for runtime import errors and add hidden imports only as needed.

## Windowed/App Options

Recommended first build flags:
- `--windowed` (GUI app, no console)
- `--icon "case_creator_icon.ico"` (if file exists and is desired)
- `--name "CaseCreator"` (or preferred dist name)

## Recommended Output Naming

Suggested app name:
- `CaseCreator`

Expected outputs:
- `dist/CaseCreator/` (packaged app folder)
- `build/CaseCreator/` (build artifacts)
- `CaseCreator.spec` (spec file)

## Environment / Dependency Notes Before Build

Run build on target-like Windows environment where app already works.

Minimum key dependencies to verify in environment:
- `PyInstaller`
- `PySide6`
- `pandas`
- `openpyxl`
- `requests`

Note:
- Do not rely on source `.bat` launchers in packaged deployment; packaged shortcut should target `dist/CaseCreator/CaseCreator.exe`.

## Settings Behavior in Packaged Build

With current hardening:
- In frozen Windows mode, settings files should use:
  - `%LOCALAPPDATA%\CaseCreator\local_settings.json`
  - `%LOCALAPPDATA%\CaseCreator\admin_settings.json`
- Missing settings files are safe and should be created on first save.

## First Packaged Smoke-Test Checklist

1. Launch `CaseCreator.exe`.
2. Confirm app opens without preexisting local/admin settings files.
3. Open Normal Settings, save, confirm `%LOCALAPPDATA%\CaseCreator\local_settings.json` creation.
4. Open Advanced Settings (admin), save, confirm `%LOCALAPPDATA%\CaseCreator\admin_settings.json` creation.
5. Verify import queue behavior and timeout warning behavior.
6. Run at least one real import and verify expected output structure/content in destination.
7. Confirm template selection and support file copy behavior (no regressions).
8. Confirm close-while-busy guard works.

## Known Likely Build/Runtime Issues To Watch

- Missing bundled assets:
  - `templates/` not included or wrong destination path.
  - `List of Signature Dr.xlsx` missing.
- Runtime import errors:
  - `openpyxl` not present in build.
- Windows permission constraints:
  - inability to write settings (should be `%LOCALAPPDATA%`, but verify).
- Network path access differences when running packaged EXE under user context.

