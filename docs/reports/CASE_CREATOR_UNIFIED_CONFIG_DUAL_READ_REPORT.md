# CASE CREATOR UNIFIED CONFIG DUAL READ REPORT

## 1. Summary of changes

The business-rules loader now performs a **dual read**: it looks for a unified document (`case_creator_rules.yaml`, then `case_creator_rules.yml`) in the resolved rules directory. If that file **exists and validates**, `BusinessRuleConfigPreview.effective_config` is built **only** from `validate_unified_business_rules_config`’s normalized payload (same four family keys as today). If the unified file is **missing**, behavior is **unchanged**: each family file is discovered and validated as before. If the unified file is **present but unreadable or invalid**, the loader **records** the failure on the preview and **falls back** to the same split-file path used historically, so effective rules still come from the quartet of YAML files when they are valid.

`BusinessRuleConfigPreview` gained small, defaulted fields so callers can see **unified vs split** and inspect **unified validation errors** after a fallback without changing the shape of `effective_config`.

## 2. Files modified

| Action | Path |
|--------|------|
| Modified | `infrastructure/config/business_rule_loader.py` |
| Modified | `infrastructure/config/business_rule_models.py` |
| Modified | `infrastructure/config/business_rule_schemas.py` (docstring only: unified validator referenced by loader) |
| Modified | `tests/test_unified_business_rules_config.py` (assert split metadata when loading shipped `v1`) |
| Created | `tests/test_business_rule_loader_dual_read.py` |
| Created | `CASE_CREATOR_UNIFIED_CONFIG_DUAL_READ_REPORT.md` (this file) |

## 3. Loader behavior

**Discovery order for unified file**

1. `case_creator_rules.yaml` under the resolved base directory  
2. Else `case_creator_rules.yml`  
3. If **both** exist, **`.yaml` wins**; a **warning** notes that the other filename is ignored.

**If a unified path is chosen**

- Parse with the same YAML path as other rules files (`yaml.safe_load`).
- **Read/parse error** → fall back to split files; store the error string in `unified_validation_errors` and add a top-level warning.
- **Validate** with `validate_unified_business_rules_config`.
- **Valid** → build preview with `rules_load_source="unified"`, per-family `BusinessRuleFileReport` rows pointing at the unified path (`loaded` / `used_default` reflect whether each family key was present in the document).
- **Invalid** → fall back to split files; `unified_validation_errors` lists schema errors; top-level warnings include a short summary that the unified file was skipped.

**If no unified candidate exists**

- Existing per-family loop runs unchanged; `rules_load_source="split"`, `unified_file_path=None`.

**Effective config shape**

- Always `doctor_overrides`, `shade_overrides`, `routing_overrides`, `argen_modes` — unchanged for downstream code.

## 4. Reporting behavior

| Field | Meaning |
|--------|--------|
| `rules_load_source` | `"unified"` if the unified file was used successfully; `"split"` if split files drove the result (including after fallback). |
| `unified_file_path` | Absolute-path string of the unified file when one was selected for read/validate; set on fallback attempts too so operators know which file failed. |
| `unified_validation_errors` | Non-empty when the unified file was unreadable or failed validation; empty when unified succeeded or was never attempted. |
| `warnings` | Includes picker warnings (e.g. both `.yaml` and `.yml`), unified validator warnings when load succeeded, read-failure lines, and a summary when falling back from invalid unified. |
| `has_errors` | Unchanged: **only** top-level `errors` and per-family `BusinessRuleFileReport.errors` from the **split** load path. A bad unified file that was successfully replaced by split files does **not** flip `has_errors` by itself, so the app keeps running; operators rely on `unified_validation_errors` and warnings. |

## 5. Validation performed

- `python3 -m unittest tests.test_unified_business_rules_config tests.test_business_rule_loader_dual_read -v` — all tests passed.
- Smoke: `load_business_rule_config_preview()` from repo root with no `case_creator_rules.yaml` in `business_rules/v1/` — `rules_load_source` is `split`, no import/cycle issues.

## 6. Production safety

- **No domain or cache modules were changed**; they still consume `effective_config` from `load_business_rule_config_preview()`.
- **Shipped `business_rules/v1/`** still has **no** unified file unless you add one, so **default deployments behave exactly as before** (split-only).
- **Semantically equivalent** unified content produces the **same** normalized families as split-only loading (covered by tests using the existing baseline fixture).
- Fallback ensures a broken unified file **cannot** empty out rules by itself as long as split files remain valid.

## 7. Risks or limitations

- Operators may not notice a failed unified file if they only watch `has_errors`; they should monitor `unified_validation_errors` / warnings in any UI or logs that surface preview metadata.
- **Two filenames** (`.yaml` vs `.yml`) require discipline; both present uses `.yaml` only, with a warning.
- **Precedence:** when unified is valid, **split files are not merged** on top of it; the unified document is the sole source for effective config in that case (by design for this pass).
- Documentation / operator runbooks may still describe four files until `case_creator_rules.yaml` is the primary edit surface.

## 8. Recommended next pass

- **Operator-facing file:** add an optional **shipped** `business_rules/v1/case_creator_rules.yaml` that mirrors the current quartet (or document a one-time copy procedure), plus UI or startup logs that print `rules_load_source` and surface `unified_validation_errors` when non-empty.
- **Hardening:** consider treating “unified present but invalid” as a **stronger** signal (e.g. optional env flag to fail closed) for sites that want to forbid silent fallback.

---

## Final chat summary

1. **Yes** — the loader reads `case_creator_rules.yaml` / `case_creator_rules.yml` when present and valid and uses its normalized four-family config.
2. **Yes** — missing unified file keeps prior split behavior; invalid or unreadable unified records errors and **falls back** to split files with clear preview metadata.
3. **Yes** — `effective_config` remains a dict with the same four family keys; no domain/rule-evaluation code was changed.
4. **Safest next pass** — ship or document a canonical unified file for operators, and improve observability (logging/UI) for `rules_load_source` and `unified_validation_errors` so fallback is never silent in practice.
