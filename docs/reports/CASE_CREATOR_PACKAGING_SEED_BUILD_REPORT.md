# CASE CREATOR PACKAGING SEED BUILD REPORT

## 1. Summary of changes

This pass makes packaged builds seed-ready by explicitly including the unified seed file in the Windows PyInstaller one-folder build script and adding fresh-profile smoke-test guidance.

Implemented:

- Packaging script inclusion for `business_rules_seed/v1/case_creator_rules.yaml`.
- Build-time guard that fails early if that seed file is missing before packaging.
- A low-risk automated test asserting loader default bundled-seed lookup resolves to a real repo file.
- A dedicated fresh-profile packaged smoke-test checklist document.

Business-rule schema and runtime rule semantics were unchanged.

## 2. Files modified

- Modified: `scripts/windows/build_pyside6_onefolder.bat`
- Modified: `tests/test_business_rule_loader_dual_read.py`
- Created: `docs/packaging/PACKAGED_UNIFIED_CONFIG_FRESH_PROFILE_SMOKE_TEST.md`
- Created: `CASE_CREATOR_PACKAGING_SEED_BUILD_REPORT.md` (this file)

## 3. Packaging/build changes

`scripts/windows/build_pyside6_onefolder.bat` now:

1. Validates source seed exists before build:
   - `business_rules_seed\v1\case_creator_rules.yaml`
2. Includes the seed in both `py -m PyInstaller` and `python -m PyInstaller` paths via:
   - `--add-data "business_rules_seed\v1\case_creator_rules.yaml;business_rules_seed\v1"`

This guarantees the built app layout contains the file where runtime seed lookup expects it.

## 4. Runtime alignment

Current loader expects bundled seed at:

- `<bundle-root>/business_rules_seed/v1/case_creator_rules.yaml`

This pass aligns packaging output to that exact relative location by adding the data file with destination `business_rules_seed\v1`.

Additional automated alignment check added:

- `test_bundled_seed_default_path_exists_in_repo` validates loader bundled-seed default resolution points to an existing file with `unified_version: 1`.

## 5. Smoke test guidance

Added:

- `docs/packaging/PACKAGED_UNIFIED_CONFIG_FRESH_PROFILE_SMOKE_TEST.md`

Checklist covers:

- Fresh profile startup
- External directory creation
- Seeding of `%LOCALAPPDATA%/CaseCreator/business_rules/v1/case_creator_rules.yaml`
- Loading from external unified file
- Persistence across restart
- Non-overwrite of existing user-edited external file
- Optional invalid-YAML negative path

Automated checks added in-repo:

- bundled seed path exists and parses
- packaged-mode seeding/non-overwrite/failure behavior tests already in loader suite

## 6. Validation performed

- Ran:
  - `python3 -m unittest tests.test_business_rule_loader_dual_read tests.test_unified_business_rules_config tests.test_unified_retirement_equivalence -v`
- Result:
  - All tests passed (`Ran 25 tests ... OK`).
- Verified packaging script now includes explicit `--add-data` seed line and missing-seed guard.
- Lint check on touched files reported no issues.

## 7. Risks or limitations

- This pass updates the primary Windows build batch script; if alternate packaging/spec pipelines exist, they must be updated similarly.
- Fresh-profile smoke test remains partly manual until a full packaged executable CI job is introduced.
- Runtime behavior still depends on correct packaged data-file inclusion at build time (now guarded for this script).

## 8. Recommended next pass

Safest next step:

1. Run a real packaged build using the updated script.
2. Execute the fresh-profile smoke-test checklist on a Windows machine/profile.
3. If successful, add a lightweight CI/build verification step that inspects `dist/CaseCreator/` for:
   - `business_rules_seed/v1/case_creator_rules.yaml`
   - successful first-run external seeding behavior in a scripted smoke test.
