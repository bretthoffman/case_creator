# CASE CREATOR MARKDOWN ORGANIZATION SWEEP REPORT

## Goal

Consolidate Case Creator documentation by moving root-level `.md` files into the existing `docs/` hierarchy. No code, YAML, imports, or non-markdown assets were changed.

## Classification rules used

| Folder | Use |
|--------|-----|
| `docs/audits/` | Audits |
| `docs/plans/` | Plans, blueprints, migration/restructure planning |
| `docs/reports/` | Pass reports, implementation reports, config/seeding reports |
| `docs/packaging/` | Packaging / PyInstaller |
| `docs/ui/` | UI-specific docs |

## Files moved (from repository root)

All nine former root files fit cleanly into **plans** or **reports**; none were ambiguous for `audits/`, `packaging/`, or `ui/`.

### `docs/plans/` (1 file)

| File | Rationale |
|------|-----------|
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_PLAN.md` | Planning / design doc for expanded doctor overrides |

### `docs/reports/` (8 files)

| File | Rationale |
|------|-----------|
| `CASE_CREATOR_ARGEN_CONTACT_MODE_ON_OFF_REPORT.md` | Implementation report for argen contact mode on/off |
| `CASE_CREATOR_BASELINE_YAML_SEEDING_REPORT.md` | Baseline YAML seeding pass report |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_ARGEN_PARITY_REPORT.md` | Parity / validation report |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_FINAL_PARITY_REPORT.md` | Parity / validation report |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_FLAGGED_REPORT.md` | Flagged live readiness report |
| `CASE_CREATOR_EXPANDED_DOCTOR_OVERRIDE_PARITY_REPORT.md` | Parity report |
| `CASE_CREATOR_PRODUCTION_DOCTOR_YAML_SEED_REPORT.md` | Production seeding pass report |
| `CASE_CREATOR_PROJECT_TREE_ORGANIZATION_REPORT.md` | Project tree organization report |

## Files not moved

- Markdown already under `docs/**` (unchanged).
- Non-markdown assets (`.py`, `.yaml`, etc.) — out of scope per instructions.

## Conservative notes

- **Internal cross-links:** If bookmarks, wikis, or external docs pointed at root paths like `/CASE_CREATOR_*.md`, update them to the paths under `docs/plans/` or `docs/reports/`.
- **Self-references inside moved reports:** Some tables still list filenames without the `docs/...` prefix; content was not rewritten in this sweep—only locations changed.

## Result

- **Zero** Case Creator planning/report `.md` files remain at the repo root (no `*.md` at root after this pass).
- This sweep report lives at `docs/reports/CASE_CREATOR_MARKDOWN_ORGANIZATION_SWEEP_REPORT.md` so it does not reintroduce a floating root markdown file.
