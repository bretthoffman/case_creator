# CASE CREATOR ARGEN CONTACT MODE ON OFF REPORT

## 1. Summary of changes

- **`contact_model_mode`** is now a **two-value** live setting: **`off`** and **`on`** (replacing `legacy_default`, `always_with_contact_models`, `always_without_contact_models` in the editable surface).
- **Active behavior** is implemented **directly in `template_utils.select_template`**: after the anterior block, if mode is **`on`**, the case is a **non–study** **eligible Argen** case (`material_hint.route` ∈ `argen_adzir`, `argen_envision`, `modeless`), and material is Adzir vs not, the template is **`argen_modeless_adzir`** or **`argen_modeless_envision`**. **`off`** does not enter that branch; selection follows the existing `elif` chain (same practical behavior as former **`legacy_default`** passthrough).
- **`template_rules.effective_argen_hint_route`** is now a **no-op passthrough** of the normalized hint (legacy three-way rewriting removed from the live path). Hint-route rewriting is **not** used to drive contact-model templates.
- **Doctor `when` clause** **`excludes_modeless_hint_route`** was reimplemented to abstain whenever the case would use **`argen_modeless_*`** templates: **`contact_model_mode: on`** + eligible Argen route, **or** legacy raw **`modeless`** hint (study cases unchanged). This keeps Abby/VD multi-outcome rules from conflicting with contact-model template selection.
- **Schema**: validates **`off`** / **`on`**; accepts deprecated strings and normalizes them with a **warning**; accepts YAML 1.1 boolean **`true`/`false`** from unquoted `on`/`off` and coerces with a warning. **`business_rules/v1/argen_modes.yaml`** uses quoted **`"off"`** to avoid boolean parsing.
- **Harness**: argen parity scenarios updated for **`on`**/**`off`**; temp YAML emits quoted modes; legacy migration row retained.

## 2. Files modified

| File | Change |
|------|--------|
| `business_rules/v1/argen_modes.yaml` | `contact_model_mode: "off"`; comments for on/off behavior. |
| `infrastructure/config/business_rule_schemas.py` | `ALLOWED_CONTACT_MODEL_MODES`, legacy map, bool coercion, `default_argen_modes`. |
| `infrastructure/config/argen_modes_runtime.py` | Baseline `off`; docstring. |
| `domain/rules/template_rules.py` | Passthrough `effective_argen_hint_route`; `contact_model_argen_on()`; `is_eligible_contact_model_argen_case()`. |
| `template_utils.py` | Direct contact-model branch before legacy `hint_route == "modeless"` branch. |
| `domain/decisions/doctor_when_eval.py` | `excludes_modeless_hint_route` uses unified argen modeless path detection. |
| `tests/doctor_policy_parity_harness.py` | Quoted argen YAML; scenarios `on`/`off`; legacy migration row. |
| `CASE_CREATOR_ARGEN_CONTACT_MODE_ON_OFF_REPORT.md` | This report (new). |

## 3. Behavior audit findings

- **Previously**, `effective_argen_hint_route` rewrote hints (`always_with` → synthetic `modeless`, `always_without` remapped `modeless` to `argen_adzir` / `argen_envision`). Template selection then depended on **`hint_route == "modeless"`** for contact-model folders.
- **Now**, **`on`** selects **`argen_modeless_*`** using **`contact_model_argen_on()`** and **`is_eligible_contact_model_argen_case()`** (normalized route in Argen allowlist). **`off`** does not use that branch; hints are unchanged by `effective_argen_hint_route` (passthrough).
- **Breaking change (documented):** Configs that relied on **`always_without_contact_models`** to remap **`modeless`** → non-modeless Argen hints no longer get that behavior; those values normalize to **`off`**, which is passthrough + legacy template branches only.

## 4. New live behavior

| `contact_model_mode` | Behavior |
|----------------------|----------|
| **`off`** | Same as former **`legacy_default`**: no contact-model forcing from config; `material_hint.route` passes through; existing Abby/VD/Argen `elif` logic applies. |
| **`on`** | For **eligible Argen** routes only and **`has_study` false**, template is **`argen_modeless_adzir`** if material is Adzir, else **`argen_modeless_envision`**. Non-eligible routes (e.g. empty / non-Argen hint) are unchanged. **Study** cases do not use this branch (same gate as the legacy modeless fast path). |

**YAML:** Use quoted **`"on"`** / **`"off"`** so PyYAML does not parse them as booleans.

## 5. Validation performed

- `python3 tests/doctor_policy_parity_harness.py` — exit **0** (offline parity, argen **`on`**/**`off`** rows, legacy migration, snapshots, observability, flags, production seed, repo load).
- Manual check: **non-eligible** route (`""`) + **`on`** still resolved to **`argen_adzir`** for a generic doctor (not forced to modeless).
- Import smoke: `template_utils.select_template`, `template_rules.contact_model_argen_on`.

## 6. Risks or limitations

- **`always_without_contact_models`** semantics are **not** preserved when migrating to **`off`**; operators who depended on that must revisit routing.
- Unquoted **`on`/`off`** in YAML can become booleans; schema coerces but emits warnings — prefer quoted strings in files.
- **Doctor outcomes live** + **`on`**: Abby/VD rules abstain on the contact-model path via updated **`excludes_modeless_hint_route`** logic; verify in staging if combining both flags.

## 7. Recommended next pass

1. Communicate the **`always_without`** behavior removal to anyone with old YAML.
2. Optional: add a dedicated parity row for **non-eligible route + on** in the harness (currently verified manually).
3. Consider pruning or archiving obsolete docs that describe the three-value enum only.

---

## Final chat summary

1. **`contact_model_mode`** is now **`off`** / **`on`**; **`off`** matches former legacy passthrough; **`on`** forces **`argen_modeless_adzir`** / **`argen_modeless_envision`** for eligible non-study Argen cases via **`select_template`**.
2. **Hint transformation** is **no longer** the active mechanism; **`effective_argen_hint_route`** only passes the normalized hint through.
3. **Yes** — with **`on`**, valid Adzir vs Envision Argen cases route to the intended contact-model templates (harness + spot check).
4. **Next:** Roll out quoted YAML, notify users about **`always_without`** migration, and pilot **`on`** in a controlled environment.
