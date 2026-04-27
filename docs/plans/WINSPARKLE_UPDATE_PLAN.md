# WinSparkle Update Plan (Planning Only)

This is a conservative updater planning document for the packaged PySide6 Windows app.  
No updater code is integrated in this step.

## 1) Is WinSparkle / pywinsparkle a good fit?

**Yes, likely a good fit** for this project’s intended model:
- Windows desktop app
- packaged distribution
- release-driven updates
- user prompt + click-to-update flow

Why it fits:
- WinSparkle is purpose-built for Windows app update prompts.
- `pywinsparkle` provides Python bindings for integration in PySide6 startup flow.
- Supports appcast-based update metadata, which can point to GitHub release assets.

## 2) What the app will need to check for updates

At high level, updater-enabled app builds will need:
- a stable application identifier and app name,
- a consistent app version string embedded in app runtime,
- WinSparkle initialization during app startup,
- a reachable update feed URL (appcast),
- signed update artifacts (recommended/expected for safe distribution).

## 3) Role of GitHub Releases

GitHub Releases should be the canonical published artifact source:
- each released version has a release tag and notes,
- packaged installer/archive asset(s) are uploaded there,
- appcast entries reference those assets (direct URLs).

Recommended:
- use immutable version tags (e.g., `v1.0.0`, `v1.0.1`),
- keep release notes concise and operator-facing,
- keep one authoritative repository/release channel.

## 4) Role of the appcast feed

Appcast is the machine-readable update index WinSparkle consumes.

It should provide:
- latest version metadata,
- release notes URL,
- download URL,
- file size and signature metadata (as required by chosen security setup).

Deployment model:
- App checks appcast URL.
- If newer version exists, user sees prompt.
- User clicks Update -> downloads/installs new package.

## 5) Release artifacts needed per version

For each updater-enabled release, publish at minimum:
- packaged Windows build artifact (installer or zip strategy to be finalized),
- release notes,
- appcast update entry pointing to artifact URL.

Likely supporting artifacts:
- checksums,
- signature files/metadata,
- optional internal rollout notes.

## 6) Signing strategy (high level)

Strong recommendation:
- Sign distributed Windows binaries/installers with code-signing certificate.
- Use a controlled signing step in release pipeline (manual first, automated later).
- Keep signing key/certificate handling out of repo and out of app settings.

Appcast/signature model:
- Ensure WinSparkle signature expectations are met by release artifacts and feed metadata.
- Validate signature verification behavior on test machine before broader rollout.

## 7) Versioning strategy recommendation

Use SemVer-style versioning:
- `MAJOR.MINOR.PATCH`

Suggested policy:
- `PATCH`: fixes/UI-only changes/no behavior contract changes.
- `MINOR`: new features/settings/update flow improvements.
- `MAJOR`: breaking operational/deployment changes.

Practical note:
- Move away from placeholder UI version (`0.0.0`) before updater integration.
- Define one canonical version source used by build/release/appcast.

## 8) App changes eventually needed (high-level only)

When updater integration begins (future step), likely changes:
- add updater init/check calls in PySide6 startup shell layer,
- add app metadata/version source wiring,
- add config for update channel/appcast URL (possibly environment/release-config driven),
- add “Check for updates” manual trigger (optional UI convenience),
- add graceful handling for updater errors/timeouts in UI.

No backend processing changes are needed for updater integration.

## 9) One-machine updater validation before 4-machine rollout

Run first on one designated test workstation:

1. Install baseline packaged build (updater-enabled).
2. Confirm app launches and real import still works.
3. Publish a newer test release to GitHub with valid appcast entry.
4. Trigger update check and confirm prompt appears.
5. Execute update and verify:
   - app updates to expected version,
   - `%LOCALAPPDATA%\CaseCreator` settings persist,
   - real import still succeeds,
   - no template/settings path regressions.
6. Validate rollback behavior if update fails mid-flow.

Only after this passes should broader deployment proceed.

## 10) Likely risks/pitfalls for this project

- Version mismatch across app binary, appcast, and release tag.
- Unsigned or improperly signed artifacts causing trust/update failures.
- Appcast URL reachability issues on locked-down networks.
- Update replacing install location while preserving `%LOCALAPPDATA%` settings (must verify).
- Packaging mode/structure changes between releases causing updater install drift.
- Operator confusion if fallback/legacy launch paths remain visible during transition.

## 11) Recommended staged rollout sequence

## Stage A - Preparation
- Finalize versioning source of truth.
- Decide artifact format (installer vs zip) for updater compatibility.
- Establish signing process.
- Create and validate appcast generation/publication process.

## Stage B - One-machine updater pilot
- Enable updater in build.
- Validate end-to-end update flow on one machine.
- Confirm no regression in import workflow/output compatibility.

## Stage C - Wider rollout (4 machines)
- Release updater-enabled version to all machines.
- Monitor first update cycle closely.
- Keep fallback launch path and rollback instructions ready during first cycle.

---

This plan is intentionally conservative and keeps fragile backend processing logic out of updater integration scope.
