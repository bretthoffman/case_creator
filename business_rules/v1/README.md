# Case Creator Unified Rules Guide

This folder contains the canonical unified rules file used by Case Creator.

## The one file to edit

Edit this file in the repo:

`business_rules/v1/case_creator_rules.yaml`

After any change, **save** and **restart** the app.

---

## Destination vs label (important)

Case Creator separates:

1. **`destination_key`** (actual routing target)
   - `argen`
   - `"1_9"`

2. **`route_label_override_key`** (display/readback label)
   - `argen`
   - `designer`
   - `serbia`
   - `ai_designer`
   - `ai_serbia`

When you want “show **Send to Serbia** but still route to **1.9**”, use a bounded
**label override** (`route_label_override_key`), not a destination path change.

---

## What can be changed in `case_creator_rules.yaml`

## 1) doctor_overrides

Use doctor rules to choose template keys and/or bounded label override keys.

- **Simple doctor rules**
  - match doctor text (`contains_any`, `contains_all`) and set:
    - `action.template_override_key`
    - optional `action.route_label_override_key`

- **Richer Abby/VD-style rules**
  - predicate + `when` + `outcomes[]` for conditional template key selection.
  - keep to supported fields already in the schema.

## 2) shade_overrides

- Edit `non_argen_shade_markers` list.
- Keep marker values simple shade code strings.

## 3) routing_overrides

- Edit `template_family_route_overrides` list to map family -> destination key.
- Allowed family keys: `argen`, `study`, `anterior`, `ai`
- Allowed destination keys: `argen`, `"1_9"`

## 4) argen_modes

- Set `contact_model_mode` to `"off"` or `"on"`.
- Set `contact_model_design_field` to one of:
  - `"3Shape Automate"` (default/historical behavior)
  - `"No"`
- `contact_model_design_field` only affects modeless Argen templates:
  - `argen_modeless_adzir`
  - `argen_modeless_envision`

---

## What should NOT be changed here

Do not try to encode these in YAML:

- raw filesystem paths
- scanner heuristics
- unsupported material/manual-review engine internals
- template engine internals outside approved rule fields

If the schema rejects a field, it is not supported.

---

## Practical examples

### Example A — Add a simple doctor rule

```yaml
doctor_overrides:
  version: 1
  enabled: true
  rules:
    - id: dr_smith_simple
      enabled: true
      match:
        contains_all: ["smith", "dental"]
      action:
        template_override_key: ai_envision
```

### Example B — Show Serbia readback while destination remains 1.9

```yaml
doctor_overrides:
  version: 1
  enabled: true
  rules:
    - id: dr_casey_serbia_readback
      enabled: true
      match:
        contains_all: ["casey", "clinic"]
      action:
        route_label_override_key: serbia
```

This changes label/readback behavior only. Destination mapping still comes from template family routing.

### Example C — Turn contact model mode on

```yaml
argen_modes:
  version: 1
  enabled: true
  contact_model_mode: "on"
  contact_model_design_field: "No"
```

### Example D — Add a non-Argen shade marker

```yaml
shade_overrides:
  version: 1
  enabled: true
  non_argen_shade_markers:
    - C3
    - A4
    - A3.5
  rules: []
```

### Example E — Change routing for AI family

```yaml
routing_overrides:
  version: 1
  enabled: true
  template_family_route_overrides:
    - family_key: argen
      destination_key: argen
    - family_key: study
      destination_key: "1_9"
    - family_key: anterior
      destination_key: "1_9"
    - family_key: ai
      destination_key: "1_9"
```

---

## Quick safety checklist

1. Edit only `case_creator_rules.yaml`.
2. Keep keys bounded; do not invent fields.
3. Validate logically (destination vs label intent).
4. Save and restart.
