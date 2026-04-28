# CASE CREATOR GITHUB RELEASE PUBLISHING REPORT

## 1. Summary of changes

Extended the existing Windows build workflow so **tagged builds (`v*`) now publish release assets to GitHub Releases** while preserving the current successful build + artifact behavior.

Key additions:
- Release-publishing permissions (`contents: write`)
- Tag-only SHA256 checksum generation for the packaged zip
- Tag-only upload of zip + checksum to the matching GitHub Release using a stable action

No app/runtime code or business-rule semantics were changed.

## 2. Files modified

- `.github/workflows/build-windows.yml`
- `CASE_CREATOR_GITHUB_RELEASE_PUBLISHING_REPORT.md` (this report)

## 3. Workflow behavior

The workflow still supports:
- `workflow_dispatch` manual runs
- `push` tags matching `v*`

Build/package path remains intact:
- Windows runner build
- Dependency install
- Existing PyInstaller batch packaging
- Existing bundled-seed validation (`business_rules_seed/v1/case_creator_rules.yaml` presence in dist)
- Zip creation
- Workflow artifact upload

New behavior (tag builds only):
- Compute `CaseCreator-vX.Y.Z-win64.zip.sha256`
- Publish zip + checksum to GitHub Release

## 4. Release asset behavior

For refs like `refs/tags/v1.0.2`:
- Zip name: `CaseCreator-v1.0.2-win64.zip`
- Checksum file: `CaseCreator-v1.0.2-win64.zip.sha256`

Release upload implementation:
- `softprops/action-gh-release@v2`
- Files uploaded:
  - `${{ env.ZIP_NAME }}`
  - `${{ env.ZIP_NAME }}.sha256`

Release upload is gated to tags only:
- `if: startsWith(github.ref, 'refs/tags/v')`

Manual `workflow_dispatch` runs do not attempt release publishing.

## 5. Validation performed

- Parsed workflow YAML successfully (`YAML OK`).
- Confirmed trigger behavior remains (`workflow_dispatch` + `push.tags: v*`).
- Confirmed build/packaging/seed-validation steps remain unchanged in intent.
- Confirmed release upload and checksum steps are tag-gated only.

Not executed in this environment:
- Live GitHub tag run to verify remote Release asset upload end-to-end.

## 6. Risks or limitations

- Release upload requires repository permissions allowing workflow `contents: write`.
- If a tag run references a protected/immutable release state, upload may fail and require repository-side release policy adjustment.
- This pass intentionally does not add updater/app-side update logic.

## 7. Recommended next step

Push the workflow change and run a real tag test (e.g., `v1.0.x-rc` in a safe branch/repo flow) to verify:
1. build passes,
2. artifact uploads,
3. GitHub Release receives both zip and `.sha256`.

Then proceed to the next conservative pass: app-side metadata/check plumbing (still no auto-install).
