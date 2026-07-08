# CASE CREATOR OUTSOURCE DESIGNER RESTRUCTURE PLAN

> Planning / audit pass. No runtime behavior is changed by this document. It identifies the
> exact seams to touch and the smallest, safest reroute using logic that already exists in the
> repo.

---

## 1. Summary of desired behavior

The business is retiring **Argen** as the active delivery path. Argen code, templates, routing
structures, and helpers stay in the repo, but the **live** path changes to a two-mode model:

| Mode | Role | Effective destination | Delivery |
| --- | --- | --- | --- |
| `outsource` | **DEFAULT** for all cases | "send-to-ai" side → `SEND_TO_AI_PATH` | **ZIPPED** |
| `designer` | **EXCEPTION** only | "send-to-designer" side → `SEND_TO_1_9_PATH` | **UNZIPPED** |

Rules for the new model:

- **outsource is the default.** Every case is outsource unless a disqualifier fires.
- **designer is the exception,** chosen *only* from YAML-managed disqualifiers:
  - certain **doctor names**
  - certain **shades**
- `has_study` **must no longer** decide designer vs outsource.
- The **existing templates stay correct** and keep being selected exactly as today.
- **No new zip system.** Reuse the existing `zip_case_folder()` + `if do_zip:` execution blocks.
- **No new "designer" pipeline.** Reuse the existing unzipped `SEND_TO_1_9_PATH` behavior.
- Argen-specific *live* behavior (Argen destination + Argen-gated zip) is no longer the active
  path, even though the code and templates remain present.

The core architectural move: **decouple destination + zip from template family / `has_study`,**
and drive them from one small `outsource` vs `designer` decision fed by YAML disqualifiers.

---

## 2. Current code-path audit

### 2.1 Entry point

`case_processor_final_clean.process_case(case_number, folder_path, log_callback)` is the single
live engine.
Call chain: `import_service.import_case` → `process_case_from_id` ([case_processor_final_clean.py:665](case_processor_final_clean.py:665)) → `process_case` ([case_processor_final_clean.py:250](case_processor_final_clean.py:250)).
The PySide6 GUI (`pyside6_ui.py`) and `manual_import.py` go through the same `import_service`.

### 2.2 Where template selection happens

- Call site: [case_processor_final_clean.py:474](case_processor_final_clean.py:474)
  `template_path = select_template_path(case_data)`
- `select_template_path` → [domain/decisions/template_selector.py:7](domain/decisions/template_selector.py:7)
  - delegates to `template_utils.select_template(case_data)` — the big if/elif ladder at
    [template_utils.py:15](template_utils.py:15) that returns a folder like `argen_adzir`,
    `ai_envision`, `reg_envision_study`, etc.
  - then optionally applies a **doctor template override** via
    `resolve_doctor_template_override_with_source` (only the `outcomes` source is gated by env
    `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE`; a `simple` action override always applies).
- **Verdict:** template selection is self-contained and *correct per the business*. It should
  **not** change in this restructure. It does, however, branch heavily on `has_study`, `signature`,
  `is_itero`, material, `shade_usable`, `non_argen_shade`, `is_abby`, `is_vd_serbia` — which is fine
  for *which template*, but that coupling must **not** leak into the destination/zip decision.

### 2.3 Where destination / final folder selection happens

Two layers:

1. **Category decision** — `select_destination(template_filename, doctor, case_data)`
   ([case_processor_final_clean.py:484](case_processor_final_clean.py:484) →
   [domain/decisions/destination_selector.py:27](domain/decisions/destination_selector.py:27)).
   - `destination_key = resolve_destination_key(template_name)`
     ([infrastructure/config/routing_override_runtime.py:40](infrastructure/config/routing_override_runtime.py:40)):
     infers a template *family* (`argen` / `study` / `anterior` / `ai`) and maps it via
     `BASELINE_FAMILY_DESTINATION_MAP` + YAML `routing_overrides`. **It can only ever return
     `DEST_ARGEN` or `DEST_1_9`.**
   - `route_label_key` → used **only for log messages** ("ARGEN CASE", "DESIGNER CASE", ...).

2. **Physical path decision** — the real seam, [case_processor_final_clean.py:489-494](case_processor_final_clean.py:489):
   ```python
   if destination_decision.destination_key == routing_rules.DEST_ARGEN:
       target_root = SEND_TO_ARGEN_PATH
   elif destination_decision.destination_key == routing_rules.DEST_1_9:
       target_root = SEND_TO_1_9_PATH
       if destination_decision.is_ai_alias_to_designer:
           debug("[route] AI template re-routed to DESIGNER path")
   ```
   Then `final_output = os.path.join(target_root, case_id)` at
   [case_processor_final_clean.py:512](case_processor_final_clean.py:512).

**Key finding:** `SEND_TO_AI_PATH` ("Send to AI") is defined and its folder is created
([config.py:34](config.py:34), [config.py:40](config.py:40)) but is **never assigned to
`target_root`** anywhere in the live processor. It is currently a dormant destination. The three
roots are defined at [config.py:34-37](config.py:34):

- `SEND_TO_AI_PATH`  = `<CC_IMPORTED_ROOT>/Send to AI`   ← currently unused as a target
- `SEND_TO_ARGEN_PATH` = `<CC_IMPORTED_ROOT>/Send to Argen` ← current Argen target
- `SEND_TO_1_9_PATH` = `<CC_IMPORTED_ROOT>/Send to 1.9`   ← current designer target (unzipped)

### 2.4 Where zip vs non-zip delivery happens

- Decision: `do_zip = should_zip(case_data, template_path, target_root)`
  ([case_processor_final_clean.py:497](case_processor_final_clean.py:497)).
  - `should_zip` ([case_processor_final_clean.py:66](case_processor_final_clean.py:66)) maps
    `target_root` → a destination key and calls
    `routing_rules.should_zip_modeless_argen(...)`
    ([domain/rules/routing_rules.py:79](domain/rules/routing_rules.py:79)):
    ```python
    is_modeless_family = route == "modeless"
    return is_modeless_family and (tpl_is_argen or is_argen_dest)
    ```
- Execution (the actual zip): the identical block appears **twice** — once in the non-3Shape
  branch [case_processor_final_clean.py:610-617](case_processor_final_clean.py:610) and once in
  the 3Shape branch [case_processor_final_clean.py:630-637](case_processor_final_clean.py:630):
  ```python
  if do_zip:
      zip_path = zip_case_folder(final_output, log_callback)
      shutil.rmtree(final_output)   # remove unzipped folder
      return f"Completed {case_id} → {zip_path}"
  ```
- The zip mechanism itself: `zip_case_folder()`
  ([case_processor_final_clean.py:44](case_processor_final_clean.py:44)) — `shutil.make_archive`
  producing a `.zip` whose top-level entry is the case folder.

### 2.5 CRITICAL finding — the existing zip trigger is currently *dead*

`evo_to_case_data.py` sets **`DISABLE_MODELESS = True`** ([evo_to_case_data.py:8](evo_to_case_data.py:8)):

```python
disable_modeless = True
modeless = detected_modeless and not disable_modeless   # -> always False
if modeless and route in ("argen_envision", "argen_adzir"):
    route = "modeless"   # <-- never executes
```

So `material_hint.route` is **never** `"modeless"`. Therefore `should_zip_modeless_argen` **always
returns `False`**, and **no case is zipped in the current live path** — including current Argen
cases, which land *unzipped* in `Send to Argen`.

This is important and *helpful*: the entire zip pipeline (`zip_case_folder` + both `if do_zip:`
blocks) already exists and is wired into both branches, but is gated off. We reuse it by flipping
the gate to "mode == outsource" — **no new zip code is required.**

### 2.6 Current effective routing (as it actually runs today)

| Template family selected | `destination_key` | `target_root` | Zipped today? |
| --- | --- | --- | --- |
| `argen_*` | `DEST_ARGEN` | `Send to Argen` | No (modeless dead) |
| `ai_*`, `*_study`, `*_anterior` | `DEST_1_9` | `Send to 1.9` | No |
| (never) `argen_modeless_*` | `DEST_ARGEN` | `Send to Argen` | Would zip if modeless enabled |

`Send to AI` is never written to. Nothing is zipped.

---

## 3. Existing reusable logic

Everything the new model needs already exists; the restructure is mostly *rewiring*, not new code.

| Need | Reuse this (already in repo) | Location |
| --- | --- | --- |
| Zip a finished case folder | `zip_case_folder()` | [case_processor_final_clean.py:44](case_processor_final_clean.py:44) |
| Zip + cleanup + return, both scanner branches | the two `if do_zip:` blocks | [case_processor_final_clean.py:610](case_processor_final_clean.py:610), [case_processor_final_clean.py:630](case_processor_final_clean.py:630) |
| Unzipped "designer" delivery | plain `SEND_TO_1_9_PATH` write (no zip) | [config.py:36](config.py:36), path assign [case_processor_final_clean.py:492](case_processor_final_clean.py:492) |
| Zipped "outsource" destination folder | `SEND_TO_AI_PATH` (already created, just unused) | [config.py:34](config.py:34), [config.py:40](config.py:40) |
| "Certain shades" disqualifier | `is_non_argen_shade(shade)` reading live `shade_overrides.non_argen_shade_markers` | [domain/rules/template_rules.py:11](domain/rules/template_rules.py:11), [infrastructure/config/shade_override_runtime.py:30](infrastructure/config/shade_override_runtime.py:30) |
| "Certain doctor names" matching style | substring/`contains_any` matcher already used for doctors | [domain/decisions/doctor_policy_resolver.py:17](domain/decisions/doctor_policy_resolver.py:17), [doctor_policy_resolver.py:29](domain/decisions/doctor_policy_resolver.py:29) |
| Bounded YAML family pattern (validator + default + `@lru_cache` runtime + `clear_*_cache`) | `argen_modes` / `shade_overrides` families | [infrastructure/config/business_rule_schemas.py](infrastructure/config/business_rule_schemas.py), [infrastructure/config/argen_modes_runtime.py](infrastructure/config/argen_modes_runtime.py) |
| Template selection (unchanged) | `select_template_path` / `select_template` | [domain/decisions/template_selector.py:7](domain/decisions/template_selector.py:7), [template_utils.py:15](template_utils.py:15) |

**Note on the shade disqualifier:** `shade_overrides.non_argen_shade_markers` (default `C3`, `A4`)
already means, semantically, "this shade should not go the Argen/outsource way." That is *exactly*
a designer disqualifier. It is already live and cached — reuse it directly for the shade half and
add **zero** new shade YAML.

**Note on config caching:** all runtime resolvers use `@lru_cache(maxsize=1)` with a
`clear_*_cache()` helper, but those helpers are only invoked from tests — the live app reads config
once per process and the YAML header instructs "SAVE THIS FILE AND RESTART THE APP." So a new
resolver following the same pattern needs no live cache-invalidation wiring; restart picks it up.

---

## 4. Proposed bounded YAML design

### 4.1 Design goals

- Beginner-editable: the disqualifiers are just **two flat lists**.
- Bounded/validated: unknown keys rejected by the existing strict allow-list validator.
- Minimal: reuse `shade_overrides` for the shade half; only the doctor-name list is genuinely new.

### 4.2 Recommended: one small new family `delivery_modes`

Add a new top-level section parallel to `argen_modes`:

```yaml
delivery_modes:
  version: 1
  enabled: true
  # outsource is always the default. A case becomes "designer" only if a
  # disqualifier below matches. has_study is intentionally NOT a factor.
  designer_doctor_names:      # case-insensitive substring match against the case doctor
    - "Brier Creek"
  designer_shades:            # OPTIONAL. If empty, shade disqualifier reuses
    []                        # shade_overrides.non_argen_shade_markers (recommended)
```

Semantics of the live resolver (new, small):

```
mode = "outsource"                       # default
if doctor matches any designer_doctor_names        -> mode = "designer"
elif shade matches designer_shades (or, if that
     list is empty, shade_overrides markers)       -> mode = "designer"
return mode
```

### 4.3 Lower-churn alternative (if avoiding a new family is preferred)

Reuse `shade_overrides.non_argen_shade_markers` for shades (no change) and add **only** a bounded
doctor list. Two placements are possible:

- **A.** New family `delivery_modes` with just `designer_doctor_names` (recommended for clarity —
  one obvious place for the whole mode decision).
- **B.** A new bounded key on an existing family (e.g. `shade_overrides` is the wrong home;
  `doctor_overrides` is rule-shaped and awkward). Not recommended — overloading `doctor_overrides`
  rules (whose actions are template/label keys) to express "mode" is more code and less legible
  than a flat list.

### 4.4 What adding a family requires (bounded, mechanical)

The schema is a strict allow-list, so a new family touches these spots only:

1. `SUPPORTED_FAMILIES += ("delivery_modes",)` — [business_rule_schemas.py:6](infrastructure/config/business_rule_schemas.py:6).
   (This automatically extends `ALLOWED_UNIFIED_TOP_LEVEL_KEYS`, which splats `*SUPPORTED_FAMILIES`
   at [business_rule_schemas.py:18](infrastructure/config/business_rule_schemas.py:18).)
2. `default_delivery_modes()` + `validate_delivery_modes()` (mirror `validate_argen_modes`,
   [business_rule_schemas.py:494](infrastructure/config/business_rule_schemas.py:494)); validate the
   two lists as "lists of non-empty strings."
3. Register both in `validate_unified_business_rules_config` — the `validators` and `effective`
   dicts at [business_rule_schemas.py:606-617](infrastructure/config/business_rule_schemas.py:606).
4. Add to `_schema_defaults_effective()` in the loader
   [business_rule_loader.py:210](infrastructure/config/business_rule_loader.py:210).
5. New runtime resolver `infrastructure/config/delivery_mode_runtime.py` with `@lru_cache`
   `_cached_preview()` + `clear_delivery_mode_cache()` (mirror
   [shade_override_runtime.py](infrastructure/config/shade_override_runtime.py)).
6. Seed the new section into `business_rules_seed/v1/case_creator_rules.yaml` and
   `business_rules/v1/case_creator_rules.yaml` so packaged/frozen installs get sane defaults.

> If the shade half reuses `shade_overrides` markers, `designer_shades` can be omitted entirely,
> shrinking the new family to a single `designer_doctor_names` list.

---

## 5. Proposed runtime reroute plan

The whole reroute lives in **one contiguous block** of `process_case` and one new helper. Template
selection, XML generation, scan handling, and the zip execution blocks are untouched.

### 5.1 New helper (domain-level, tiny)

`resolve_delivery_mode(case_data) -> "outsource" | "designer"` — reads the new YAML resolver +
`is_non_argen_shade`:

```python
def resolve_delivery_mode(case_data) -> str:
    doctor = case_data.get("doctor", "")
    shade  = case_data.get("shade", "")
    if is_designer_doctor(doctor):          # new delivery_mode_runtime, bounded list
        return "designer"
    if is_designer_shade(shade):            # designer_shades OR shade_overrides markers
        return "designer"
    return "outsource"                      # DEFAULT
```

`is_designer_shade` can literally call `template_rules.is_non_argen_shade(shade)` when
`designer_shades` is empty.

### 5.2 The seam change (destination + zip)

Replace the family→path mapping and the `should_zip(...)` call, i.e.
**[case_processor_final_clean.py:489-497](case_processor_final_clean.py:489)**, with:

```python
delivery_mode = resolve_delivery_mode(case_data)
if delivery_mode == "designer":
    target_root = SEND_TO_1_9_PATH     # send-to-designer side
    do_zip = False                     # UNZIPPED (existing behavior)
    log_callback("🧑‍🎓 DESIGNER CASE")
else:  # outsource (DEFAULT)
    target_root = SEND_TO_AI_PATH      # send-to-ai side
    do_zip = True                      # ZIPPED (reuses zip_case_folder)
    log_callback("📦 OUTSOURCE CASE")
```

That is the entire behavioral change. Everything downstream already consumes `target_root` and
`do_zip`:

- `final_output = os.path.join(target_root, case_id)` — unchanged
  ([case_processor_final_clean.py:512](case_processor_final_clean.py:512)).
- The two `if do_zip:` blocks — unchanged
  ([case_processor_final_clean.py:610](case_processor_final_clean.py:610),
  [case_processor_final_clean.py:630](case_processor_final_clean.py:630)). Outsource now exercises
  them; designer skips them exactly as `Send to 1.9` does today.

### 5.3 What to leave in place (conservative)

- **Keep `select_template_path` / `select_template` as-is.** Templates remain correct; `argen_*`
  templates may still be *selected* — they just get delivered per the new mode. (Argen-specific
  `Materials.xml` shade injection at [case_processor_final_clean.py:539](case_processor_final_clean.py:539)
  is keyed off the template name, not the destination, so it is unaffected.)
- **Keep `select_destination`, `resolve_destination_key`, `should_zip`,
  `should_zip_modeless_argen`, `routing_overrides`, `argen_modes` present.** They become dormant on
  the live path but stay for parity/tests/rollback. You may keep calling `select_destination` purely
  for its `route_label_key` log string, or drop the call — not required either way.
- **Do not touch** scan renaming, XML generation, PDF copy, failure handling, `DISABLE_MODELESS`.

### 5.4 Reroute summary table (before → after)

| Case | Before (today) | After (new model) |
| --- | --- | --- |
| Not disqualified (default) | template family → `Send to Argen` or `Send to 1.9`, unzipped | `outsource` → **`Send to AI`, ZIPPED** |
| Doctor on designer list | depended on template/label | `designer` → **`Send to 1.9`, UNZIPPED** |
| Shade is a designer/non-argen shade | depended on template | `designer` → **`Send to 1.9`, UNZIPPED** |
| `has_study` true/false | influenced template *and* destination | influences template only; **no effect on mode** |

---

## 6. Risks / edge cases

1. **"Send to AI" is a new active destination.** Confirm the downstream consumer of `Send to AI`
   expects the zip shape `zip_case_folder` produces (folder as the single top-level entry). Reusing
   that exact function keeps the shape identical to what Argen zipping historically emitted, which
   is the safest choice.
2. **Empty `CC_IMPORTED_ROOT`.** `SEND_TO_AI_PATH` becomes `""` (same failure mode as the other
   roots today). No new risk, but the outsource default now depends on this root being configured —
   worth an explicit check/log.
3. **Doctor-name normalization.** `case_data["doctor"]` is `"First Last"` built at
   [evo_to_case_data.py:119](evo_to_case_data.py:119). Match case-insensitively on a stripped
   substring (as `_contains_any` already does). Beware "Dr." prefixes and multi-word names in the
   YAML list.
4. **Shade normalization.** The shade is singularized in `evo_to_case_data` and re-cleaned
   (strip "Vita Classic-") in `generate_final_xml`. Resolve the mode against the same
   `case_data["shade"]` the case carries, and match uppercased/`contains` like
   `is_non_argen_shade` — otherwise a "C3" written as "Vita Classic - C3" could slip through.
5. **Study/anterior cases now default to outsource + ZIP.** This is the intended decoupling of
   `has_study`, but it is a real change: a `reg_envision_study` case that previously went unzipped
   to `Send to 1.9` will now zip to `Send to AI` unless disqualified. Confirm that is acceptable to
   the outsource consumer.
6. **3Shape branch parity.** The 3Shape branch has its own `if do_zip:` block
   ([case_processor_final_clean.py:630](case_processor_final_clean.py:630)); outsource 3Shape cases
   will now zip. Same reused function — verify a 3Shape outsource case end-to-end.
7. **Designer target folder assumption.** This plan maps designer → `SEND_TO_1_9_PATH` (the existing
   unzipped designer destination). If the designer team actually watches a *different* physical
   folder, that is a one-line change in §5.2 — confirm the folder before shipping.
8. **Vestigial labels.** `route_label_key`, `is_ai_alias_to_designer`, and the ARGEN/SERBIA log
   branches ([case_processor_final_clean.py:500-509](case_processor_final_clean.py:500)) become
   partly unused. Leave them to minimize churn; tidy later.
9. **Config precedence within designer.** Decide and document doctor-vs-shade order (either yields
   `designer`, so order only matters for logging). Recommended: doctor first, then shade.

---

## 7. Recommended phased implementation plan

**Phase 0 — Lock the audit (this document).** No code changes. Agree on: designer target folder
(§6.7), whether `designer_shades` reuses `shade_overrides` markers, and doctor-name list contents.

**Phase 1 — Bounded YAML seam (no runtime wiring yet).**
- Add `delivery_modes` family: `default_*` + `validate_*` in
  [business_rule_schemas.py](infrastructure/config/business_rule_schemas.py), register in the
  unified validator, add to loader defaults, seed both YAML files.
- Add `infrastructure/config/delivery_mode_runtime.py` (`@lru_cache`, `clear_delivery_mode_cache`,
  `is_designer_doctor`, `is_designer_shade`).
- Unit-test the resolver in isolation (doctor match, shade match, default). Nothing calls it in the
  processor yet, so live behavior is unchanged and this phase is safe to land alone.

**Phase 2 — Add `resolve_delivery_mode` helper.** Pure function combining §5.1 with the Phase-1
resolver. Unit-test against representative `case_data` dicts. Still not wired into `process_case`.

**Phase 3 — Flip the seam.** Replace
[case_processor_final_clean.py:489-497](case_processor_final_clean.py:489) with the §5.2 block.
This is the only behavioral change. Keep `select_template_path` and the `if do_zip:` blocks intact.
Validate with a manual run of: (a) a default case → zipped in `Send to AI`; (b) a designer-doctor
case → unzipped in `Send to 1.9`; (c) a designer-shade case → unzipped; (d) a former `has_study`
case → now outsource unless disqualified.

**Phase 4 — Optional cleanup (separate pass, not now).** Retire/relabel dormant Argen routing,
simplify log labels, decide the fate of `SEND_TO_ARGEN_PATH`. Explicitly out of scope here.

---

## 8. Final recommended next implementation pass

Do **Phase 1 only** next: land the bounded `delivery_modes` YAML family + the
`delivery_mode_runtime.py` resolver + seeds + unit tests, with **no** change to `process_case`.

Rationale: it is fully additive and dormant (zero live-behavior change, trivially revertible), it
establishes the beginner-editable YAML surface the whole model depends on, and it lets the
doctor/shade disqualifier logic be tested in isolation before the single-block seam flip in Phase 3.
The reroute itself (Phase 3) is then a ~10-line, one-location change against an already-tested
resolver.

---

### Appendix — seam quick reference

| # | Question | Answer (file:line) |
| --- | --- | --- |
| 1 | Template selection | `select_template_path` [template_selector.py:7](domain/decisions/template_selector.py:7); ladder [template_utils.py:15](template_utils.py:15) |
| 2 | Destination / final folder | category [destination_selector.py:27](domain/decisions/destination_selector.py:27); **physical** [case_processor_final_clean.py:489-494](case_processor_final_clean.py:489); `final_output` [:512](case_processor_final_clean.py:512) |
| 3 | Zip vs non-zip | decide [:497](case_processor_final_clean.py:497) → `should_zip` [:66](case_processor_final_clean.py:66) → [routing_rules.py:79](domain/rules/routing_rules.py:79); execute [:610](case_processor_final_clean.py:610) & [:630](case_processor_final_clean.py:630) |
| 4 | Existing reusable zip | `zip_case_folder` [case_processor_final_clean.py:44](case_processor_final_clean.py:44) (currently dead via `DISABLE_MODELESS` [evo_to_case_data.py:8](evo_to_case_data.py:8)) |
| 5 | New bounded YAML | `delivery_modes` family (two lists) in [business_rule_schemas.py](infrastructure/config/business_rule_schemas.py) + [delivery_mode_runtime.py] (new); shade half may reuse `shade_overrides.non_argen_shade_markers` |
| 6 | Runtime seams to change | one helper `resolve_delivery_mode` + the single block [case_processor_final_clean.py:489-497](case_processor_final_clean.py:489) |
