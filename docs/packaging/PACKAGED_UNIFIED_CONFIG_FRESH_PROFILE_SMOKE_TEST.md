# Packaged Unified Config Fresh-Profile Smoke Test

## Goal

Verify a packaged build can seed and load unified rules for a brand-new user profile.

## Prerequisites

- Canonical unified rules in repo: `business_rules/v1/case_creator_rules.yaml` (human-edited source of truth).
- Built one-folder package from `scripts/windows/build_pyside6_onefolder.bat` (refreshes `business_rules_seed/v1/` from canonical before packaging).
- Build output folder present (e.g. `dist\CaseCreator\`)
- Windows machine/profile with write access to `%LOCALAPPDATA%`

## Steps

1. **Start from a fresh profile state**
   - Close all running Case Creator instances.
   - Rename or delete `%LOCALAPPDATA%\CaseCreator\business_rules\v1\` if it exists.

2. **Launch packaged app**
   - Start `CaseCreator.exe` from the packaged output folder.

3. **Verify first-run seeding**
   - Confirm file now exists:
     - `%LOCALAPPDATA%\CaseCreator\business_rules\v1\case_creator_rules.yaml`
   - Confirm file is non-empty and has `unified_version: 1`.

4. **Verify app loads external unified file**
   - Check logs/diagnostics for unified source line if available.
   - Ensure no warnings about missing unified seed/load defaults during normal startup.

5. **Verify persistence of user edits**
   - Edit external file (safe low-impact change, e.g. add a comment line).
   - Restart packaged app.
   - Confirm edit is still present (file was not overwritten).

6. **Verify non-overwrite behavior**
   - Record file timestamp.
   - Restart app again.
   - Confirm timestamp/content unchanged unless user edited it.

## Negative-path checks (recommended)

1. Introduce temporary invalid YAML in external file.
2. Launch app and confirm diagnostics indicate validation/load issue.
3. Restore valid YAML and confirm normal startup.

## Expected result

- First launch seeds `%LOCALAPPDATA%\CaseCreator\business_rules\v1\case_creator_rules.yaml` from bundled seed.
- Subsequent launches use existing external file and do not overwrite it.
- Invalid external YAML surfaces diagnostics and safe fallback behavior.
