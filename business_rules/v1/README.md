# Case Creator Unified Rules Guide

This folder contains the canonical unified rules file used by Case Creator.

## The one file to edit

Edit this file in the repo:

`business_rules/v1/case_creator_rules.yaml`

After any change, **save** and **restart** the app.

---

## Delivery model (read this first)

Every case is delivered in one of two ways:

| Mode | When | Where it goes | Zipped? |
| --- | --- | --- | --- |
| **outsource** | **default — all cases** | **Send to AI** | **Yes (zipped)** |
| **designer** | **exception only** | **Send to 1.9** | **No (unzipped)** |

A case becomes **designer** only when a YAML disqualifier matches:

1. the **doctor name** is listed in `delivery_modes.designer_doctor_names`, **or**
2. the **shade** matches a marker in `shade_overrides.non_outsource_shades`.

Otherwise the case is **outsource**. `has_study` does **not** affect delivery mode.

> There is no "Send to Serbia" and no Abby/VD special delivery routing anymore. Those are retired
> as live delivery behavior. Delivery is decided **only** by the two lists above.

---

## How to send cases to the designer

You can enter values two ways — pick whichever is easier. Spaces around commas are ignored, and
empty entries are dropped.

- **Comma-separated line** (simplest):

  ```yaml
  designer_doctor_names: Jane Doe, John Smith, Pat Lee
  ```

- **YAML list** (one per line):

  ```yaml
  designer_doctor_names:
    - Jane Doe
    - John Smith
  ```

### By doctor — `delivery_modes.designer_doctor_names`

Case-insensitive name substrings. Any case whose doctor name contains one of these goes to the
designer (Send to 1.9, unzipped). Leave it empty to keep every doctor on outsource.

- **Example:** `Jane Doe`
- **Multiple:** `Jane Doe, John Smith, Pat Lee`

### By shade — `shade_overrides.non_outsource_shades`

Any case whose shade matches one of these markers goes to the designer. Use simple shade code
strings (e.g. `C3`, `A4`, `A3.5`, `B3`).

- **Example:** `C3`
- **Multiple:** `C3, A4, A3.5`

---

## Other sections (advanced / legacy — not the delivery authority)

These sections remain in the file for template selection and historical compatibility. **None of
them decides outsource vs designer delivery anymore** — only the two lists above do.

### `doctor_overrides`

**Empty by default** (`rules: []`), and most setups should leave it that way. It is an advanced
**template**-selection override only — it does **not** change where a case is delivered or whether
it is zipped. To route a doctor to the designer, use `delivery_modes.designer_doctor_names`, not
this section.

### `routing_overrides`

Legacy template-family → destination mapping. Retained for compatibility; not used to decide
outsource vs designer delivery.

### `argen_modes`

Legacy Argen contact-model settings that only affect the two `argen_modeless_*` templates.
Retained for compatibility; Argen is no longer the active delivery path.

---

## What should NOT be changed here

Do not try to encode these in YAML:

- raw filesystem paths
- scanner heuristics
- unsupported material/manual-review engine internals
- template engine internals outside approved rule fields

If the schema rejects a field, it is not supported.

---

## Quick safety checklist

1. Edit only `case_creator_rules.yaml`.
2. To change **delivery**, edit `delivery_modes.designer_doctor_names` (doctors) or
   `shade_overrides.non_outsource_shades` (shades).
3. Keep keys bounded; do not invent fields.
4. Save and restart.
