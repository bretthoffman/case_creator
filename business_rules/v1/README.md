# Case Creator unified business rules (operator guide)

## The one file to edit in the repository

Edit **only** this file in the repo:

`business_rules/v1/case_creator_rules.yaml`

It is the **canonical** unified config: all four exposed rule families live in one YAML document. After changes, **save the file and restart the app** so the loader picks them up.

### What you should not edit in-repo for “second source”

- **`business_rules_seed/v1/case_creator_rules.yaml`** — This is a **copy** used as the **bundled default** for packaged builds and first-run seeding. It is refreshed from the canonical file by `scripts/sync_unified_config_seed.py` and by the Windows PyInstaller build script. Treat it as a **generated artifact**, not a second place to maintain rules by hand.

### Packaged installs (Windows)

On first run, the app may create:

`%LOCALAPPDATA%\CaseCreator\business_rules\v1\case_creator_rules.yaml`

by copying the **bundled** seed. After that, edit **that external file** for that machine (it persists across app updates). The repo file above is what developers ship as the default template via the bundle.

---

## What you can change (plain English)

The file has four main sections under `unified_version: 1`:

### 1. `doctor_overrides`

Controls **doctor-name-based template overrides** (which template folder key is used when a rule matches).

- **Simple rules** — Match on doctor name text (`contains_any` / `contains_all`) and set a single `action.template_override_key` from the **approved list** in the schema.
- **Richer rules (Abby / VD style)** — Use `match.predicate` (`abby_dew`, `vd_brier_creek`) with `when` / `outcomes[]` for conditional template keys.  
  **Note:** Multi-outcome evaluation may still be gated by the existing **feature flag** in your environment; the YAML can contain those rules even when the flag is off.

You **cannot** put raw filesystem paths here — only bounded keys the app knows how to resolve.

### 2. `shade_overrides`

- **`non_argen_shade_markers`** — List of shade **code substrings** (e.g. `C3`, `A4`) used to detect “non-Argen” shade cases for marker logic.  
- **`rules`** — Reserved/limited in current phases; follow schema comments in-file.

### 3. `routing_overrides`

- **`template_family_route_overrides`** — Maps **template family** (`argen`, `ai`, `study`, `anterior`) to a **destination key** the app understands (`argen` vs `1_9`).  
  First matching entry wins for that family.

### 4. `argen_modes`

- **`contact_model_mode`** — `"off"` or `"on"` (quote in YAML to avoid boolean quirks). Controls whether contact-model Argen templates are used where applicable.

---

## What is not meant to be edited here

These stay **internal** or live in code/other layers — do not try to encode them as ad-hoc YAML:

- Raw **filesystem paths** to templates or cases  
- **Scanner heuristics** and low-level detection  
- **Unsupported material / manual-review** engine internals  
- Anything outside the **documented keys** in `infrastructure/config/business_rule_schemas.py`

If the validator rejects a key, it is not supported in this file.

---

## Schema and safety

- Top-level keys allowed: `unified_version` (required, `1`), optional envelope `enabled`, and the four family objects.  
- Unknown keys are rejected.  
- Invalid YAML or invalid schema → app falls back to **safe built-in defaults** with diagnostics (do not rely on silent “partial” apply).

Full rules: see `infrastructure/config/business_rule_schemas.py`.

---

## Examples (patterns only — adjust IDs and text)

### Example A — Simple doctor rule

```yaml
doctor_overrides:
  version: 1
  enabled: true
  rules:
    - id: my_dental_group_ai_envision
      enabled: true
      match:
        contains_all: ["Lakeside", "Dental"]
      action:
        template_override_key: ai_envision
```

Use only **known** `template_override_key` values (see comments in `case_creator_rules.yaml` or the schema).

### Example B — Turn Argen contact model on

```yaml
argen_modes:
  version: 1
  enabled: true
  contact_model_mode: "on"
```

### Example C — Add a non-Argen shade marker

```yaml
shade_overrides:
  version: 1
  enabled: true
  non_argen_shade_markers:
    - C3
    - A4
    - ZZ1
  rules: []
```

### Example D — Change routing for the `ai` family to Argen destination

```yaml
routing_overrides:
  version: 1
  enabled: true
  template_family_route_overrides:
    - family_key: argen
      destination_key: argen
    - family_key: ai
      destination_key: argen
    # ... other families as needed
```

(Only use allowed `family_key` / `destination_key` pairs; see existing rows in your file.)

---

## After editing

1. Save `case_creator_rules.yaml`.  
2. **Restart** Case Creator.  
3. If you maintain the repo and care about packaged defaults: run  
   `python3 scripts/sync_unified_config_seed.py`  
   (or build with the Windows script, which refreshes the seed automatically).
