# CASE CREATOR PACKAGED VERSION INJECTION REPORT

## 1. Summary of changes

Packaged Windows builds now **bundle `app_version.txt`** into the PyInstaller one-folder output via **`--add-data "app_version.txt;."`**, so `get_app_info()` finds it under **`_MEIPASS`** at runtime (same as other data files in `_internal`).

**GitHub Actions** writes **`app_version.txt`** immediately before `build_pyside6_onefolder.bat`: for **`refs/tags/...`**, the tag text is normalized to **drop a single leading `v`/`V`** (e.g. `v0.0.3-base` → file contains `0.0.3-base`) so the UI’s existing **`v{app_version}`** formatting does not produce `vv…`. Non-tag runs (including **`workflow_dispatch`**) use **`0.0.0-ci`**.

The repo includes a tracked **`app_version.txt`** with **`0.0.0-dev`** for local/dev; the batch script still creates **`0.0.0-dev`** if the file is missing before packaging. CI validation asserts **`dist\CaseCreator\_internal\app_version.txt`** exists after the build.

## 2. Files modified

| File | Change |
|------|--------|
| `app_version.txt` | New tracked default `0.0.0-dev` (+ newline). |
| `scripts/windows/build_pyside6_onefolder.bat` | Ensure `app_version.txt` exists; add `--add-data "app_version.txt;."` to both PyInstaller branches. |
| `.github/workflows/build-windows.yml` | Step **Write app_version.txt for packaged build**; validate step checks `_internal\app_version.txt`. |
| `import_service.py` | Docstring documents resolution order and file format (no leading `v`; CI/dev tokens). |
| `tests/test_import_service_version.py` | Tests for env override, repo `app_version.txt`, and `_MEIPASS` path. |
| `docs/reports/CASE_CREATOR_PACKAGED_VERSION_INJECTION_REPORT.md` | This report. |

## 3. Root cause

`get_app_info()` already supported **`app_version.txt`** under **`_MEIPASS`**, but the **PyInstaller spec never bundled that file**, so frozen installs always fell through to **`0.0.0`**. CI did not generate a version file before packaging.

## 4. Version injection/build changes

- **Tagged release:** `GITHUB_REF=refs/tags/v0.0.3-base` → file `0.0.3-base` (UI shows `v0.0.3-base`).
- **Non-tag CI:** `0.0.0-ci`.
- **Local packaging:** default `0.0.0-dev` from repo file or batch-generated file.
- **Override:** `CASE_CREATOR_APP_VERSION` still wins at runtime.

## 5. Runtime version-reading behavior

Unchanged order: **env → `_MEIPASS/app_version.txt` → `import_service.py` directory → `0.0.0`**. After this pass, the **bundled** path is populated for release zips, so post-updater relaunch reads the **injected** version.

## 6. Validation performed

- `python3 -m unittest tests.test_import_service_version -v`
- **Windows CI** should confirm the new validate step prints the embedded version.

## 7. Remaining risks or limitations

- Tags **without** a leading `v` are written to the file **as-is**; UI still prefixes **`v`** (e.g. tag `0.0.3` → display `v0.0.3`).
- Very old manual zips built before this change still report **`0.0.0`** until replaced.

## 8. Recommended next step

Cut or rebuild a **tagged** release, install/update, and confirm **Check for Update** shows **`Current version: v…`** matching the tag (minus duplicate `v`).

---

## Final chat summary

1. **Tagged packaged builds carry the real release version:** Yes — **`app_version.txt`** is written from the Git tag and bundled into **`_internal`**.  
2. **App shows correct installed version instead of `v0.0.0`:** Yes — for builds produced after this change, assuming the bundled file is present.  
3. **Updater-installed builds after relaunch:** Yes — the installed folder includes the same bundled **`app_version.txt`** as the release zip.  
4. **Safest next step:** Run one **tagged** Windows workflow, confirm validate output and UI version on a real machine.
