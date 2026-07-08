# CASE CREATOR CANONICAL RULES CLEANUP REPORT

> Focused cleanup of the user-facing canonical YAML and helper docs. **No live routing,
> `process_case`, zip, or template-selection code was changed.** The stale Abby/VD/example
> `doctor_overrides` rules are removed from the editable config, and the docs now teach only the
> outsource/designer model.
>
> **Full test suite: 77 tests, OK.**

---

## 1. Summary of changes

- Emptied `doctor_overrides.rules` in the canonical unified YAML (`rules: []`), removing the stale
  `abby_dew_multi_outcome`, `vd_brier_creek_multi_outcome`, and `example_single_key_doctor`
  entries. `doctor_overrides` stays structurally present (bounded default) but is clearly
  non-authoritative and empty.
- Synced the packaged seed to match (byte-parity preserved).
- Updated the test fixture (`unified_business_rules_baseline.yaml`) to mirror the cleaned canonical
  (its documented job), and conservatively updated the three tests that compared the canonical to
  the frozen split archive / old baseline.
- Cleaned the helper docs (`README.md`, `CASE_CREATOR_RULES_EDIT_PROMPT.md`) so they teach only:
  default = outsource; excluded doctors → designer; excluded shades → designer. Removed remaining
  Abby/VD "special exception" language and stale doctor-overrides examples; marked the `abby_dew` /
  `vd_brier_creek` predicates as retired/legacy.

No behavior changed: `doctor_overrides` outcomes are env-gated (`CASE_CREATOR_DOCTOR_OUTCOMES_LIVE`,
off by default) and already had no effect on delivery after the live reroute, so emptying them does
not alter runtime template selection in the default configuration.

---

## 2. Files modified

**Canonical config + seed**
- `business_rules/v1/case_creator_rules.yaml` — `doctor_overrides.rules` → `[]`; refreshed the
  explanatory comment. All other sections unchanged.
- `business_rules_seed/v1/case_creator_rules.yaml` — re-synced via
  `scripts/sync_unified_config_seed.py` (byte-identical to canonical).

**Helper docs**
- `business_rules/v1/README.md` — `doctor_overrides` subsection now states it is empty by default
  and rarely needed (template-only, never delivery).
- `business_rules/v1/CASE_CREATOR_RULES_EDIT_PROMPT.md` — removed "existing Abby/VD rules" language;
  marked `abby_dew` / `vd_brier_creek` predicates as retired/legacy (do not use for new rules);
  replaced the `["abby","dew"]` match example with `["jane","doe"]`; annotated the two
  `doctor_overrides` examples as advanced/template-only.

**Tests (conservative updates for the intentionally-cleaned family)**
- `tests/fixtures/unified_business_rules_baseline.yaml` — `doctor_overrides.rules` → `[]` (fixture
  is a documented canonical mirror).
- `tests/test_business_rule_loader_dual_read.py` — `_archived_split_merged_document()` now sets
  `doctor_overrides` to the schema default so archive-derived configs match the cleaned canonical.
- `tests/test_unified_business_rules_config.py` — `test_in_memory_split_merge_matches_preview`
  overrides `doctor_overrides` to the default before comparing to the canonical preview.
- `tests/test_unified_retirement_equivalence.py` — same archive-merge override; the obsolete
  "Abby Dew → ai_adzir" assertion was flipped to assert **no** override is produced from the
  cleaned canonical (even with outcomes evaluation forced on), which is the correct new expectation.

---

## 3. Canonical YAML cleanup

Before → after for `doctor_overrides`:

```yaml
# before: three rules (abby_dew_multi_outcome, vd_brier_creek_multi_outcome, example_single_key_doctor)
doctor_overrides:
  version: 1
  enabled: true
  rules:
  - id: abby_dew_multi_outcome
    ...
```

```yaml
# after: bounded, empty, clearly non-authoritative
# doctor_overrides does NOT control delivery (outsource vs designer). It is an advanced,
# template-only override layer and is intentionally left EMPTY for the current business model.
# To send a doctor's cases to the designer, use delivery_modes.designer_doctor_names (bottom of file).
doctor_overrides:
  version: 1
  enabled: true
  rules: []
```

Unchanged (still the real, current model):
- `delivery_modes.designer_doctor_names` — live doctor-based designer exclusion (empty list).
- `shade_overrides.non_argen_shade_markers` — live shade-based designer exclusion (`C3`, `A4`).
- `routing_overrides`, `argen_modes` — retained as legacy/compatibility, still schema-valid.
- The delivery-model header comment.

The editable YAML now presents the real current model: two disqualifier lists drive designer
delivery; everything else is outsource.

---

## 4. Helper-doc cleanup

- **README.md** — already outsource/designer-first and Serbia-free; the `doctor_overrides`
  subsection now says it is **empty by default** and rarely needed. No doctor-overrides examples
  imply the old process.
- **CASE_CREATOR_RULES_EDIT_PROMPT.md**:
  - `doctor_overrides` section: "Important" note now states it is empty by default and only for
    forcing a specific template; removed "do not rewrite existing Abby/VD rules" language.
  - `abby_dew` / `vd_brier_creek` predicates documented as **legacy/retired** — do not use for new
    rules; prefer `contains_all` / `contains_any`.
  - Match example changed from `["abby","dew"]` to `["jane","doe"]`.
  - The two `doctor_overrides` examples (Example 4 template rule, Example 8 multi-outcome) are
    annotated as advanced/template-only and redirect delivery requests to
    `delivery_modes.designer_doctor_names`.
  - The only remaining Abby/VD/Serbia mentions are explicit **"retired / no longer live"** notes.

---

## 5. Validation / tests performed

- Canonical loads as `rules_load_source="unified"`, `has_errors=False`, with
  `doctor_overrides = {version:1, enabled:true, rules:[]}` and
  `delivery_modes.designer_doctor_names = []`.
- Canonical ↔ seed **byte parity** verified (`cmp`), enforced by
  `tests.test_unified_canonical_seed_parity`.
- **Full suite: `Ran 77 tests ... OK`** — including the four canonical/archive/fixture parity tests
  updated in this pass.
- Grep confirms no `doctor_overrides` rule content remains in the canonical, and the only Abby/VD
  strings in the docs are retired/legacy notes.

---

## 6. Remaining risks or limitations

1. **Frozen split archive is unchanged.** `business_rules/archive/v1_split_backup/` still contains
   the old `doctor_overrides.yaml` (abby/vd). Tests now override that family to the current default
   when comparing to canonical; the archive itself is left as a historical artifact (not fabricated).
2. **Legacy predicates still schema-valid.** `abby_dew` / `vd_brier_creek` remain accepted by the
   validator (`ALLOWED_DOCTOR_MATCH_PREDICATES`) so old/hand-edited files won't be rejected. They
   are documented as retired. Removing them from the schema is a code change and out of scope here.
3. **Dormant code untouched (intentional).** No dormant-code deletion was performed this pass, per
   instructions. `doctor_overrides` template-override plumbing, `destination_selector`, and the
   `routing_rules` Serbia/zip helpers remain present but uninvoked for delivery.
4. **Existing installs.** A previously-seeded external unified file (packaged/frozen installs) is
   never overwritten by the loader; those users keep their current `doctor_overrides` until the file
   is re-seeded or edited. New installs seed from the cleaned canonical.

---

## 7. Recommended next step

Optional, still conservative:
- Retire the legacy `abby_dew` / `vd_brier_creek` predicates from the schema (and the inline Abby/VD
  logic in `template_utils.select_template`) once it is confirmed template selection no longer needs
  them — a small **code** pass, deliberately excluded here.
- Consider whether `routing_overrides` / `argen_modes` should also be trimmed from the editable YAML
  now that Argen is not the active delivery path (docs already label them legacy).
- If the business wants specific doctors delivered to the designer, populate
  `delivery_modes.designer_doctor_names`.
