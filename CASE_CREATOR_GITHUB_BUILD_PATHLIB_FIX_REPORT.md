# CASE CREATOR GITHUB BUILD PATHLIB FIX REPORT

## 1. Summary of changes

The **`pathlib==1.0.1`** line was **removed** from **`requirements.txt`**. That PyPI package is an obsolete backport of the Python 3.4+ standard library module **`pathlib`**; on **Python 3.11** (used by the Windows GitHub Actions workflow) it should not be installed. Its presence caused **PyInstaller** to fail with an explicit incompatibility error during the one-folder packaging step.

No workflow, batch script, or application logic was changed.

## 2. Files modified

| Path | Change |
|------|--------|
| `requirements.txt` | Removed `pathlib==1.0.1` |
| `CASE_CREATOR_GITHUB_BUILD_PATHLIB_FIX_REPORT.md` | This report (created) |

## 3. Root cause

**`pip install -r requirements.txt`** in **`.github/workflows/build-windows.yml`** pulled in the **`pathlib`** distribution from PyPI. That package shadows and replaces the intent of the stdlib module and is **explicitly rejected by PyInstaller** with:

`The 'pathlib' package is an obsolete backport of a standard library package and is incompatible with PyInstaller.`

The CI image uses **Python 3.11**, which already includes **`pathlib`** in the standard library, so the backport is unnecessary and harmful for frozen builds.

## 4. Fix applied

**Preferred clean fix:** delete **`pathlib==1.0.1`** from **`requirements.txt`** so CI and local installs on Python 3.x use **stdlib `pathlib` only**.

No bounded “keep for older Python” branch was added: the Windows packaging workflow is pinned to 3.11, and removing the backport aligns installs with modern Python.

## 5. Validation performed

| Check | Result |
|-------|--------|
| **`requirements.txt`** | No longer lists `pathlib` |
| **Other install inputs** | `.github/workflows/build-windows.yml` only adds `PySide6` and `pyinstaller` after `requirements.txt`; no separate `pathlib` install |
| **Code imports** | Repository uses `from pathlib import Path` (and similar) against the **standard library**; nothing imports the PyPI backport by name |
| **Local sanity** | Removing the line does not alter business-rule or loader code paths |

**Operational validation:** Re-run the **“Build Windows package”** workflow on GitHub (`workflow_dispatch` or a `v*` tag push) to confirm PyInstaller completes end-to-end. That run was not executed in this environment (no hosted Windows runner here).

## 6. Remaining risks or limitations

- **Very old Python 2.x or early 3.x** environments that somehow relied on the PyPI `pathlib` backport are out of scope; this project’s documented CI and packaging path is **Python 3.11+**.
- **`requirements.txt`** still contains other packages that mirror stdlib names (e.g. **`uuid==1.30`**). That was not part of this failure; if PyInstaller or another tool flags it later, treat it as a separate audit.

## 7. Recommended next step

Push the change and **re-run** the Windows build workflow. If the job succeeds, keep the artifact smoke check (exe + bundled seed) as-is. If a new error appears, triage from the new log line rather than re-adding `pathlib`.

---

## Final chat summary

1. **Yes** — the pip package **`pathlib`** was the real blocker: it triggered PyInstaller’s explicit “obsolete backport / incompatible” error during the packaging step.
2. **`requirements.txt`** was changed (line removed); **`CASE_CREATOR_GITHUB_BUILD_PATHLIB_FIX_REPORT.md`** was added.
3. **Yes** — **re-run** the GitHub Actions **Build Windows package** workflow after pushing to confirm the fix on `windows-latest`.
4. **Yes** — any **Node.js deprecation warning** from Actions (e.g. from `actions/checkout` or `actions/setup-python` internals) is **unrelated** to Python, `pathlib`, or PyInstaller; it does not explain this failure.
