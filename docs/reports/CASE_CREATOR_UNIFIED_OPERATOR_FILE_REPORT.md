# CASE CREATOR UNIFIED OPERATOR FILE REPORT

## 1. Summary of changes

A canonical operator-facing unified file was added at **`business_rules/v1/case_creator_rules.yaml`**. It was **seeded** by loading the four existing split YAML roots (`doctor_overrides`, `shade_overrides`, `routing_overrides`, `argen_modes`) from `business_rules/v1/*.yaml`, merging them under `unified_version: 1`, and writing one document. A **beginner-friendly comment block** at the top covers save/restart, human editing guidance, and **LLM copy-paste instructions** (ask clarifying questions, return the full file, no invented keys, preserve unrelated content).

The **split YAML files were not modified or removed**; the dual-read loader still prefers a **valid** unified file, falls back to split files when unified is missing or invalid, and records preview metadata as before.

**Lightweight observability:** `infrastructure/config/business_rule_loader.py` now logs at **INFO** when loading **split-only** (no unified file) or **unified** successfully, and at **WARNING** when the unified file is **unreadable** or **schema-invalid** and the loader **falls back** to split files (with a short error preview).

The test fixture **`tests/fixtures/unified_business_rules_baseline.yaml`** was refreshed from the same parsed document as the seeded file (without comments) so tests stay aligned.

## 2. Files modified

| Action | Path |
|--------|------|
| Created | `business_rules/v1/case_creator_rules.yaml` |
| Modified | `infrastructure/config/business_rule_loader.py` (logging) |
| Modified | `tests/test_unified_business_rules_config.py` (expect `unified` when loading shipped `v1`) |
| Modified | `tests/test_business_rule_loader_dual_read.py` (seeded validation, equivalence, log assertion) |
| Modified | `tests/fixtures/unified_business_rules_baseline.yaml` (synced to seeded content) |
| Created | `CASE_CREATOR_UNIFIED_OPERATOR_FILE_REPORT.md` (this file) |

## 3. Unified file contents

- **`unified_version: 1`** plus the four family subtrees, each matching the current split file’s logical content (doctor rules, shade markers/routing table, argen contact mode).
- **Top-of-file comments** (YAML `#` lines): save/restart warning; pointer to this file as the primary edit surface; LLM workflow (full-file copy, full-file reply, schema bounds, no extra top-level keys); reference to `business_rule_schemas.py`.

Comments are ignored by `yaml.safe_load`; validation uses the same rules as before.

## 4. Loader behavior

Unchanged precedence from the dual-read pass:

| Condition | Result |
|-----------|--------|
| `case_creator_rules.yaml` / `.yml` present and valid | `rules_load_source=unified`, `effective_config` from normalized unified document |
| Unified file absent | `rules_load_source=split`, per-family files as today |
| Unified present but unreadable or invalid | `rules_load_source=split`, `unified_file_path` + `unified_validation_errors` set, warnings include fallback summary |

With the new seed file in repo **`v1`**, default **source** discovery now loads **unified** for equivalent effective config to the prior split-only baseline.

## 5. Observability

- **Logs** (`logging` logger `infrastructure.config.business_rule_loader`):
  - **INFO:** `load_source=split (no unified file in …)` or `load_source=unified path=…`
  - **WARNING:** unified unreadable or invalid, explicitly `load_source=split (fallback)` with error detail / count
- **Preview** fields (existing): `rules_load_source`, `unified_file_path`, `unified_validation_errors`, `warnings` — suitable for any UI that already surfaces `BusinessRuleConfigPreview`.

Runtime caches still call `load_business_rule_config_preview()` behind `lru_cache`; each distinct cache may log **once per process** on first load.

## 6. Validation performed

- `python3 -m unittest tests.test_unified_business_rules_config tests.test_business_rule_loader_dual_read -v` — all passed.
- Seeded file: `yaml.safe_load` + `validate_unified_business_rules_config` succeeds; effective config matches a **split-only** temporary directory copy of the four YAMLs.

## 7. Production safety

- **No domain or schema semantics** were broadened; only a new on-disk document and logging were added.
- **Equivalence:** unified content matches split baseline normalization, so **rule behavior** is unchanged when operators do not edit anything.
- **Fallback** remains if operators break the unified file; split files stay as the safety net.
- **No large UI** was added.

## 8. Risks or limitations

- **Dual maintenance:** Until split files are retired, operators could edit split files and forget the unified file (unified still wins when valid). Runbooks should state: **edit `case_creator_rules.yaml` first**; keep split files in sync if still editing them during transition.
- **Four INFO lines** possible on cold start (separate `lru_cache` instances per runtime helper) — acceptable; tune log level if noisy.
- **Comment drift:** LLM edits might drop comments; behavior is unaffected, only readability.

## 9. Recommended next pass

- **Documentation / operator README:** single place stating unified-first workflow and fallback behavior.
- **Optional deprecation path:** later, detect divergence between unified and split (hash or warning) or retire split files once confidence is high.
- **Optional UI:** one line in an existing settings/diagnostics screen showing `rules_load_source` (no new heavy workflow).

---

## Final chat summary

1. **Yes** — `business_rules/v1/case_creator_rules.yaml` exists and is seeded from the current split-family baseline.
2. **Yes** — with comments and full four-family content, it is the intended **one-page** edit surface for beginners; split files remain for fallback only.
3. **Yes** — invalid/missing unified still uses split files; tests and logging cover fallback.
4. **Safest next pass** — update operator/docs to unified-first, then (when ready) optional divergence warnings or phased removal of duplicate split edits.
