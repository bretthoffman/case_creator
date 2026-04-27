# Packaged Path Audit

Conservative audit of file/path usage relevant to packaged (PyInstaller) deployment.

Scope:
- Path behavior only.
- No backend refactor/change.
- Focus on packaged/frozen runtime risks.

## Canonical packaged app path context

- Primary UI entrypoint: `pyside6_ui.py`.
- Core runtime path config is centralized in `config.py`.

---

## Safe As-Is For Packaging

These path usages are generally safe if configured base paths are valid.

## 1) Join-on-config-path usage (core engine)

- `template_utils.py`
  - `select_template()` builds template path from `TEMPLATE_DIR` + template folder/file (line 180).
- `case_processor_final_clean.py`
  - output and scan/file paths are built from discovered/runtime roots via `os.path.join(...)` in many places.
  - representative writes/reads:
    - final output folder/XML creation (lines 552-557),
    - template read/write path usage (lines 819, 895),
    - output support files copy (`Materials.xml`, `Manufacturers.3ml`) (lines 573-585),
    - failed-import marker writes (lines 686-689).

Why safe:
- `os.path.join(...)` itself is fine; behavior depends on base path values from config/settings.

## 2) Project-relative default asset bases in config

- `config.py`
  - `_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))` (line 8)
  - `_DEFAULT_SIGNATURE_DOCTORS_PATH = <project>/List of Signature Dr.xlsx` (line 9)
  - `_DEFAULT_TEMPLATE_DIR = <project>/templates` (line 10)

Why mostly safe:
- Uses script-directory-relative defaults, which are packaging-friendly in one-folder deployment when data files are included.

## 3) Optional folder creation guarded by non-empty root

- `config.py` lines 34-42
  - derived output paths only created when `CC_IMPORTED_ROOT` is set.

Why safe:
- avoids creating invalid directories from empty roots.

---

## Needs Packaged-Path Adjustment

These are likely to need explicit packaging/runtime strategy (not broad code refactor).

## 1) Settings file write location (`__file__` directory)

- `local_settings.py`
  - settings file path: `os.path.join(dirname(abspath(__file__)), "local_settings.json")` (line 9)
  - save writes temp + replace in same directory (lines 50-55).
- `admin_settings.py`
  - settings file path: same pattern for `admin_settings.json` (line 9)
  - save writes temp + replace in same directory (lines 64-69).

Packaging risk:
- If packaged into protected install location (e.g., `Program Files`), writes can fail.
- In one-file mode, `__file__`-relative behavior can be undesirable/transient.

Conservative adjustment direction:
- choose and document a stable writable user path for settings in packaged builds (e.g., `%APPDATA%/...`) before release build.

## 2) Source launchers hardcode dev project path

- `launch_importer.bat` / `launch_importer_tk_fallback.bat`
  - `PROJECT_DIR=C:\Users\brett\Documents\3shape_case_importer` (line 5/4 respectively)
  - `pushd` to source tree.

Packaging impact:
- packaged shortcuts should target packaged executable, not these source-tree launchers.

---

## Needs PyInstaller Data-File Inclusion

These are runtime-read assets that must be bundled/included.

## 1) Templates directory

- Runtime depends on `TEMPLATE_DIR` (config line 17 defaulting to `<project>/templates`).
- `template_utils.select_template()` resolves exact template XML files from this tree (line 180).
- `case_processor_final_clean.generate_final_xml()` reads selected template XML (line 819).
- `case_processor_final_clean` copies per-template support files:
  - `Materials.xml`
  - `Manufacturers.3ml`
  (lines 573-585).

Required inclusion:
- entire `templates/` subtree (all template folders + files), not partial subsets.

## 2) Signature doctor Excel file

- `template_utils.is_signature_doctor()` reads `SIGNATURE_DOCTORS_PATH` via `pandas.read_excel(..., engine="openpyxl")` (line 17).
- Default in config points to `<project>/List of Signature Dr.xlsx` (line 9).

Required inclusion:
- `List of Signature Dr.xlsx`
- ensure `openpyxl` availability in packaged environment.

---

## Needs Human Decision

These are path/data decisions, not automatic code rewrites.

## 1) One-folder vs one-file packaging mode

- Given current `__file__`-relative settings paths and runtime data files, one-folder is safer for first build.
- one-file may require extra handling for writable settings location and data extraction behavior.

## 2) External dependency paths and defaults

- `config.py` defaults currently include empty strings for key machine paths:
  - `EVIDENT_PATH` (line 13)
  - `TRIOS_SCAN_ROOT` (line 15)
  - `CC_IMPORTED_ROOT` (line 32)
  - EVO credentials/base can also be empty (lines 21-23, 28-29).

Decision required:
- whether packaged app ships with preconfigured defaults, relies on first-run settings entry, or both.

## 3) Template-internal absolute references

- Multiple `templates/*/Materials.xml` files contain absolute `O:\...` path values (`AdditiveModelPath` / `VisibleModelPath`).

Decision required:
- confirm whether these are required by downstream 3Shape workflows in target environments.
- if they are environment-specific, decide whether to keep as-is, standardize externally, or document prerequisite mapping.

## 4) Settings file resilience in locked environments

- Current settings save is robust for missing/malformed files, but not for unwritable install directories.

Decision required:
- final packaged writable location policy for `local_settings.json` and `admin_settings.json`.

---

## Notes on CWD Dependence

- Core runtime mostly uses configured paths and `__file__`-relative defaults.
- Limited CWD-dependent behavior appears in auxiliary scripts (e.g., `rx_fetch_and_parse.py` writes `rx_downloads` relative to CWD, line 45), but these are not primary app runtime.

---

## Minimal Packaging-Facing Checklist (Path Focus)

1. Include `templates/` as data files.
2. Include `List of Signature Dr.xlsx` as data file.
3. Verify packaged runtime can read those assets from configured defaults.
4. Define writable location strategy for `local_settings.json` and `admin_settings.json`.
5. Verify first-run with missing settings files still launches and allows save.
6. Verify configured network/mapped path roots resolve on production machines.
7. Use packaged executable shortcut (not source `.bat`) in deployment.
