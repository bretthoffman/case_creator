# CASE CREATOR UNIFIED RETIRE SPLIT REPORT

## 1. Summary of findings

The live unified file **`business_rules/v1/case_creator_rules.yaml`** was shown **equivalent** to the pre-retirement quartet of YAML files for all four exposed families:

- **Normalized config:** `validate_unified_business_rules_config` on a merge of the archived split files matches `load_business_rule_config_preview()` for the shipped `v1` directory (unified on disk).
- **Loader:** `rules_load_source` is `unified` for normal operation; archived content is not read.
- **Runtime:** Doctor, shade, routing, and argen resolvers were checked against the same effective dict implied by the archived merge (`tests/test_unified_retirement_equivalence.py`); the **doctor policy parity harness** still passes end-to-end, including production seed and repo `v1` load checks.

Because equivalence was strong and automated checks passed, the **active** per-family YAML files were **removed** from `business_rules/v1/` and **copied** to **`business_rules/archive/v1_split_backup/`** as a read-only historical reference. The loader no longer reads split files; a missing or invalid unified file results in **schema defaults** and **preview errors**, not silent use of archived YAML.

## 2. Files modified

| Action | Path |
|--------|------|
| Created | `business_rules/archive/v1_split_backup/README.md` |
| Created (copy) | `business_rules/archive/v1_split_backup/doctor_overrides.yaml` |
| Created (copy) | `business_rules/archive/v1_split_backup/shade_overrides.yaml` |
| Created (copy) | `business_rules/archive/v1_split_backup/routing_overrides.yaml` |
| Created (copy) | `business_rules/archive/v1_split_backup/argen_modes.yaml` |
| Removed (from active v1) | `business_rules/v1/doctor_overrides.yaml` |
| Removed (from active v1) | `business_rules/v1/shade_overrides.yaml` |
| Removed (from active v1) | `business_rules/v1/routing_overrides.yaml` |
| Removed (from active v1) | `business_rules/v1/argen_modes.yaml` |
| Modified | `business_rules/v1/case_creator_rules.yaml` (header comments: unified-only, archive pointer) |
| Modified | `infrastructure/config/business_rule_loader.py` (unified-only + defaults on failure) |
| Modified | `infrastructure/config/business_rule_models.py` (`rules_load_source` default / semantics) |
| Modified | `infrastructure/config/business_rule_schemas.py` (docstrings + omission warning wording) |
| Modified | `tests/test_business_rule_loader_dual_read.py` |
| Modified | `tests/test_unified_business_rules_config.py` (archive path for merge test) |
| Modified | `tests/doctor_policy_parity_harness.py` (temp rules via unified only) |
| Modified | `tests/fixtures/doctor_policy_abby_vd_offline.yaml` (comment) |
| Created | `tests/test_unified_retirement_equivalence.py` |
| Created | `CASE_CREATOR_UNIFIED_RETIRE_SPLIT_REPORT.md` (this file) |

## 3. Equivalence evidence

- **Dict equality:** Merged archived YAML (four roots + `unified_version: 1`) validates to the same normalized map as loading **`case_creator_rules.yaml`** from `business_rules/v1/` (`test_shipped_v1_uses_unified_matches_archived_baseline`, `test_in_memory_split_merge_matches_preview` using archive paths).
- **Fixture parity:** `tests/fixtures/unified_business_rules_baseline.yaml` matches loader output when placed as the only rules file in a temp dir, and matches an archive-built unified file (`test_fixture_unified_matches_archive_baseline_dir`).
- **Resolvers:** `resolve_contact_model_mode`, `resolve_non_argen_shade_markers`, `resolve_destination_key`, and `resolve_doctor_template_override_key` (with outcomes flag on) were asserted against the effective config implied by the archive (`test_runtime_resolvers_match_effective_config_baseline`).
- **Harness:** `python tests/doctor_policy_parity_harness.py` — all groups green, including **production_seed** (doctor subtree read from unified) and **repo v1 load**.

No split-only live behavior was found: the unified file contained the same seeded subtrees as the archived files.

## 4. Retirement decision

**Retired from the active rules directory:** the four split YAMLs are **not** present under `business_rules/v1/` anymore.

**Archived (not loaded):** identical copies live under `business_rules/archive/v1_split_backup/` with a README explaining they are reference-only.

**Fallback:** There is **no** runtime fallback to those archived files. Invalid/missing `case_creator_rules.yaml` → **defaults + errors** (explicitly tested).

## 5. Loader/runtime changes

- **`load_business_rule_config_preview`** loads only `case_creator_rules.yaml` / `case_creator_rules.yml` (deterministic preference when both exist).
- **Success:** `rules_load_source="unified"`, `effective_config` from `validate_unified_business_rules_config`.
- **Missing unified file:** `rules_load_source="defaults"`, all families set to `default_*()`, `errors` / `unified_validation_errors` populated, **WARNING** log.
- **Unreadable or invalid unified:** same as missing (defaults + diagnostics), **WARNING** log with a short error preview.
- **Logging:** INFO on successful unified load; WARNING when using defaults.

Per-family file discovery (`doctor_overrides.yaml`, etc.) was **removed** from the loader.

## 6. Validation performed

- `python3 -m unittest tests.test_unified_business_rules_config tests.test_business_rule_loader_dual_read tests.test_unified_retirement_equivalence -v` — all passed.
- `python3 tests/doctor_policy_parity_harness.py` — all passed.
- Import smoke: `load_business_rule_config_preview()` from repo root returns `unified` with no errors.

## 7. Risks or limitations

- **Broken unified file** now means **defaults for all families** (possible mis-routing until fixed). Operators must keep `case_creator_rules.yaml` valid; logs and `BusinessRuleConfigPreview.has_errors` surface failure.
- **Deployments** that relied on editing only split files under `v1` must switch to the unified file (archived copies help manual recovery).
- **Documentation** elsewhere in `docs/reports/` may still mention old paths; those are historical unless updated in a later docs sweep.

## 8. Final operator guidance

- **Edit only:** `business_rules/v1/case_creator_rules.yaml` (or `.yml` if that is the sole unified name in your directory — prefer `.yaml`).
- **Do not expect** `doctor_overrides.yaml` / `shade_overrides.yaml` / `routing_overrides.yaml` / `argen_modes.yaml` under `v1` to load; use the **archive** folder only as a reference or to copy content back into the unified file by hand.
- **Save and restart** the app after changes.

---

## Final chat summary

1. **Yes** — `case_creator_rules.yaml` matches the old split backups for normalized effective config and for representative live resolver behavior (plus full parity harness).
2. **Removed** from `business_rules/v1/` and **archived** under `business_rules/archive/v1_split_backup/` (not loaded at runtime).
3. **Unified-only** for live loading — **no** split-file dual-read; failure → **defaults** + errors, not archived YAML.
4. Operators should edit **`business_rules/v1/case_creator_rules.yaml`** only.
