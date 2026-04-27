# CASE CREATOR EXPANDED DOCTOR OVERRIDE PLAN

## 1. Purpose

The live `doctor_overrides` YAML family today supports only:

- Doctor **string match** (`contains_any` / `contains_all` on the doctor field), and  
- A single **`template_override_key`** applied **after** `template_utils.select_template` completes (`domain/decisions/template_selector.py`).

That design is **insufficient** for Abby Dew and VD Brier Creek because both are **not** “one doctor → one template.” They interact with **material**, **shade / non-Argen shade**, **scanner (iTero vs not)**, **shade_usable**, **signature**, **study**, **anterior**, **hint_route (modeless / Argen family)**, and—separately—**Brier Creek** naming affects **route labels** through a **different** predicate than the VD template predicate.

If an operator enables a single `template_override_key` for Abby, the post-processor override **replaces the entire** `select_template` result and **flattens** material-specific outcomes (e.g. `ai_adzir` vs `ai_envision`). That is why the baseline seeding report correctly refused to move Abby into the current YAML shape.

This plan defines the **minimum expanded, validated schema** and **integration points** needed to represent **today’s coded behavior faithfully**, without implementation in this pass.

---

## 2. Current built-in doctor behaviors

Source of truth: `template_utils.select_template`, `domain/rules/doctor_rules.py`, `case_processor_final_clean.py` (case_data enrichment), `domain/decisions/destination_selector.py`, `domain/rules/routing_rules.py`.

### 2.1 Abby Dew

**Match (doctor identity)** — `domain/rules/doctor_rules.is_abby_dew`:

- Doctor string (case-insensitive) contains **both** substrings `"abby"` and `"dew"`.

**Template effects** — `template_utils.select_template` sets `is_abby = is_abby_dew(doctor_name)`. Abby participates only in branches that are **reached** after earlier `if / elif` conditions (anterior-only block, modeless block, `is_ai` blocks, signature/iTero/shade_usable “early” branches, etc.).

**Direct Abby branches** (explicit `is_abby` in condition):

| Condition (all must hold for that `elif`) | Template folder |
|---------------------------------------------|-----------------|
| `not has_study`, `not signature`, `is_adz_material(material)`, `shade_usable`, **`is_abby`** | `ai_adzir` |
| `not has_study`, `not signature`, **not** `is_adz_material(material)`, `shade_usable`, **`is_abby`** | `ai_envision` |

**Indirect Abby effects** — Abby appears in **negated** form on Argen single-unit branches:

- `... shade_usable and not non_argen_shade and not is_abby and not is_vd_serbia` → `argen_adzir`
- `... shade_usable and not non_argen_shade and not is_abby and not is_vd_serbia` → `argen_envision`

So Abby **blocks** those Argen outcomes when the case would otherwise land on those lines **and** `non_argen_shade` is false. With Abby true, the flow falls through to later branches (including non‑Argen shade branches and the explicit Abby lines above).

**Material dependence:** Yes — `template_rules.is_adz_material(material)` (`"adz" in material`).

**Other inputs that gate whether Abby logic runs at all:** `has_study`, `signature`, `is_anterior`, `hint_route` / modeless path, `is_ai`, `is_itero`, `shade_usable`, `non_argen_shade` (`template_rules.is_non_argen_shade(shade)`), and the full `elif` order.

**Route / destination / label:** Abby does **not** special-case `select_destination` or `route_label_for_template` by name. Outcomes are entirely driven by the **chosen template filename** and the generic rules in `routing_rules.route_label_for_template(template, doctor_name)` (Serbia only if `"brier creek"` in doctor string — see §2.3).

**Argen restrictions:** Abby is excluded from the **default Argen** branches (lines with `not is_abby`) and steered to **AI** templates on the explicit Abby branches when those lines are reached.

### 2.2 VD Brier Creek (template predicate)

**Match (doctor identity)** — `domain/rules/doctor_rules.is_vd_brier_creek`:

- Doctor string contains **at least one** of last-name tokens: `britt`, `de frias`, `escobar`, `martin` (substring match, case-insensitive).
- **And** doctor string contains **`brier creek`** (substring, case-insensitive).

**Note:** Docstring mentions “vd-brier creek”; implementation does **not** require the `"vd-"` prefix—only `"brier creek"`.

**Template variable:** `is_vd_serbia = is_vd_brier_creek(doctor_name)` in `select_template`.

**Direct VD branches:**

| Condition | Template folder |
|-----------|-----------------|
| `not has_study`, `not signature`, `is_adz_material`, `not is_itero`, **`is_vd_serbia`** | `ai_adzir_model` |
| `not has_study`, `not signature`, **not** `is_adz_material`, `not is_itero`, **`is_vd_serbia`** | `ai_envision_model` |

**Indirect VD effects (Argen blocking):** Same pattern as Abby—VD is in the negated clause on the Argen branches:

- `not is_abby and not is_vd_serbia` required for `argen_adzir` / `argen_envision` on those lines.

**Material / scanner dependence:** Yes — Adz vs Envision and **non–iTero** (`not is_itero`) for the VD-specific `*_model` outcomes.

**Route / destination / label (template-driven only for VD-specific rows):** Choosing `ai_adzir_model` / `ai_envision_model` changes template family classification (`ai` in filename), which flows into `resolve_destination_key` and label selection like any other AI template.

### 2.3 “Serbia” labeling vs VD template predicate (critical distinction)

**Template-related VD** uses **`is_vd_brier_creek`** (narrow: last-name list + `brier creek`).

**Route labels** for study / anterior / AI templates use **`routing_rules.is_serbia_case`**:  
`"brier creek" in (doctor_name or "").lower()` — **no** last-name list.

So: **any** doctor name containing “Brier Creek” can get **Serbia-style labels** (`LABEL_SERBIA` / `LABEL_AI_SERBIA`) when the template is study, anterior, or AI. **VD template branches** apply only to the **narrow** subset matching `is_vd_brier_creek`.

Effects in `case_processor_final_clean.py`: `select_destination` → `route_label_key` → exact log strings (`SERBIA CASE`, etc.). Destination roots still come from `destination_key` (Argen vs `1_9`), not from the label.

### 2.4 Other doctor-specific branching (related context)

- **Signature doctors** — `is_signature_doctor` (Excel list: `List of Signature Dr.xlsx` via `config.SIGNATURE_DOCTORS_PATH`). Drives many `signature` branches in `select_template`. Set in `case_processor_final_clean.py` from `template_utils.is_signature_doctor` (re-imported locally). This is **doctor-specific** but **not** Abby/VD; any expanded “doctor policy” system should not accidentally conflate Excel signature rules with substring rules unless explicitly scoped.
- **`is_ai` in `case_data`** — Read in `select_template` but **not** set in the main `evo_to_case_data` / processor path observed in this repo (stays default `False` unless another caller sets it). The `is_ai` `elif` block is part of the **code** chain but may be **unreachable** in the primary Evolution import pipeline today. Parity tests should still account for it if external entrypoints set `is_ai`.

---

## 3. Why the current YAML schema is too weak

**What it can do today**

- Match doctor name with `contains_any` / `contains_all`.
- Apply at most one **live** action: `template_override_key` (`doctor_override_runtime.resolve_doctor_template_override_key` — `route_label_override_key` exists in schema but is **not** applied live in the runtime resolver today).
- Apply that key **globally** for the doctor match, **after** full template selection.

**What it cannot do**

- Express **conditional** template outcomes (material, scanner, shade markers, shade_usable, study, signature, anterior, hint_route / modeless).
- Express **negative** gating (“remove doctor from Argen eligibility on these lines only”) without replacing the whole template.
- Express **multiple** ordered outcomes per doctor (elif-style) without flattening.
- Align **narrow** VD template logic with **broad** Brier Creek **label** logic—they use **different** predicates in code today; a single doctor match block cannot capture both without separate fields.
- Cooperate with **`select_template`’s order**—faithful behavior is order-sensitive.

---

## 4. Proposed expanded doctor override schema

**Goals:** bounded fields, schema-validated, no arbitrary expression language, sufficient to encode **current** Abby and VD behaviors **and** keep a path for signature/Excel later if desired.

**Top-level file shape (conceptual)** — unchanged `version`, `enabled`, `rules: []`.

**Each rule** — extend with optional structured blocks:

| Section | Purpose |
|---------|---------|
| `match` | Doctor identity: keep existing `contains_any` / `contains_all`; **add optional** `predicate` enum for built-ins (`abby_dew`, `vd_brier_creek`) that **must** match the same Python helpers (parity testing). |
| `when` | Optional **gate** on the whole rule: all/any of **bounded** condition clauses (see §5). If absent, treat as “doctor match only” (backward compatible for simple overrides). |
| `outcomes` | Ordered list of `{ when, action }`. **First** matching `when` wins within the rule. If no `outcomes` entry matches, rule does **nothing** (fall through to code baseline). Replaces single flat `action` for complex doctors. |
| `action` | **Legacy / simple rules:** single `template_override_key` and/or (when made live) `route_label_override_key`. **Mutually exclusive** with `outcomes` for the same rule, or `outcomes` takes precedence—validator enforces one mode. |

**Validation rules (design-level)**

- `outcomes[].when` uses the same clause vocabulary as §5.
- `outcomes[].action` uses only keys from §6.
- No raw paths. All template keys ∈ `KNOWN_TEMPLATE_KEYS` (existing pattern).
- Rule order global: first **enabled** rule whose `match` + top-level `when` passes; then **outcomes** sub-order.

---

## 5. Proposed supported condition fields

Only fields needed to reproduce **observed** Abby/VD interactions in `select_template` **and** optional label alignment:

| Clause type | Semantics | Maps to |
|-------------|-----------|---------|
| `field_eq` | `{ "field": "<case_data field>", "value": <bool|string> }` | e.g. `has_study`, `signature`, `shade_usable`, `is_anterior` |
| `material_is_adz` | boolean | `template_rules.is_adz_material(material)` |
| `material_is_envision` | boolean | logically `not is_adz` for current binary material model |
| `scanner_is_itero` | boolean | `template_rules.is_itero_scanner(scanner)` |
| `non_argen_shade` | boolean | `template_rules.is_non_argen_shade(shade)` |
| `hint_route` | `{ "in": ["modeless", "argen_adzir", ...] }` or `eq` | After `effective_argen_hint_route(normalized_hint_route, material)` if parity requires matching post-argen-modes transform; **design choice:** store “effective” vs “raw” in schema version notes. |
| `shade_usable` | boolean | `bool(shade.strip())` as set in processor |

**Explicitly omitted (for minimum scope):** free-text regex on doctor, arbitrary numeric tooth ranges beyond what `field_eq` on `is_anterior` already encodes, nested OR trees deeper than `all` / `any` lists.

**Label / Serbia predicate (separate from template):**

| Clause | Semantics |
|--------|-----------|
| `doctor_contains` | list of substrings (all or any) for **label-only** rules—use to model `is_serbia_case` breadth vs `is_vd_brier_creek` narrow template rules **without** conflating them |

---

## 6. Proposed supported action fields

Keep **bounded** and minimal:

| Action key | Meaning |
|------------|---------|
| `template_override_key` | Same as today: force final template folder key (must remain in `KNOWN_TEMPLATE_KEYS`). |
| `route_label_override_key` | One of `ALLOWED_ROUTE_LABEL_KEYS` — **only** when label seam is wired to consult doctor YAML (today schema allows; runtime does not). Use sparingly; prefer template-driven labels when possible. |
| `destination_key_override` | `argen` \| `1_9` — **optional** future if doctor policy must override family map; **not** required for current Abby/VD if templates stay authoritative. |

**Deferred (not needed for current Abby/VD parity if `outcomes` + `template_override_key` are sufficient):**

- `forbid_argen`, `disallow_template_families` — tempting for “negative” gating, but easy to desync from `select_template` order; prefer explicit `outcomes` that set the **same** template the `elif` chain would pick.

**`template_family_override_key`** — belongs to **shade** family in current codebase, not doctor; do not overload unless deliberately merging families (out of scope).

---

## 7. Exact YAML representation proposal for Abby Dew

**Intent:** Two **outcomes** mirror the two explicit `is_abby` branches (lines 96–97 and 111–112). **Additional** parity requires that when the code would have **blocked** Argen due to `not is_abby` on lines 84 / 99, the YAML-driven engine must **not** return an Argen template for Abby in those situations—either by matching the same `when` clauses as those lines or by delegating to `select_template` when no doctor outcome applies.

**Illustrative YAML (syntax indicative; not live):**

```yaml
rules:
  - id: builtin_abby_dew_template_policy
    enabled: true
    match:
      predicate: abby_dew
    when:
      all:
        - { field: has_study, eq: false }
        - { field: signature, eq: false }
    outcomes:
      - when:
          all:
            - { material_is_adz: true }
            - { field: shade_usable, eq: true }
        action:
          template_override_key: ai_adzir
      - when:
          all:
            - { material_is_adz: false }
            - { field: shade_usable, eq: true }
        action:
          template_override_key: ai_envision
```

**Caveat (must be handled in implementation):** In code, Abby can also route through **non_argen_shade** branches (e.g. `ai_adzir` / `ai_adzir_model`) **before** the explicit Abby branches, depending on `non_argen_shade`, `is_itero`, and `elif` order. A faithful migration either:

- **(A)** Implements `outcomes` with **full** clause sets for every template path Abby can take, or  
- **(B)** Calls a **doctor policy hook inside** `select_template` **before** or **instead of** scattered `is_abby` checks, returning “no override” when the generic chain should decide—**largest** refactor, or  
- **(C)** Keeps code `is_abby` until parity tests prove YAML covers **all** reachable states.

This plan recommends **(C)** as a staging strategy, then **(A)** with exhaustive parity tables derived from the `elif` chain.

---

## 8. Exact YAML representation proposal for VD Brier Creek

**Template policy (narrow predicate):**

```yaml
rules:
  - id: builtin_vd_brier_creek_template_policy
    enabled: true
    match:
      predicate: vd_brier_creek
    when:
      all:
        - { field: has_study, eq: false }
        - { field: signature, eq: false }
        - { scanner_is_itero: false }
    outcomes:
      - when:
          all:
            - { material_is_adz: true }
        action:
          template_override_key: ai_adzir_model
      - when:
          all:
            - { material_is_adz: false }
        action:
          template_override_key: ai_envision_model
```

**Serbia / Brier Creek labeling (broad predicate):** Today this is **not** “VD” — it is **any** doctor containing `brier creek`. If the goal is YAML visibility for **labels**, add a **separate** optional rule type or a dedicated `label_rules` subsection:

```yaml
label_rules:
  - id: brier_creek_serbia_labels
    match:
      doctor_contains_all: ["brier creek"]
    action:
      route_label_override_key: serbia   # only for templates that would use designer vs serbia split
```

**Important:** `route_label_for_template` today chooses Serbia vs designer **per template family** (study/anterior/ai). A blind override could conflict with Argen templates (Argen label stays Argen). Implementation must **restrict** label overrides to the same branches where `routing_rules.route_label_for_template` currently chooses between designer and Serbia—**not** a global override.

---

## 9. Runtime integration plan

| Seam | Role |
|------|------|
| **`template_utils.select_template` (or immediate helper)** | Primary place to evaluate **doctor `outcomes`** **with access** to full `case_data` and **before** final `folder` is chosen—**or** to replace inline `is_abby` / `is_vd_serbia` checks once parity is proven. |
| **`domain/decisions/template_selector.select_template_path`** | Today applies YAML `template_override_key` **after** `select_template`. Expanded design should **merge** into one coherent phase: either **only** pre-merged template from `select_template`, or **one** doctor resolver that returns `Optional[template_key]` with full conditionals—**avoid** applying a second global override on top of conditional outcomes (double substitution risk). |
| **`domain/decisions/destination_selector`** | Keep **template-derived** `destination_key` via `resolve_destination_key` unless a future **bounded** `destination_key_override` is added to doctor policy. |
| **`routing_rules.route_label_for_template` or wrapper** | If label rules are externalized, inject **after** template name is known, **narrowly** replacing designer vs Serbia choice for study/anterior/ai—mirror existing `is_serbia_case` semantics. |

---

## 10. Migration strategy

**Phase 0 — No double application**

- Disable post-hoc single-key override when a rule uses `outcomes` (validator + runtime contract).
- Or: deprecate post-processor override path entirely in favor of **one** doctor resolution pass inside template selection.

**Phase 1 — Introduce schema + loader normalization only**

- Parse `outcomes`, validate clauses; **do not** wire to live selection yet.

**Phase 2 — Parity harness**

- For each rule id, generate cartesian samples over bounded fields (material, scanner, shade_usable, non_argen_shade, signature, has_study, …) and assert old code vs new resolver agree on `folder`.

**Phase 3 — Cutover Abby**

- Remove **only** `is_abby` branches from `select_template` when parity suite passes; keep code fallback behind feature flag if needed.

**Phase 4 — Cutover VD template branches**

- Same for `is_vd_serbia` template branches.

**Phase 5 — Labels (optional, separate)**

- Model `is_serbia_case` explicitly; **do not** conflate with `is_vd_brier_creek` in a single match block.

**Rollback:** feature flag or `enabled: false` per rule; keep `doctor_rules.py` predicates as canonical matchers for `predicate` enum.

---

## 11. Validation strategy

1. **Unit parity:** For each predicate (`abby_dew`, `vd_brier_creek`), table-test template folder outputs across combinations of: `has_study`, `signature`, `material` (adz/envision), `scanner` (itero/non), `shade` (non-Argen marker yes/no), `shade_usable`, `is_anterior`, `hint_route` / modeless, and `is_ai` (if ever set).
2. **Integration:** Run `select_template_path` (or future unified entry) on recorded real `case_data` snapshots (anonymized) and diff template path.
3. **Destination:** Assert `resolve_destination_key(template_filename)` unchanged for before/after template choices.
4. **Labels:** For doctor strings: (a) VD Brier match, (b) Brier Creek without VD last name, (c) neither—assert `route_label_key` matches current `route_label_for_template` for fixed template filenames.
5. **Regression:** Abby must never receive `argen_adzir` / `argen_envision` on the lines where `not is_abby` is required in today’s code, for states that previously fell through to Abby AI branches.
6. **Config safety:** Invalid YAML must fall back to **current** code-only behavior (today’s loader pattern).

---

## 12. Recommended implementation pass

**Safest next code-change pass (after this plan):**

1. **Schema + validation only:** extend `business_rule_schemas.validate_doctor_overrides` with optional `predicate`, `when`, `outcomes` (strict allowlists). **Do not** change runtime resolution.
2. Add **`domain/decisions/doctor_policy_resolver.py`** (name indicative) exposing `resolve_doctor_template_policy(case_data) -> Optional[str]` returning a **template key** only when a rule’s `outcomes` matches—**not** wired into `select_template` yet; used from **tests only**.
3. Build the **parity harness** comparing resolver output to `select_template` for Abby/VD slices.
4. Only after green parity, **replace** inline `is_abby` / `is_vd_serbia` branches in `select_template` with the resolver (single integration point).

**Do not** start by seeding production YAML with multi-outcome rules until step 3 passes.

---

## Final chat summary

1. **What blocks Abby/VD today:** Doctor YAML allows only a **single** `template_override_key` applied **after** full template selection, which **cannot** express material/scanner/shade/shade_usable–dependent outcomes or the **negated** Argen gating Abby/VD rely on without flattening or double-applying.
2. **Minimum schema expansion:** `match` (including optional `predicate` enums), top-level `when`, and an ordered **`outcomes[]`** of `{ when, action }` with **bounded** condition clauses; optional separate **label rules** if Serbia breadth (`brier creek`) is to be visible separately from **VD** template narrow matching.
3. **Can Abby/VD be fully moved to YAML safely?** **Yes, with conditions:** requires **exhaustive parity** against the current `elif` chain (including indirect paths via `non_argen_shade` and order) and a **single** integration seam to avoid **double** overrides. **Label broad vs narrow** predicates must stay **explicitly separate** in schema and tests.
4. **Next implementation pass:** Schema + validator + **offline** `doctor_policy_resolver` + **parity harness**; **no** live wiring until Abby/VD slices match exactly.
