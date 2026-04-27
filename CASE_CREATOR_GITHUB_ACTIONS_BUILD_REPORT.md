# CASE CREATOR GITHUB ACTIONS BUILD REPORT

## 1. Summary of changes

A **Windows-only GitHub Actions workflow** was added to build the existing **PyInstaller one-folder** Case Creator package on `windows-latest`, using the same **`scripts/windows/build_pyside6_onefolder.bat`** path as local developers. After a successful build, the workflow **zips `dist/CaseCreator/`** (the full one-folder output) and uploads that zip as a **workflow artifact** named **`CaseCreator-win64`**.

This pass is **CI packaging only**: no in-app update UI, no updater executable, no GitHub Release upload, and no version-check logic in the app.

## 2. Files modified

| Action | Path |
|--------|------|
| Created | `.github/workflows/build-windows.yml` |
| Modified | `scripts/windows/build_pyside6_onefolder.bat` (when `GITHUB_ACTIONS` is set, use `python -m PyInstaller` instead of the `py` launcher so CI uses the same interpreter as `setup-python` / `pip install`) |
| Created | `CASE_CREATOR_GITHUB_ACTIONS_BUILD_REPORT.md` (this file) |

## 3. Workflow behavior

**Triggers**

- **`workflow_dispatch`** — manual runs from the Actions tab (recommended for first verification).
- **`push` of tags** matching **`v*`** — conservative release-tag pattern only (e.g. `v1.2.3`).

**Steps (high level)**

1. Checkout repository.
2. **Python 3.11** via `actions/setup-python` with pip cache.
3. `pip install -r requirements.txt`, then **`pip install PySide6 pyinstaller`** (packaging deps are not in `requirements.txt`, matching `docs/packaging/PYINSTALLER_BUILD_PLAN.md`).
4. Run **`scripts\windows\build_pyside6_onefolder.bat`** via `cmd` so behavior matches documented Windows builds (including **canonical → seed copy** before PyInstaller).
5. **Validate** `dist\CaseCreator\CaseCreator.exe` and a bundled **`business_rules_seed/v1/case_creator_rules.yaml`** under `dist\CaseCreator` (recursive search so layout works whether PyInstaller places data next to the exe or under `_internal`).
6. **Zip** the `dist\CaseCreator` folder:
   - Tag builds: `CaseCreator-<tag>-win64.zip` (e.g. `CaseCreator-v1.2.3-win64.zip`).
   - Other runs: `CaseCreator-win64.zip`.
7. **Upload** the zip with `actions/upload-artifact@v4` (artifact name **`CaseCreator-win64`**).

**Concurrency:** `cancel-in-progress` for the same workflow + ref to avoid duplicate long builds.

## 4. Build output

**Workflow artifact**

- **Name:** `CaseCreator-win64`
- **Content:** One zip file:
  - **Tag push:** `CaseCreator-vX.Y.Z-win64.zip`
  - **`workflow_dispatch`:** `CaseCreator-win64.zip`

**Zip layout**

- The archive contains a **single top-level folder `CaseCreator/`** (because `Compress-Archive` is given `dist\CaseCreator`). Inside it: **`CaseCreator.exe`**, PyInstaller runtime files, and bundled data (including templates, Excel list, and seed YAML) per the batch script — the same **“copy the whole folder”** layout described for manual installs in packaging docs.

## 5. Seed/config packaging alignment

The workflow does **not** duplicate PyInstaller flags in YAML. It relies on **`build_pyside6_onefolder.bat`**, which:

On **GitHub Actions**, the batch file skips the Windows **`py` launcher** and runs **`python -m PyInstaller`** so the build uses the same Python that installed dependencies in earlier workflow steps (avoiding a mismatch if `py` targeted a different runtime).

The batch file also:

1. Asserts **`business_rules/v1/case_creator_rules.yaml`** exists.
2. Copies it to **`business_rules_seed/v1/case_creator_rules.yaml`** before invoking PyInstaller.
3. Passes **`--add-data "business_rules_seed\v1\case_creator_rules.yaml;business_rules_seed\v1"`** so the frozen app includes the **packaged unified seed** consistent with the current packaged config design.

The validation step confirms that **`case_creator_rules.yaml`** appears under a **`business_rules_seed\v1\`** path inside **`dist\CaseCreator`**.

## 6. Validation performed

| Check | Result |
|-------|--------|
| Workflow YAML structure (steps, triggers, artifact upload) | Parsed successfully with PyYAML locally |
| Reuse of existing Windows build entrypoint | Uses `scripts/windows/build_pyside6_onefolder.bat` |
| Post-build checks | `CaseCreator.exe` + bundled seed path |
| Zip + `upload-artifact` | Zip created from `dist\CaseCreator`; upload uses `if-no-files-found: error` |

**Not run in this environment:** an actual GitHub-hosted Windows job (requires pushing to GitHub and running the workflow). After merge, run **`workflow_dispatch`** once to confirm end-to-end pip install, PyInstaller, and artifact download.

## 7. Risks or limitations

- **First CI run may fail** if `requirements.txt` (heavy scientific stack) is slow or hits a Windows wheel edge case; timeout is set to 60 minutes.
- **Repository must contain** `List of Signature Dr.xlsx`, `case_creator_icon.ico`, `templates/`, and canonical rules YAML — same as local batch prerequisites; if these are missing in a clone, the batch step fails by design.
- **No Release publishing** — artifact retention follows GitHub’s artifact policy; not a substitute for `CASE_CREATOR_GITHUB_UPDATE_SYSTEM_PLAN.md` Release-based distribution.
- **No code signing** — SmartScreen may warn on first run of CI-built exe.

## 8. Recommended next pass

**Safest next step:** after one successful **`workflow_dispatch`** run, add **automated GitHub Release creation** (or `softprops/action-gh-release`) for **`v*`** tags only, attaching the same zip + optional `SHA256SUMS`, using a tightly scoped token — still **without** implementing the external updater or in-app update button until Release assets are stable.

---

## Final chat summary

1. **Yes** — once this workflow is pushed and run on GitHub, **Actions can build the Windows package** using the same batch script as local packaging.
2. **Yes** — the workflow **uploads a packaged zip** as workflow artifact **`CaseCreator-win64`**.
3. **Yes** — the batch step **refreshes and bundles** `business_rules_seed/v1/case_creator_rules.yaml`, and the workflow **validates** that path under `dist\CaseCreator`.
4. **Safest next pass:** prove the workflow with **`workflow_dispatch`**, then add **Release upload for `v*` tags** (checksum file optional), still **no** updater / auto-update code.
