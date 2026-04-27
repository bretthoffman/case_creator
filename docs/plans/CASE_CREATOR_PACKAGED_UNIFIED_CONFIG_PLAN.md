# CASE CREATOR PACKAGED UNIFIED CONFIG PLAN

## 1. Purpose

Packaged installs should not require editing files inside the app bundle directory because packaged locations can be read-only, replaced on upgrades, and difficult for beginners to find safely. The unified config model works best when the live editable file is in a stable user-writable app-data location that persists across upgrades.

This plan defines how to keep a bundled default unified seed for packaging while ensuring the live file is external and beginner-editable.

## 2. Definition of done

Final desired state:

- Packaged build includes a **bundled default seed**: `case_creator_rules.yaml`.
- Packaged runtime reads unified config from a **user-writable external path**.
- On first packaged run, if external file is missing, app creates folders and copies bundled seed there.
- On subsequent runs, packaged runtime reads only the external unified file.
- Source/dev mode still reads cleanly from repo-local path behavior.
- Operators and docs point to one editable file only: `case_creator_rules.yaml` at the correct runtime path.

## 3. Recommended packaged/runtime path architecture

Use a two-location model:

- **Bundled seed location (read-only/runtime resource):** inside package resources.
- **Live editable location (read-write):** app-data path per user machine.

Mode behavior:

- **Source/dev mode:** continue using repo-relative `business_rules/v1/case_creator_rules.yaml` (or env override if set).
- **Frozen/package mode:** resolve external app-data directory first; ensure external file exists via seeding from bundled resource if missing; load from external file.

Do not edit bundled file at runtime.

## 4. Proposed packaged editable config location

Recommended live packaged path (Windows/frozen):

- Directory: `%LOCALAPPDATA%/CaseCreator/business_rules/v1/`
- File: `%LOCALAPPDATA%/CaseCreator/business_rules/v1/case_creator_rules.yaml`

This aligns with existing frozen-path conventions already used in loader/settings behavior around `%LOCALAPPDATA%/CaseCreator`.

## 5. Proposed bundled default config location

Recommended bundled seed path inside app resources:

- `business_rules_seed/v1/case_creator_rules.yaml`

Rationale:

- Keeps seed content clearly separate from the external editable live path.
- Avoids ambiguity with archived/backward folders.
- Easy to include explicitly in packaging spec and resource lookup code.

Implementation note for future code pass: resolve bundled seed via runtime resource helpers appropriate for PyInstaller/frozen mode (e.g., `sys._MEIPASS` aware lookup), with a source-mode fallback to repo path.

## 6. Loader path resolution plan

Introduce a small path-resolution seam (planning only):

1. Resolve mode (`override`, `env_override`, `frozen_windows`, `source`) as today.
2. Resolve two paths:
   - `external_live_unified_path`
   - `bundled_seed_unified_path` (only meaningful for packaged mode)
3. Behavior by mode:
   - **Source:** load repo-local unified file directly (current behavior).
   - **Frozen:** ensure external exists (seed if needed), then load external.

Proposed functional split:

- `resolve_unified_runtime_paths(...) -> UnifiedRuntimePaths`
- `seed_external_unified_if_missing(paths) -> SeedResult`
- `load_business_rule_config_preview(...)` remains consumer of resolved live path.

## 7. First-run seeding plan

When packaged app starts:

1. Compute external directory `%LOCALAPPDATA%/CaseCreator/business_rules/v1`.
2. Create directory tree if missing (`mkdir(parents=True, exist_ok=True)`).
3. If external `case_creator_rules.yaml` exists:
   - Do nothing (no overwrite).
4. If external file missing:
   - Read bundled seed `business_rules_seed/v1/case_creator_rules.yaml`.
   - Write copy to external path atomically (temp file + rename preferred).
5. Emit lightweight observability:
   - `INFO`: seeded new external unified config
   - `INFO`: external unified already exists
   - `WARNING/ERROR`: seeding failed with reason

If seeding fails:

- Loader should return explicit preview errors (not silent success).
- Keep safe fallback behavior explicit (see section 8).

## 8. Validation and fallback behavior

Target safe behavior:

- **Packaged external unified missing:**
  - Attempt seed from bundled default.
  - If seed succeeds, validate/load seeded file.
  - If seed fails, return errors and use schema defaults (current safe pattern), with clear logs.

- **Packaged external unified invalid:**
  - Do not overwrite user file automatically.
  - Return validation errors and use schema defaults (current behavior), with explicit guidance in warning text.

- **Bundled seed missing/unreadable:**
  - Return explicit errors and use schema defaults.
  - Log as packaging/configuration defect.

- **Source-mode repo unified invalid:**
  - Keep current behavior: preview errors + defaults.

Guardrail: no hidden fallback to retired split files.

## 9. Packaging/build implications

Packaging must include:

- Code modules (unchanged).
- Templates/resources (existing packaged set).
- **Bundled default unified seed** at deterministic bundled path:
  - `business_rules_seed/v1/case_creator_rules.yaml`

Likely required in build scripts/spec:

- Add seed file to packaged data collection.
- Ensure resource lookup works in both source and frozen modes.
- Keep archive-only retired split files out of live packaged runtime path (optional to ship as docs/reference, but not required for runtime).

## 10. Migration plan from current state

Current state (after split retirement): runtime expects unified file in resolved `business_rules/v1` path. Migration to package-friendly external model:

1. Add path resolver that distinguishes packaged external live path vs bundled seed path.
2. Add first-run seed function in packaged mode only.
3. Keep source mode unchanged.
4. Add tests for packaged path resolution and seeding outcomes.
5. Update operator docs to point packaged users to `%LOCALAPPDATA%/CaseCreator/business_rules/v1/case_creator_rules.yaml`.

No schema changes needed.

## 11. Recommended implementation phases

Phase 1: Path abstraction only

- Add path dataclass + resolution helpers.
- No behavior change yet; wire logging only.

Phase 2: First-run seeding in packaged mode

- Implement seed-if-missing.
- Keep current validation/default error semantics.

Phase 3: Packaging inclusion

- Add bundled seed file to package build config.
- Add startup smoke checks in CI/build validation.

Phase 4: Docs/operator guidance

- Update beginner docs for packaged edit location.
- Add troubleshooting for invalid YAML and recovery.

Phase 5: Hardening

- Optional atomic-write improvements, checksums/version stamp in comments, and better diagnostics.

## 12. Recommended first implementation pass

Safest first code pass:

- Implement **path-resolution seam + packaged seed-if-missing** behind existing loader.
- Do not change schema or rule semantics.
- Keep current error/default behavior when validation fails.
- Add focused tests for:
  - packaged path resolution,
  - first-run seeding success,
  - seed missing/failure behavior,
  - existing external file not overwritten.

This pass yields immediate package-friendliness without broad runtime risk.

## 13. Risks and guardrails

Primary risks:

- Missing bundled seed in package build.
- Incorrect frozen resource path resolution.
- Accidental overwrite of user-edited external config.
- Silent defaults if seeding/validation fails without clear logs.

Guardrails:

- Never overwrite existing external unified file automatically.
- Treat bundled seed missing as explicit runtime error condition.
- Keep prominent logs and preview errors with actionable path details.
- Add packaging smoke test: packaged app can seed + validate external unified on fresh profile.
- Keep one canonical filename: `case_creator_rules.yaml`.
