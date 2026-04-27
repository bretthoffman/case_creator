# CASE CREATOR BASELINE YAML SEEDING REPORT

## 1. Summary of changes

This pass **documented and seeded baseline behavior** for the four already-exposed live YAML families (`doctor_overrides`, `shade_overrides`, `routing_overrides`, `argen_modes`) so the editable files reflect **real defaults** and **where code still owns policy**.

- **Routing:** explicit **baseline family → destination_key** rows were added to `routing_overrides.yaml`, matching `routing_override_runtime.BASELINE_FAMILY_DESTINATION_MAP`. Runtime behavior is unchanged (values equal prior implicit defaults).
- **Shade / Argen modes:** markers and mode were **already** aligned with code; comments now **point to the authoritative code constants** and describe fallback semantics.
- **Doctor:** **no enabled Abby (or similar) rule was added**—built-in Abby Dew and VD Brier Creek behavior is **material- and branch-dependent** inside `template_utils.select_template`, while the live doctor YAML layer applies a **single** `template_override_key` **after** that function and would **flatten** those branches. Instead, the file now **documents** built-in behavior and includes a **disabled** example rule for copy/paste only.

No new config families were exposed, and no template precedence, scanner, manual-review, naming, UI, or settings code paths were modified.

## 2. Files modified

| File |
|------|
| `business_rules/v1/doctor_overrides.yaml` |
| `business_rules/v1/shade_overrides.yaml` |
| `business_rules/v1/routing_overrides.yaml` |
| `business_rules/v1/argen_modes.yaml` |
| `CASE_CREATOR_BASELINE_YAML_SEEDING_REPORT.md` (this file) |

## 3. Baseline behaviors found

### Doctor-related (template selection — **code-owned today**)

| Behavior | Location | Notes |
|----------|----------|--------|
| Abby + Dew substring match | `domain/rules/doctor_rules.is_abby_dew` | Drives `is_abby` branches in `template_utils.select_template` (e.g. `ai_adzir` vs `ai_envision` by material). |
| VD Brier Creek + last-name list | `domain/rules/doctor_rules.is_vd_brier_creek` | Drives `is_vd_serbia` template branches (e.g. `ai_*_model` paths). |
| Signature doctor list | `domain/rules/doctor_rules.is_signature_doctor` | Excel-backed; not the doctor YAML override family. |

**Live YAML doctor layer:** `resolve_doctor_template_override_key` in `infrastructure/config/doctor_override_runtime.py` — **only** `template_override_key`; applied in `domain/decisions/template_selector.py` **after** `select_template`.

### Shade (live YAML + code fallback)

| Behavior | Location |
|----------|----------|
| Default non-Argen markers `C3`, `A4` | `domain/rules/template_rules.NON_ARGEN_SHADE_MARKERS` |
| Effective marker set | `infrastructure/config/shade_override_runtime.resolve_non_argen_shade_markers` |

### Routing (live YAML + code baseline)

| family_key | Baseline destination_key | Source |
|------------|-------------------------|--------|
| `argen` | `argen` | `routing_override_runtime.BASELINE_FAMILY_DESTINATION_MAP` |
| `study` | `1_9` | same |
| `anterior` | `1_9` | same |
| `ai` | `1_9` | same |

### Argen modes (live YAML + code baseline)

| Field | Baseline | Source |
|-------|----------|--------|
| `contact_model_mode` | `legacy_default` | `argen_modes_runtime.BASELINE_CONTACT_MODEL_MODE` → passthrough in `template_rules.effective_argen_hint_route` |

## 4. YAML seeding decisions

### `doctor_overrides.yaml`

- **Removed** the misleading comment example that suggested enabling Abby → a single template key (that would **break** the material split).
- **Added** comments mapping built-in doctor behavior to `template_utils` / `doctor_rules`.
- **Added** one **`enabled: false`** rule (`example_single_key_doctor`) so beginners see valid schema **without** changing runtime.

### `shade_overrides.yaml`

- **Kept** `non_argen_shade_markers: [C3, A4]` (already matched code).
- **Added** comment cross-reference to `NON_ARGEN_SHADE_MARKERS` and invalid/empty fallback behavior.

### `routing_overrides.yaml`

- **Seeded** `template_family_route_overrides` with the four baseline rows matching `BASELINE_FAMILY_DESTINATION_MAP`.
- **Added** comment that this mirrors the runtime module baseline.

### `argen_modes.yaml`

- **Kept** `contact_model_mode: legacy_default`.
- **Added** short descriptions of each allowed mode and a pointer to `effective_argen_hint_route`.

## 5. Runtime compatibility strategy

- **No processor or loader code changes** were required.
- **Routing:** Overrides are applied only when `family_key` matches; seeded `destination_key` values **equal** the previous baseline from `BASELINE_FAMILY_DESTINATION_MAP`, so **no double-application** and no drift.
- **Shade / Argen:** Values unchanged; comments only clarify parity with code.
- **Doctor:** Only **disabled** rules were added; `resolve_doctor_template_override_key` skips `enabled: false`, so behavior matches an empty enabled rule set. **Abby Dew** was explicitly verified to still resolve to **material-dependent** templates via `select_template_path` (no YAML override).

## 6. Validation performed

- Loaded preview with `CASE_CREATOR_BUSINESS_RULES_DIR` pointing at `business_rules/v1`: **no validation errors** for any family.
- **Shade:** `resolve_non_argen_shade_markers(NON_ARGEN_SHADE_MARKERS) == ('C3', 'A4')`.
- **Routing:** `resolve_destination_key` for representative `argen_*`, `ai_*`, `*_study`, `*_anterior` template names returns **`argen`** vs **`1_9`** as before.
- **Argen modes:** `resolve_contact_model_mode() == 'legacy_default'`.
- **Doctor:** `resolve_doctor_template_override_key('Abby Dew') is None` with seeded file.
- **Abby material split:** `select_template_path` still selects `ai_adzir` vs `ai_envision` for synthetic Abby cases differing only by material / hint route.
- **Imports:** Core modules import cleanly (no new circular dependencies).

## 7. Risks or limitations

- **Doctor family remains mostly code-owned** for Abby, VD Brier Creek, and signature logic; YAML is for **additional** single-key overrides only. Editors must not “copy Abby” into an enabled rule without understanding the material split.
- **Routing** overrides are still **narrow** (destination keys only); labels and paths are unchanged.
- **Shade `rules[]`** remain non-live per prior passes.
- If **duplicate `family_key` rows** are added later, **first match wins**—documented in YAML header.

## 8. Recommended next pass

Safest next step: **optional UI or log surfacing** of “effective business rule preview” (which YAML file loaded, warnings, first-line effective values) **without** expanding live families—improves trust in seeded baselines.

Alternatively, a **docs-only** pass: link from `docs/reports/` to `business_rules/v1/*.yaml` as the operational source of truth for the four families.

## Final chat summary

1. **Seeded / clarified:** explicit **routing** baseline map in YAML; **shade** and **argen** baselines confirmed and documented; **doctor** file documents built-in rules and adds a **disabled** example only.
2. **Files with real baseline examples:** `routing_overrides.yaml` (live baseline rows), `shade_overrides.yaml`, `argen_modes.yaml`, `doctor_overrides.yaml` (disabled example + narrative).
3. **Partly code-owned:** **doctor** (Abby, VD Brier Creek, signature), and all **template precedence** / branch logic outside the narrow YAML surfaces.
4. **Safest next pass:** diagnostics surfacing effective loaded config, or documentation cross-links—no new live families.
