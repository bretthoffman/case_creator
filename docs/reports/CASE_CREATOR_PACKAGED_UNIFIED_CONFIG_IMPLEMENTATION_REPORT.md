# CASE CREATOR PACKAGED UNIFIED CONFIG IMPLEMENTATION REPORT

## 1. Summary of changes

This pass implemented packaged-aware unified config loading while preserving business-rule semantics.

- Added a runtime path-resolution seam (`resolve_unified_runtime_paths`) that returns a structured `UnifiedRuntimePaths` object with:
  - runtime mode,
  - live unified config path,
  - bundled seed path (packaged mode).
- Added packaged first-run seed behavior in `business_rule_loader`:
  - create external `%LOCALAPPDATA%/CaseCreator/business_rules/v1` directory tree,
  - if no external unified file exists (`.yaml`/`.yml`), copy bundled seed into `case_creator_rules.yaml`,
  - never overwrite existing user file.
- Integrated seeding into loader startup flow for frozen mode only.
- Added focused logging for path/use/seed outcomes.
- Added tests for source vs frozen path resolution and seeding success/failure/overwrite protections.
- Added bundled default seed file at `business_rules_seed/v1/case_creator_rules.yaml`.

No schema or rule evaluation semantics were changed.

## 2. Files modified

- Modified: `infrastructure/config/business_rule_loader.py`
- Modified: `infrastructure/config/business_rule_models.py`
- Modified: `tests/test_business_rule_loader_dual_read.py`
- Created: `business_rules_seed/v1/case_creator_rules.yaml`
- Created: `CASE_CREATOR_PACKAGED_UNIFIED_CONFIG_IMPLEMENTATION_REPORT.md` (this file)

## 3. Path resolution behavior

### Source/dev (including explicit override/env override)

- `resolve_unified_runtime_paths(...)` keeps existing behavior:
  - `override_base_dir` -> mode `override`, live path under that directory,
  - `CASE_CREATOR_BUSINESS_RULES_DIR` -> mode `env_override`, live path under that directory,
  - default source mode -> repo-local `business_rules/v1/case_creator_rules.yaml`.
- No seeding is attempted in these modes.

### Frozen/package mode

- Path resolution returns:
  - external live path: `%LOCALAPPDATA%/CaseCreator/business_rules/v1/case_creator_rules.yaml`,
  - bundled seed path: `business_rules_seed/v1/case_creator_rules.yaml` from packaged resource root (`sys._MEIPASS` when present; repo root fallback for non-packaged tests/dev).

## 4. First-run seeding behavior

In frozen mode only (`mode == "frozen_windows"`):

1. Create external directory tree if missing.
2. Detect existing unified file(s) via existing deterministic picker (`.yaml` preferred then `.yml`).
3. If an external unified file already exists -> log INFO and do nothing.
4. If missing:
   - read bundled seed bytes,
   - write to a temporary file,
   - atomically replace to `case_creator_rules.yaml`.
5. If seeding fails (dir create, seed missing, copy error):
   - log ERROR,
   - return defaults preview with `errors`/`unified_validation_errors` populated.

Existing external files are never overwritten automatically.

## 5. Validation performed

Executed:

- `python3 -m unittest tests.test_business_rule_loader_dual_read tests.test_unified_business_rules_config tests.test_unified_retirement_equivalence -v`

Result:

- All tests passed (`Ran 24 tests ... OK`).
- New/updated assertions cover:
  - source-mode runtime path resolution,
  - frozen runtime path resolution (external + bundled seed),
  - first-run seed success,
  - existing external file preserved (no overwrite),
  - seed failure -> defaults + diagnostics,
  - existing unified-only behavior still intact for non-packaged paths.

Also checked:

- imports resolve, no circular import issues observed,
- lints for touched files reported no issues.

## 6. Production safety

Why behavior is safe and conservative:

- Business-rule schema validators were untouched.
- Doctor/shade/routing/argen runtime semantics are unchanged; only file path resolution + seed-if-missing flow changed.
- Source/dev path behavior remains compatible with current repo-local workflow.
- Frozen mode still uses unified-only model and keeps existing safe-defaults-on-error behavior.
- No split fallback was reintroduced.

## 7. Risks or limitations

- This pass adds loader support and tests, but packaged build scripts/spec still need to explicitly include `business_rules_seed/v1/case_creator_rules.yaml` for real frozen artifacts.
- Frozen-path tests simulate frozen mode via targeted mocks; they do not run an actual packaged executable.
- If packaged seed is omitted at build time, loader now surfaces clear diagnostics and defaults, but user still needs a corrected build.

## 8. Recommended next pass

Safest next step:

1. Update packaging/build spec(s) to include `business_rules_seed/v1/case_creator_rules.yaml` explicitly.
2. Add one packaging smoke test/checklist step (fresh profile) verifying:
   - first launch creates `%LOCALAPPDATA%/CaseCreator/business_rules/v1/case_creator_rules.yaml`,
   - app loads unified config from external path,
   - restart preserves user edits.
3. Update operator-facing packaged docs to point users to the external editable path.
