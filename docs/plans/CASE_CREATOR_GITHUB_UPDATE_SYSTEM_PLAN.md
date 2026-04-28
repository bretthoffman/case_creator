# CASE CREATOR GITHUB UPDATE SYSTEM PLAN

## 1. Purpose

Case Creator is packaged for Windows (PyInstaller one-folder) and stores **persistent operator data** under `%LOCALAPPDATA%\CaseCreator\` (unified rules, local settings, admin settings). The maintainer works primarily on macOS and should not need a Windows machine for every release.

**GitHub Actions on `windows-latest` runners** plus **GitHub Releases** as the canonical distribution channel solves this by:

- Running the same packaging script (`scripts/windows/build_pyside6_onefolder.bat` or an equivalent CI-invoked PyInstaller command) on Microsoft-hosted Windows infrastructure.
- Publishing a **versioned, downloadable artifact** (zip of the `dist\CaseCreator\` folder or equivalent) that end users and an updater can fetch without building from source.
- Keeping **user data outside the install directory**, so replacing the installed app folder does not touch `%LOCALAPPDATA%\CaseCreator\`.

This matches common patterns for small desktop apps: CI builds, Releases host binaries, updater swaps the install tree only.

## 2. Definition of done

Final desired state:

| Criterion | Description |
|-----------|-------------|
| **Automated Windows build** | Pushing a tag (or merging to `main` / manual `workflow_dispatch`) triggers a workflow that produces a Windows packaged folder on a Windows runner. |
| **Packaged zip on GitHub Release** | Each user-visible version has a Release with an attached zip (e.g. `CaseCreator-1.2.3-win64.zip`) containing the full one-folder output. |
| **App-side Update** | The PySide6 app exposes an **Update** entry (menu or button) when updates are enabled. |
| **External updater** | The app launches a small **separate process** (e.g. `CaseCreatorUpdate.exe` or `update.cmd` + helper) that performs download/extract/swap while the main app has exited. |
| **Persistent data survives** | `%LOCALAPPDATA%\CaseCreator\` contents used for live config (see §8) are **never** deleted or overwritten by the updater except by explicit user action outside this flow. |
| **No source builds for users** | Users only download release zips; no Python/Git required on client machines. |

## 3. Recommended overall architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│  Developer (Mac): tag release, push → GitHub                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Actions (windows-latest)                                 │
│  • checkout • setup Python • install deps • run PyInstaller      │
│  • zip dist/CaseCreator/ • upload workflow artifact               │
│  • attach zip to GitHub Release (same tag)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  GitHub Release assets                                           │
│  • CaseCreator-x.y.z-win64.zip  (+ optional checksum file)        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  End-user PC                                                     │
│  Install dir: e.g. C:\Apps\CaseCreator\  (versioned app files)   │
│  Data dir:    %LOCALAPPDATA%\CaseCreator\  (never replaced)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
              User clicks Update → app exits
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  External updater process                                        │
│  • Download zip to temp • verify hash/sig (phase 2+)             │
│  • Backup current install dir • extract new tree • swap           │
│  • Relaunch CaseCreator.exe • report failure + rollback if needed │
└─────────────────────────────────────────────────────────────────┘
```

**Principle:** the **install directory** is disposable; **`%LOCALAPPDATA%\CaseCreator\`** is the source of truth for per-user rules and settings across versions.

## 4. Build pipeline design

### Trigger strategy (recommended)

1. **Release tags:** `v*` tags (e.g. `v1.4.0`) trigger `release` workflow — clearest mapping between git version and Release asset.
2. **`workflow_dispatch`** for manual test builds without a Release.
3. Optional: **`push` to `main`** for nightly/CI artifacts **not** advertised to production updater (avoid accidental user updates).

### Windows runner

- Use `runs-on: windows-latest` (or `windows-2022`).
- Install Python version pinned in repo (e.g. 3.11/3.12) via `actions/setup-python`.
- `pip install -r requirements.txt` (+ PyInstaller if not in requirements).
- Invoke packaging:
  - Either call `scripts\windows\build_pyside6_onefolder.bat` from repo root, or
  - Inline the same `py -m PyInstaller ...` flags the batch file uses (single source of truth: prefer one script both local and CI call).

### Packaged output format

- **One-folder** output: entire `dist\CaseCreator\` directory (per current conservative model).
- **CI artifact:** zip that directory so the zip root contains `CaseCreator.exe` and siblings (same layout as today’s “copy whole folder” deployment docs).

### Artifact naming / versioning

- **Zip name:** `CaseCreator-${VERSION}-win64.zip` where `VERSION` comes from tag (`v1.4.0` → `1.4.0`) or `github.ref_name`.
- **Embedded version:** long-term, write version into a small `version.txt` or build-time constant read by the app and updater (phase 2).
- **Checksum:** ship `SHA256SUMS` or `.sha256` alongside the zip on the Release for updater verification.

## 5. Release publishing design

### Workflow artifacts vs GitHub Releases assets

| Mechanism | Pros | Cons |
|-----------|------|------|
| **Workflow artifacts** | Easy, automatic retention | Not a stable public URL for production updater; retention expires; not ideal for “check for updates.” |
| **GitHub Release assets** | Stable download URLs; version metadata; normal for desktop updaters | Requires `contents: write` / `GH_TOKEN` with permissions; slightly more wiring. |

**Recommendation:** use **GitHub Releases** as the **authoritative update source** for the updater. Use workflow artifacts only for **CI debugging** and pre-release QA.

**Update metadata:** publish a small **`latest.json`** (or use GitHub Releases API) listing:

- `version`
- `asset_name` / direct `browser_download_url`
- `sha256`
- `min_supported_version` (optional)

The app or updater can fetch `latest.json` from the Release body or a raw asset to avoid parsing HTML.

## 6. Updater architecture

### End-user flow

1. User opens Case Creator → **Help / Check for updates** (or automatic check on startup, phase 2).
2. App compares **current version** vs **latest** from GitHub Release metadata (or `latest.json`).
3. If update available: show **Yes/No** dialog with version + short release notes link.
4. On **Yes**:
   - App writes a small **job file** (e.g. `%LOCALAPPDATA%\CaseCreator\update\pending.json`) with: target version, download URL, expected hash, install path, exe name to relaunch.
   - App spawns **updater** with elevated args if needed (prefer non-admin install path to avoid UAC; see §7).
   - App **exits cleanly** (flush settings if any in-memory).
5. **Updater** (separate process):
   - Downloads zip to `%TEMP%\CaseCreator-update\...`
   - Verifies hash
   - Backs up current install dir to `%LOCALAPPDATA%\CaseCreator\update\backup-<timestamp>\` (optional but recommended)
   - Stops any running `CaseCreator.exe` (wait/retry)
   - Replaces files under install root (delete old tree or rename + extract fresh)
   - Deletes temp download on success
   - Launches new `CaseCreator.exe` from install path
   - On failure: restore from backup and show error (see §9)

### Why external updater

Windows cannot reliably replace executables that are in use. The main app must exit before files under its install directory are overwritten. A tiny updater EXE (or signed script + helper) is the standard pattern.

## 7. Install / update folder model

Define explicitly:

| Location | Role | Updater behavior |
|----------|------|------------------|
| **Install root** | e.g. `C:\Apps\CaseCreator\` or `C:\Program Files\CaseCreator\` | **Replaced** on update (full tree swap). |
| **`%LOCALAPPDATA%\CaseCreator\`** | User rules, settings, update staging | **Never** deleted as part of normal update. Subfolders may be used for `update\` staging only. |

**Never replace:** files under `%LOCALAPPDATA%\CaseCreator\` listed in §8 except optional dedicated `update\` scratch with quarantine rules.

**Installer (first-time):** recommend installing to a user-writable path to avoid admin/UAC for updates; if installed under `Program Files`, updater may need elevation (more risk — phase later).

## 8. Persistence rules

These paths **must survive** routine app updates (updater must not touch them except app logic reading/writing them):

| File | Purpose |
|------|---------|
| `%LOCALAPPDATA%\CaseCreator\business_rules\v1\case_creator_rules.yaml` | Live unified rules (may be seeded on first run; user edits persist). |
| `%LOCALAPPDATA%\CaseCreator\local_settings.json` | Local user settings. |
| `%LOCALAPPDATA%\CaseCreator\admin_settings.json` | Admin settings. |

**Implementation guardrails:**

- Updater only operates on **install root** paths derived from `Path(exe).parent` (or recorded install path in registry/job file), never on `%LOCALAPPDATA%\CaseCreator\` except `update\` staging.
- Do not run `rmdir` on `%LOCALAPPDATA%\CaseCreator\`.
- App continues to use frozen-mode discovery already aligned with `%LOCALAPPDATA%\CaseCreator\...` for business rules.

## 9. Update failure and rollback behavior

| Failure | Recommended behavior |
|---------|----------------------|
| **Download fails** | Abort; show error; leave install unchanged; delete partial download. |
| **Hash mismatch** | Abort; do not extract; same as above. |
| **Unzip fails** | Abort; install unchanged. |
| **Replace fails** (locked file, disk full) | If backup exists: **restore previous tree** from backup; notify user. If no safe backup: fail closed with support instructions. |
| **New app fails to launch** | Optional: offer “open folder” / “restore backup” if health check fails within timeout (phase 2). |

**Rollback strategy:** before swap, rename current install folder to `CaseCreator.bak-<timestamp>` or copy to backup; extract new to `CaseCreator`; on success delete `.bak` after N days or keep one generation.

## 10. Security and safety boundaries

**Should:**

- Download only from **GitHub Releases** URLs (or your own HTTPS CDN mirroring the same asset).
- Verify **SHA-256** (minimum) of the zip before extract.
- Use **HTTPS** only.
- Prefer **release assets** tied to signed tags; document that users should not sideload zips from untrusted sources.

**Should not:**

- Execute arbitrary scripts downloaded from the internet.
- Disable verification to “make updates easier.”
- Update from random workflow artifact URLs without versioning.

**Code signing (phase 3+):** Authenticode-sign `CaseCreator.exe` and updater to reduce SmartScreen friction; out of scope for first pass but note for production hardening.

## 11. Recommended implementation phases

**Phase 0 — Planning (this document)**  
Lock folder model, Release-as-source-of-truth, persistence list.

**Phase 1 — CI build only**  
GitHub Actions: build on tag, upload workflow artifact, **manual** attach to Release (or automated upload with token).

**Phase 2 — Release automation**  
Workflow creates/updates GitHub Release and uploads zip + checksum using `GH_TOKEN`.

**Phase 3 — Version surface**  
App reads embedded version; “About” shows version; optional `latest.json` consumption.

**Phase 4 — Updater v1**  
External updater binary or signed helper; job file contract; download + verify + swap + relaunch; rollback folder.

**Phase 5 — In-app UX**  
Update button, progress, failure messages, link to release notes.

**Phase 6 — Hardening**  
Signing, delta updates (optional), staged rollout, telemetry-free error reporting.

## 12. Recommended first implementation pass

**Safest first code-change pass after this plan:**

1. Add **`.github/workflows/build-windows.yml`** (or similar) that:
   - triggers on `workflow_dispatch` and optionally on `push` of tags `v*`,
   - runs PyInstaller on `windows-latest`,
   - uploads the zip as a **workflow artifact** only.

2. Document in README: “Releases are built on GitHub Actions; download zip from Releases.”

**Do not** ship the updater or auto-update until Phase 1 is reliable and a human has verified the zip layout matches current manual deployment (`dist\CaseCreator\`).

## 13. Risks and guardrails

| Risk | Mitigation |
|------|------------|
| Wrong zip layout / missing DLLs | CI smoke test: launch exe headless or import check; compare file list to known-good manifest. |
| Updater deletes user data | Strict path allowlist; never touch `%LOCALAPPDATA%\CaseCreator\` except `update\`. |
| Partial update corrupts install | Backup + atomic swap pattern; verify hash before extract. |
| Program Files + UAC | Prefer per-user install path; document admin install limitations. |
| Token leakage | Use GitHub OIDC or fine-scoped `contents: write` on release only; no tokens in repo. |
| Supply chain | Tags + Release assets + checksum verification; optional signing later. |

---

## Final chat summary

1. **Yes** — **GitHub Actions (Windows runner) + GitHub Releases assets** is the recommended update distribution model for this project; workflow artifacts alone are insufficient as the long-term updater target.
2. **User settings and rules survive** because they live under **`%LOCALAPPDATA%\CaseCreator\`** (unified YAML, `local_settings.json`, `admin_settings.json`); the updater only replaces the **install directory** tree, not that folder.
3. **The updater** should run **after the main app exits**, **download and verify** the Release zip, **backup then replace** the install folder, and **relaunch** `CaseCreator.exe`, with **rollback** if swap or launch fails.
4. **Safest first implementation pass:** add a **Windows-only GitHub Actions workflow** that builds and publishes a **verifiable zip artifact** (workflow artifact first, then automate Release upload), **without** shipping auto-update or updater logic until the build is proven stable.
