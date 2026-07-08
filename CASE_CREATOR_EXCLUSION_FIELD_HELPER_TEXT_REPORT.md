# CASE CREATOR EXCLUSION FIELD HELPER TEXT REPORT

> Beginner-editing polish for the two designer-exclusion inputs. Added short helper/example text at
> each field and aligned the parser so the displayed comma-separated format is **truthful**.
>
> **No live routing, `process_case`, zip, template-selection, or updater code was changed.** The
> only behavioral change is that the two existing YAML fields now *also* accept a comma-separated
> line (in addition to a YAML list). **Full test suite: 90 tests, OK.**

---

## 1. Summary of changes

- **Editing surface:** the app has no dedicated UI widgets for the two exclusion lists — editing is
  done via **Settings → "Open Rules Folder"**, which opens `case_creator_rules.yaml` for direct
  editing (the established design; there is no inline rules editor). So the "input field" a beginner
  uses is the YAML entry itself, and the helper text lives right at each field.
- **Helper/example text** added at both fields (YAML comments) and mirrored in the README and the
  rules-edit prompt:
  - doctor → `delivery_modes.designer_doctor_names` — Example `Jane Doe`; Multiple
    `Jane Doe, John Smith, Pat Lee`
  - shade → `shade_overrides.non_argen_shade_markers` — Example `C3`; Multiple `C3, A4, A3.5`
  - (Neutral doctor names were chosen over the literal "Abby Dew / VD Brier Creek" from the brief,
    to honor the "do not reintroduce Abby/VD language" constraint — confirmed with the requester.)
- **Parser alignment:** both fields now accept a **comma-separated string** as well as a YAML list.
  Values are split on commas, each item is trimmed, and empty items are dropped. The effective
  config remains a **list**, so nothing downstream changes.
- Hardened the `non_argen_shade_markers` normalizer against a latent crash on already-invalid input
  (now fails gracefully, matching the `designer_doctor_names` normalizer).

The examples shown are truthful: typing `designer_doctor_names: Jane Doe, John Smith, Pat Lee` or
`non_argen_shade_markers: C3, A4, A3.5` in the YAML now parses exactly as displayed.

---

## 2. Files modified

**Parser (schema validators)**
- `infrastructure/config/business_rule_schemas.py`
  - New shared helper `_coerce_str_list()` — comma-separated string → trimmed, de-empty list;
    lists and other types passed through unchanged.
  - `validate_delivery_modes` — coerce `designer_doctor_names` (string or list); updated error text.
  - `validate_shade_overrides` — coerce `non_argen_shade_markers` (string or list); updated error
    text; hardened the normalizer comprehension to skip non-strings (no crash on invalid input).

**Canonical config + seed (helper text at the fields)**
- `business_rules/v1/case_creator_rules.yaml` — added Example/Multiple/comma-line helper comments
  directly above `non_argen_shade_markers` and `designer_doctor_names`. Field values/structure
  unchanged (still lists).
- `business_rules_seed/v1/case_creator_rules.yaml` — re-synced (byte-parity kept).

**Helper docs**
- `business_rules/v1/README.md` — "How to send cases to the designer" now shows the comma-line and
  YAML-list forms and the Example/Multiple helper lines for both fields (neutral doctor names).
- `business_rules/v1/CASE_CREATOR_RULES_EDIT_PROMPT.md` — `shade_overrides` and `delivery_modes`
  sections document the comma-or-list entry format with the same Example/Multiple text.

**Tests**
- `tests/test_exclusion_field_csv_entry.py` **(new)** — comma entry for both fields (single,
  multiple, trimming, empties, list-still-works), unified-config acceptance, and end-to-end live
  resolution from a comma-entry YAML file.
- `tests/test_delivery_modes_runtime.py` — the old "string is rejected" test became
  "string is accepted and coerced" (`test_names_accept_comma_separated_string`).

---

## 3. UI helper text added

At each field in `case_creator_rules.yaml` (the surface opened by "Open Rules Folder"):

```yaml
  # Shades that send a case to the DESIGNER (Send to 1.9, unzipped). Everything else is outsource.
  # Enter as a comma-separated line OR a YAML list; spaces around commas are ignored.
  #   Example:  C3
  #   Multiple: C3, A4, A3.5
  # Comma line:  non_argen_shade_markers: C3, A4, A3.5
  non_argen_shade_markers:
  - C3
  - A4
```

```yaml
  # LIVE: doctors whose cases go to the DESIGNER (Send to 1.9, unzipped) instead of the default
  # OUTSOURCE (Send to AI, zipped). Case-insensitive substring match; empty = everyone outsource.
  # Enter as a comma-separated line OR a YAML list; spaces around commas are ignored.
  #   Example:  Jane Doe
  #   Multiple: Jane Doe, John Smith, Pat Lee
  # Comma line:  designer_doctor_names: Jane Doe, John Smith, Pat Lee
  designer_doctor_names: []
```

The README and rules-edit prompt carry the same Example/Multiple text plus both entry forms.

---

## 4. Parsing / input behavior alignment

`_coerce_str_list(value)` runs at validation, before the existing list checks:

- **Comma-separated string** → `split(",")`, `strip()` each, drop empties.
  `"C3, A4 , , A3.5"` → `["C3", "A4", "A3.5"]`.
- **YAML list** → unchanged (still fully supported).
- **Empty string** → `[]` (same as an empty list / default).
- **Any other type** (int, dict, list with non-strings) → passed through, then rejected by the
  existing "must be a list of non-empty strings or a comma-separated string" validation.

The normalized/effective config is always a **list**, so the live resolvers
(`resolve_designer_doctor_names`, `resolve_non_argen_shade_markers`) and delivery routing are
unchanged: doctor matching stays case-insensitive substring; shade markers are still uppercased and
compared as before. No new config family, no YAML structure change, no special syntax beyond commas.

---

## 5. Validation performed

Automated (`tests/test_exclusion_field_csv_entry.py` + updated runtime test):

- ✅ Helper/example text present at both fields (YAML comments + README + prompt).
- ✅ Single value works — doctor `Jane Doe`; shade `C3`.
- ✅ Multiple comma-separated values work — exactly the displayed examples
  (`Jane Doe, John Smith, Pat Lee`; `C3, A4, A3.5`).
- ✅ Spaces around commas/entries trimmed; empty entries dropped.
- ✅ YAML-list entry still supported; effective config stays a list.
- ✅ Invalid input still rejected and bounded (non-string list items → invalid, no crash).
- ✅ End-to-end: a comma-entry YAML file resolves through the live resolvers to the same values
  (shade markers uppercased; `is_designer_doctor` substring match intact).
- ✅ Canonical loads as `unified`, `has_errors=False`; canonical ↔ seed byte parity verified.
- ✅ Full suite: `Ran 90 tests ... OK`. No live routing behavior changed except through the same
  existing YAML fields.

---

## 6. Remaining risks or limitations

1. **YAML gotcha for values containing a comma.** A doctor/shade value that itself contains a comma
   can't be expressed on a comma-separated line (it would split). Such a value can still be entered
   via the YAML-list form. Practical shade/doctor values don't contain commas, so this is a
   non-issue in practice; the helper text steers users to the simple case.
2. **No dedicated UI widget.** Per the app's design, the exclusion inputs are edited in the YAML
   file (via "Open Rules Folder"), not in a Settings text box. Adding real Settings fields would
   require write-back to the unified YAML (comment-preserving round-trip) — intentionally out of
   scope for this focused pass.
3. **Comment-only YAML edits.** The helper text is YAML comments; a future comment-stripping
   round-trip writer (if ever added) would need to preserve them. None exists today.

---

## 7. Recommended next step

- Optional: add real Settings text fields for the two exclusion lists (pre-filled from the live
  config, saved back via a comment-preserving writer such as `ruamel.yaml`) if inline editing is
  desired over the "Open Rules Folder" workflow. This is a larger UI + persistence change and was
  deliberately not done here.
- Otherwise no follow-up required: the beginner entry format is now simple, truthful, and covered by
  tests.
