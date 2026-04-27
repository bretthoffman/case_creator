# CASE CREATOR GITHUB ACTIONS NODE WARNING CLEANUP REPORT

## 1. Summary of changes

The Windows build workflow **`.github/workflows/build-windows.yml`** was updated only by **pinning newer major versions** of official GitHub actions whose older majors still ran on the **deprecated Node.js 20** action runtime:

| Action | Before | After |
|--------|--------|-------|
| Checkout | `actions/checkout@v4` | `actions/checkout@v5` |
| Setup Python | `actions/setup-python@v5` | `actions/setup-python@v6` |
| Upload artifact | `actions/upload-artifact@v4` | `actions/upload-artifact@v6` |

All **run steps** (install, pathlib guard, PyInstaller batch, validation, zip, artifact path) are **unchanged in intent and order**. No application code, packaging scripts, or business rules were modified.

**Why not a workflow `env` opt-in?** The practical fix for “this action runs on Node 20” is to use **action releases that declare `node24`**, which these majors do. Relying on undocumented global env knobs would be less explicit and harder to maintain.

## 2. Files modified

| Path | Change |
|------|--------|
| `.github/workflows/build-windows.yml` | Bumped `checkout`, `setup-python`, and `upload-artifact` major versions as above |
| `CASE_CREATOR_GITHUB_ACTIONS_NODE_WARNING_CLEANUP_REPORT.md` | This report (created) |

## 3. Root cause

GitHub is deprecating the **Node 20** runtime used by **composite/JavaScript actions**. Older **major tags** of `actions/checkout`, `actions/setup-python`, and `actions/upload-artifact` were still associated with that runtime, which surfaces as **Annotations** / summary warnings even when the job succeeds.

## 4. Fix applied

**Narrow version bumps** to current majors that upstream documents as running on **Node 24** (and requiring **Actions Runner `2.327.1` or newer** on self-hosted runners). `github.com` hosted `windows-latest` meets that requirement.

No speculative rewrites: same `with:` blocks (`python-version`, `cache`, artifact `name` / `path` / `if-no-files-found`).

## 5. Validation performed

| Check | Result |
|-------|--------|
| Workflow YAML syntax | Parsed successfully with PyYAML locally |
| Build pipeline intent | Install → pathlib steps → `build_pyside6_onefolder.bat` → validate → zip → upload unchanged |
| Scope | Only the three `uses:` lines under the Node-related actions |

**Not run:** A live GitHub Actions job in this environment.

## 6. Remaining risks or limitations

- **Self-hosted runners** older than **2.327.1** could fail after these bumps; **GitHub-hosted** runners are fine.
- **Future** deprecation notices may appear again when GitHub raises the floor; re-bump majors when release notes recommend it.
- **`upload-artifact@v6`** may include behavior changes vs v4 for advanced scenarios; this workflow only uploads a **single zip path** with the same inputs as before, which remains the common path.

## 7. Recommended next step

Push and run **Build Windows package** (`workflow_dispatch` or a `v*` tag). Confirm the job is green and check the run summary **Annotations** for any remaining Node 20 warnings (there should be none for these three actions).

---

## Final chat summary

1. **Change:** Bumped **`actions/checkout`** to **`@v5`**, **`actions/setup-python`** to **`@v6`**, and **`actions/upload-artifact`** to **`@v6`** so those steps use maintained action releases aligned with **Node 24**, addressing the deprecation warning without workflow rewrites.
2. **Build behavior:** **Same** — triggers, Python version, install commands, pathlib uninstall/verify, batch build, zip layout, and artifact name/path are unchanged.
3. **Rerun:** **Yes** — run the workflow on GitHub once to confirm warnings are gone and the artifact still uploads.
4. **Watch:** Other ecosystem actions could warn later; **self-hosted** Windows agents must stay on a **current runner** version. Optional: periodically re-check release notes for `checkout` / `setup-python` / `upload-artifact` when GitHub announces the next runtime bump.
