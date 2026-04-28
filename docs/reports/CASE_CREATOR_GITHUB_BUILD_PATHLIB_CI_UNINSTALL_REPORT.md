# CASE CREATOR GITHUB BUILD PATHLIB CI UNINSTALL REPORT

## 1. Summary of changes

The **Build Windows package** workflow (`.github/workflows/build-windows.yml`) now runs **`python -m pip uninstall -y pathlib`** immediately after installing dependencies and **before** the PyInstaller batch step. A follow-up step runs **`python -m pip show pathlib`** and **fails the job** if that distribution is still installed (exit code 0), so PyInstaller never starts while the obsolete backport remains.

**`requirements.txt`** was inspected: it **does not** currently list `pathlib`; the CI guard still helps if a dependency reintroduces it or the file regresses.

## 2. Files modified

| Path | Change |
|------|--------|
| `.github/workflows/build-windows.yml` | Added **Uninstall obsolete pip pathlib backport** and **Verify pip pathlib package is absent** steps between install and package |
| `CASE_CREATOR_GITHUB_BUILD_PATHLIB_CI_UNINSTALL_REPORT.md` | This report (created) |

## 3. Root cause

PyInstaller errors when the **PyPI `pathlib` package** (obsolete stdlib backport) is present in the environment. That can happen if it is pinned in **`requirements.txt`**, pulled **transitively**, or left over from a **cached / older** install path. The failure message is explicit: the backport is **incompatible with PyInstaller**.

## 4. Fix applied

**Primary fix (as requested):** in CI, **unconditionally** run **`python -m pip uninstall -y pathlib`** after `pip install -r requirements.txt` and `pip install PySide6 pyinstaller`, then **verify** with **`pip show pathlib`** — the workflow must **not** see that package (non-zero exit from `pip show` when absent).

**Note:** `pip uninstall` when the package is already absent completes with a skip warning; that is acceptable.

No application code, schemas, rules, or updater logic was changed.

## 5. Validation performed

| Check | Result |
|-------|--------|
| **`requirements.txt`** | No `pathlib` line present (grep) |
| **Workflow YAML** | Uninstall + verify steps inserted in the correct order (after install, before `build_pyside6_onefolder.bat`) |
| **Verify step logic** | If `pip show pathlib` succeeds (`$LASTEXITCODE -eq 0`), the step throws and fails the job |

**Not run here:** a full GitHub-hosted Windows job; re-run the workflow on the repo to confirm end-to-end.

## 6. Remaining risks or limitations

- If a future dependency **re-installs `pathlib` in a post-install hook** after the verify step (unlikely), the guard would not catch it unless ordering changes; current workflow has no such step between verify and PyInstaller.
- **`pip uninstall pathlib`** only affects the **active** `python` on `PATH` (same as `setup-python`), which matches the PyInstaller step.

## 7. Recommended next step

Push the workflow change and **re-run “Build Windows package”** (`workflow_dispatch` or a `v*` tag). Confirm PyInstaller completes and the artifact uploads.

---

## Final chat summary

1. **Yes** — the workflow now runs **`python -m pip uninstall -y pathlib`** after dependency installation and before packaging.
2. **Yes** — the next step runs **`python -m pip show pathlib`** and **fails** if the package is still present (`LASTEXITCODE -eq 0`).
3. **Yes** — **re-run** the Actions workflow after pushing to confirm on `windows-latest`.
4. **Yes** — any **Node** deprecation warnings from GitHub-hosted actions remain **unrelated** to this Python/PyInstaller/`pathlib` issue.
