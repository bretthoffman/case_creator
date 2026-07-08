# CASE CREATOR DELIVERY MODES PHASE 1 REPORT

> Additive, **dormant** pass. `process_case`, destination selection, zip behavior, and template
> selection are **unchanged**. This pass only adds a bounded unified-config family plus a runtime
> resolver that nothing live consumes yet.

---

## 1. Summary of changes

Added a new bounded unified-config family, **`delivery_modes`**, whose only field is
`designer_doctor_names` — a list of doctor-name substrings that will (in the *next* pass) force a
case into **designer** mode instead of the default **outsource** mode.

- Family is wired through the same plumbing as the existing families (schema default + validator +
  unified-config registration + loader default preview).
- A new runtime resolver module exposes the normalized list and a pure, case-insensitive matching
  helper for the future live pass.
- Canonical unified YAML and the packaged seed both include the new family (byte-parity kept).
- Operator docs (README + rules-edit prompt) mention the family conservatively, flagged as dormant.
- Focused tests added; three pre-existing tests that hard-enumerate the family set were made
  resilient to a family that postdates the split archive.

Confirmed decisions honored this pass:
- "designer" = existing **Send to 1.9** path; "outsource" = existing **Send to AI** path
  (documented only; **not** wired yet).
- Shade-based designer disqualification **reuses** `shade_overrides.non_argen_shade_markers` and is
  **not** duplicated into `delivery_modes`.
- No new zip system, no template-selection change, no destination change in this pass.

**Full test suite: 69 tests, OK.**

---

## 2. Files modified

**Schema / loader (config plumbing)**
- `infrastructure/config/business_rule_schemas.py`
  - `SUPPORTED_FAMILIES` now includes `"delivery_modes"` (this auto-extends
    `ALLOWED_UNIFIED_TOP_LEVEL_KEYS`, which splats `*SUPPORTED_FAMILIES`).
  - `FAMILY_FILE_CANDIDATES` entry added for parity with other families.
  - New `default_delivery_modes()`.
  - New `validate_delivery_modes(...)`.
  - Registered `delivery_modes` in the `validators` and `effective` dicts of
    `validate_unified_business_rules_config`.
- `infrastructure/config/business_rule_loader.py`
  - `_schema_defaults_effective()` now includes `delivery_modes`.

**New runtime resolver**
- `infrastructure/config/delivery_mode_runtime.py` (new).

**Canonical config + seed**
- `business_rules/v1/case_creator_rules.yaml` — added `delivery_modes` section.
- `business_rules_seed/v1/case_creator_rules.yaml` — synced via
  `scripts/sync_unified_config_seed.py` (byte-identical to canonical).

**Operator docs (conservative)**
- `business_rules/v1/README.md` — new "5) delivery_modes" section, flagged dormant.
- `business_rules/v1/CASE_CREATOR_RULES_EDIT_PROMPT.md` — added `delivery_modes` to the allowed
  top-level keys, the typical-shape example, and a bounded SECTION (flagged dormant).

**Tests**
- `tests/test_delivery_modes_runtime.py` (new) — focused schema + resolver + helper tests.
- `tests/test_business_rule_loader_dual_read.py` — `_schema_defaults_effective()` now derives from
  `SUPPORTED_FAMILIES` (future-proof); `_archived_split_merged_document()` skips families with no
  archived split file.
- `tests/test_unified_retirement_equivalence.py` — archived-merge loop skips missing per-family
  files.
- `tests/test_unified_business_rules_config.py` — in-memory split-merge loop skips missing
  per-family files.

> The three test edits are intent-preserving: the `v1_split_backup` archive is a frozen snapshot
> from before `delivery_modes` existed, so there is legitimately no `delivery_modes.yaml` there.
> Omitting an absent family lets the unified validator fill it with its default, which matches the
> canonical `effective_config` (whose `delivery_modes` also equals the default).

---

## 3. New YAML family

Added to `business_rules/v1/case_creator_rules.yaml` (and the seed):

```yaml
delivery_modes:
  version: 1
  enabled: true
  # Doctor-name substrings that force a case into designer mode (Send to 1.9, unzipped)
  # instead of the default outsource mode (Send to AI, zipped). Case-insensitive substring
  # match. DORMANT until the live routing pass wires this in; empty = outsource for all.
  # Shade-based designer disqualification reuses shade_overrides.non_argen_shade_markers.
  designer_doctor_names: []
```

**Schema / validation bounds** (`validate_delivery_modes`):
- `version` must equal the schema version (`1`).
- `enabled` optional boolean (defaults `true`).
- `designer_doctor_names` must be a **list of non-empty strings** (or `[]`). Values are trimmed;
  invalid types/empties are rejected.
- No other keys are introduced. Unknown top-level keys remain rejected by the unified validator.
- `default_delivery_modes()` → `{"version": 1, "enabled": True, "designer_doctor_names": []}`.

---

## 4. Runtime resolver added

`infrastructure/config/delivery_mode_runtime.py`, following the exact pattern of
`shade_override_runtime.py` (`@lru_cache(maxsize=1)` preview + `clear_*_cache()` helper):

- `resolve_designer_doctor_names(default_names=()) -> Tuple[str, ...]`
  - Live read of `delivery_modes.designer_doctor_names` (validated config only).
  - Normalizes: strips, drops empties, de-duplicates case-insensitively, preserves order/casing.
  - Falls back to `default_names` (normally empty) on missing / invalid / disabled / error.
- `is_designer_doctor(doctor_name, designer_names=None) -> bool`
  - Pure, **case-insensitive substring** match (repo convention, cf.
    `doctor_policy_resolver._contains_any`).
  - When `designer_names` is `None`, reads live config; otherwise matches the provided list
    (hermetic for tests / future call sites).
- `clear_delivery_mode_cache()` — mirrors the other families' cache-clear helpers.

**Nothing calls these from live code yet** — the module is imported only by its own tests.

---

## 5. Validation / tests performed

New focused tests (`tests/test_delivery_modes_runtime.py`):
- **Valid default family** — `default_delivery_modes()` validates and round-trips.
- **Normalization** — whitespace trimmed; valid names normalized.
- **Invalid types rejected** — non-list `designer_doctor_names`; lists containing non-strings or
  empties; bad `version`; non-dict family.
- **Unified config accepts the new family** — present-and-valid → valid + normalized; omitted →
  filled with default; present-and-invalid → unified validation fails with a `delivery_modes:`
  error.
- **Runtime resolver** — returns normalized tuple (trim + case-insensitive de-dupe, order
  preserved); empty by default; disabled family falls back to defaults. (Uses the repo's
  `CASE_CREATOR_BUSINESS_RULES_DIR` + `clear_*_cache()` injection pattern.)
- **Matching helper** — case-insensitive substring match; empty inputs safe.

Regression coverage:
- Updated 3 pre-existing family-enumerating tests to tolerate the archive-less new family.
- **Full suite: `Ran 69 tests ... OK`.**
- Canonical loads as `rules_load_source="unified"` with `has_errors=False` and
  `effective_config["delivery_modes"] == default_delivery_modes()`.
- Canonical ↔ seed **byte parity** verified (`cmp`), enforced by
  `tests.test_unified_canonical_seed_parity`.

---

## 6. Why behavior is still dormant

- `process_case` ([case_processor_final_clean.py:250](case_processor_final_clean.py:250)) and its
  destination/zip block ([case_processor_final_clean.py:489-497](case_processor_final_clean.py:489))
  were **not touched**. Destination still comes from `select_destination` /
  `resolve_destination_key`, and zip still comes from `should_zip` /
  `should_zip_modeless_argen` — unchanged.
- Template selection (`select_template_path` / `select_template`) was **not touched**.
- No live module imports `delivery_mode_runtime` (verified by grep: only the schema/loader
  reference the `delivery_modes` *config key*; the resolver functions are referenced only by their
  tests).
- The new family's default is an **empty** `designer_doctor_names`, and even a populated list has no
  consumer yet, so runtime routing/zip output is identical to before this pass.

---

## 7. Recommended next pass

Wire the dormant resolver into the live path (the reroute described in the audit plan):

1. Add a small `resolve_delivery_mode(case_data) -> "outsource" | "designer"` helper that returns
   `designer` when **either**:
   - `is_designer_doctor(case_data["doctor"])` (new `delivery_mode_runtime`), **or**
   - `template_rules.is_non_argen_shade(case_data["shade"])` (existing live shade behavior),
   else `outsource`.
2. Replace the destination + zip seam at
   [case_processor_final_clean.py:489-497](case_processor_final_clean.py:489) with:
   - `designer` → `target_root = SEND_TO_1_9_PATH`, `do_zip = False` (unzipped, existing behavior).
   - `outsource` → `target_root = SEND_TO_AI_PATH`, `do_zip = True` (reuses `zip_case_folder` and
     the existing `if do_zip:` blocks).
3. Keep `select_template_path` and the two `if do_zip:` execution blocks unchanged.
4. Add end-to-end tests: default → zipped in `Send to AI`; designer-doctor → unzipped in
   `Send to 1.9`; designer-shade → unzipped; a former `has_study` case → outsource unless
   disqualified (proving `has_study` no longer decides mode).

Confirm before shipping Phase 3: that "send-to-designer side" is indeed the `Send to 1.9` folder
(one-line change otherwise), and that the `Send to AI` consumer accepts the `zip_case_folder` shape.
