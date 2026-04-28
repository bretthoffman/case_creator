# CASE CREATOR CHECK FOR UPDATE REPORT

## 1. Summary of changes

Implemented a **user-triggered, check-only** update UX pass:

- Added a **Check for Update** button to the main UI.
- Clicking it opens a small update dialog.
- Dialog checks GitHub Releases **only when clicked**.
- Dialog reports one of:
  - up to date,
  - update available,
  - check failed.

No download/install/update replacement logic was added.

## 2. Files modified

- `pyside6_ui.py`
- `update_check.py` (new)
- `import_service.py`
- `tests/test_update_check.py` (new)
- `CASE_CREATOR_CHECK_FOR_UPDATE_REPORT.md` (this report)

## 3. UI behavior

### Main window

Added button in the existing right-side control stack:
- **Check for Update**

### Dialog behavior

Clicking opens `UpdateCheckDialog` with initial state:
- `Checking for updates...`

Then updates status text to:
- `You're up to date.`
- `Update available: vX.Y.Z` + `Update installation not yet implemented.`
- `Could not check for updates.`

The check runs on a worker thread so UI remains responsive.

## 4. Version source

Audited existing source:
- existing UI version display came from `import_service.get_app_info()`.

Conservative improvement:
- `get_app_info()` now resolves `app_version` in this order:
  1. `CASE_CREATOR_APP_VERSION` env var if set,
  2. `app_version.txt` under frozen `_MEIPASS` if present,
  3. `app_version.txt` next to `import_service.py` if present,
  4. fallback `0.0.0`.

This preserves current behavior while allowing stable version injection without introducing a broad new version system.

## 5. GitHub release check behavior

Implemented in `update_check.py`:

- Uses GitHub API endpoint (no HTML scraping):
  - `https://api.github.com/repos/<repo>/releases/latest`
- Default repo: `bretthoffman/case_creator`
- Repo can be overridden via `CASE_CREATOR_GITHUB_REPO`.
- Uses timeout and safe exception handling (`HTTPError`, `URLError`, generic exceptions).

Version comparison strategy (bounded/documented):
- Supports current tag style like `v0.0.2-test`.
- Parses bounded `vMAJOR.MINOR.PATCH[-suffix]` format.
- Compares major/minor/patch numerically.
- Same numeric version: stable latest is newer than prerelease-like current.
- Fallback for unparsable tags: normalized string mismatch => update available.

No updater/download/swap behavior is present.

## 6. Validation performed

### Automated tests

Ran:
- `python3 -m unittest tests.test_update_check tests.test_open_rules_folder_path -v`

Result:
- **6 tests passed**.

Covered:
- update available / up-to-date / failure result handling,
- prerelease + `v`-prefix version compare behavior,
- existing rules-folder tests unaffected.

### Static checks

- Linter diagnostics on modified files: **no issues**.

## 7. Risks or limitations

- Default GitHub repo is hardcoded and should match the actual release repo; override is available via env var.
- Bounded comparator is intentionally conservative (not full semver ecosystem behavior).
- This pass does not provide release notes/details UI or clickable release link.

## 8. Recommended next step

Safest next pass:
1. Add explicit release metadata display in the dialog (latest tag + link),
2. Introduce a small app-version file generated during build/release for guaranteed packaged-version correctness,
3. Keep install/update execution out of scope until updater process pass.
