# CASE CREATOR NON OUTSOURCE SHADES RENAME REPORT

## 1. Summary of changes

This was a bounded canonical-YAML + schema/runtime rename/alignment pass performed right before
release. The live delivery model was **not** changed. The only behavioral change is a **field
rename** for the shade-based designer-exclusion list:

```
shade_overrides.non_argen_shade_markers   ->   shade_overrides.non_outsource_shades
```

The rename is compatibility-minded: the validator accepts **both** names at input, but the
canonical shipped YAML, the normalized/effective config, and all beginner-facing docs use only the
new name `non_outsource_shades`. Legacy files (and existing user files) that still use
`non_argen_shade_markers` continue to work unchanged via a validated alias.

The shade-exclusion block was also moved to the requested near-bottom position: it is now the
**second-from-bottom** family, sitting directly **above** `delivery_modes` / `designer_doctor_names`.

The live delivery model is unchanged:

- default = outsource (Send to AI, zipped)
- designer = Send to 1.9, unzipped (the exception)
- doctor-based designer exclusions: `delivery_modes.designer_doctor_names`
- shade-based designer exclusions: `shade_overrides.non_outsource_shades` (renamed field)

## 2. Files modified

Schema / runtime / code (live behavior preserved):

- `infrastructure/config/business_rule_schemas.py` — default shade shape now emits
  `non_outsource_shades`; `validate_shade_overrides` accepts the new name, accepts the legacy
  `non_argen_shade_markers` as an alias, and normalizes to the single canonical key
  `non_outsource_shades`. Docstring reference updated.
- `infrastructure/config/shade_override_runtime.py` — resolver reads the normalized
  `non_outsource_shades` key; docstring updated. Function name `resolve_non_argen_shade_markers`
  intentionally retained for call-site stability.
- `infrastructure/config/delivery_mode_runtime.py` — cross-reference comment updated to the new
  field name.
- `domain/decisions/delivery_mode_selector.py` — cross-reference comment updated.
- `case_processor_final_clean.py` — live-delivery comment updated.

Canonical / seed config:

- `business_rules/v1/case_creator_rules.yaml` — field renamed, block moved second-from-bottom,
  helper/example/comment lines updated.
- `business_rules_seed/v1/case_creator_rules.yaml` — identical to canonical (parity preserved).

Beginner-facing docs:

- `business_rules/v1/README.md` — the three shade-field references now teach `non_outsource_shades`.
- `business_rules/v1/CASE_CREATOR_RULES_EDIT_PROMPT.md` — all 13 field-name references renamed;
  the "Typical top-level shape" example reordered so the shade block sits directly above
  `delivery_modes`. (The `non_argen_shade` *doctor when-condition* and the hyphenated prose
  "non-Argen shade" were intentionally left unchanged — they are different identifiers.)

Tests / fixtures:

- `tests/fixtures/unified_business_rules_baseline.yaml` — field renamed (done in prior work).
- `tests/test_exclusion_field_csv_entry.py` — inputs/reads use the new field name; help-text
  docstring updated. Runtime function name kept.
- `tests/test_unified_retirement_equivalence.py` — reads the normalized `non_outsource_shades`.
- `tests/test_business_rule_loader_dual_read.py` — reads the normalized `non_outsource_shades`
  (input in that case intentionally left as the legacy name, exercising the alias through the
  full loader path).
- `tests/test_non_outsource_shades_rename.py` — **new** focused proof test (see section 6).

Not modified (intentional):

- `business_rules/archive/v1_split_backup/shade_overrides.yaml` — frozen split backup; still uses
  the legacy name and is validated through the alias (parity preserved automatically).
- Historical `*_REPORT.md` / `docs/**` records — left as accurate records of prior passes.
- Code identifiers `resolve_non_argen_shade_markers`, `is_non_argen_shade`,
  `NON_ARGEN_SHADE_MARKERS`, and the `non_argen_shade` when-condition — kept for stability.

## 3. YAML layout change

Final top-level ordering (both canonical and seed):

```
unified_version
doctor_overrides
routing_overrides
argen_modes
shade_overrides      # <- shade exclusion block, second-from-bottom
  non_outsource_shades: [C3, A4]
delivery_modes       # <- bottom
  designer_doctor_names: []
```

This satisfies the requested shape: the shade exclusion block is second-from-bottom, directly
above `delivery_modes` / `designer_doctor_names`.

## 4. Field rename and compatibility behavior

- **Preferred / canonical name:** `non_outsource_shades`.
- **Legacy alias (still accepted at input):** `non_argen_shade_markers`.
- **Normalization:** the validator always emits the single canonical key `non_outsource_shades` in
  the normalized/effective config, regardless of which input name was used.
- **Precedence rule (documented and tested):** if **both** keys are present in one file, the new
  name `non_outsource_shades` wins and the legacy `non_argen_shade_markers` is ignored, with a
  warning. Using the legacy name alone also emits a "rename it" warning.

Shipped canonical YAML and helper docs use only `non_outsource_shades`.

## 5. Runtime/schema impact

- `default_shade_overrides()` now returns `non_outsource_shades: ["C3", "A4"]`.
- `validate_shade_overrides()` resolves the field with the precedence above and normalizes to
  `non_outsource_shades`. Comma-string and YAML-list entry formats are unchanged.
- `resolve_non_argen_shade_markers()` (name retained) reads `shade_overrides.non_outsource_shades`
  from the effective config; the defaults fallback `("C3", "A4")` is unchanged.
- `resolve_delivery_mode()` is unchanged: shade exclusions still flow through
  `template_rules.is_non_argen_shade` -> designer.
- Loading the canonical YAML yields `rules_load_source = unified`, no errors, no warnings, and
  `shade_overrides.non_outsource_shades = ['C3', 'A4']`.

## 6. Validation/tests performed

Full suite: **105 tests, all passing** (`python3 -m unittest discover -s tests`).

New focused test `tests/test_non_outsource_shades_rename.py` proves:

1. the new field name validates and normalizes to `non_outsource_shades`;
2. the legacy `non_argen_shade_markers` alias is still accepted and normalized to the new key
   (with a legacy warning);
3. when both are present, the new name wins (with a precedence warning);
4. `default_shade_overrides()` uses the new key;
5. the canonical **and** seed YAML use only the new field name, second-from-bottom directly above
   `delivery_modes`, and remain byte-identical;
6. the **live** `resolve_delivery_mode` sends a matching shade to `designer` via the new field
   name **and** via the legacy alias;
7. `README.md` and `CASE_CREATOR_RULES_EDIT_PROMPT.md` teach only the new field name.

Manual load check: canonical YAML loads via the unified path with no errors and no warnings.

## 7. Remaining risks or limitations

- **Low risk.** The change is a rename plus a validated alias; live routing logic and the
  outsource/designer model are untouched.
- The runtime function name `resolve_non_argen_shade_markers` and the `NON_ARGEN_SHADE_MARKERS`
  default constant still carry the old name. This is intentional (call-site stability) and does not
  affect behavior or the user-facing YAML/docs. A future cosmetic pass could rename these code
  identifiers if desired.
- The frozen archive file `business_rules/archive/v1_split_backup/shade_overrides.yaml` still uses
  the legacy name by design; it validates through the alias and keeps canonical/seed parity.
- Historical report/plan markdown files still reference the old field name as accurate records of
  past work and were intentionally not rewritten.

## 8. Recommended next release step

The codebase is ready for the final push/tag/build step. No updater/release logic was touched in
this pass. Recommended: commit these changes, then proceed with the normal tag/build. Because a
compatibility alias is in place, existing user files with `non_argen_shade_markers` will keep
working after the release; the alias can be removed in a later major version once files are known
to have migrated to `non_outsource_shades`.
