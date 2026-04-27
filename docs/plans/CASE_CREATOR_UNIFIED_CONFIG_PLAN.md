# CASE CREATOR UNIFIED CONFIG PLAN

## 1. Purpose

Case Creator already exposes **four validated YAML families** under `business_rules/v1/` (`doctor_overrides`, `shade_overrides`, `routing_overrides`, `argen_modes`), merged at runtime into a single **effective config** in memory. That is the right foundation, but it fragments the **user and LLM editing experience**: beginners must find multiple files, understand family boundaries, and avoid cross-file inconsistencies.

Consolidating into **one human- and LLM-editable file** (still validated against the same bounded semantics) delivers:

- **One place** to review “what the app can be told to do” for exposed business rules.
- **One copy-paste artifact** for ChatGPT-style assistants, with a **standard instruction block** at the top so edits stay safe and schema-faithful.
- **Easier operational discipline**: diff one file, ship one file to support, teach one mental model.
- **Preserved safety**: the runtime continues to reject unknown keys, unknown template keys, and invalid enums; the unified file is a **presentation and packaging** layer, not a loosening of validation.

This document is **planning only**—no code migration yet.

## 2. Definition of done

The desired final state:

| Criterion | Description |
|-----------|-------------|
| **One exposed editable file** | Operators and docs refer to a single primary file (e.g. `case_creator_rules.yaml` or `business_rules.yaml`) as the editable source for all **currently exposed** business-rule families. |
| **One top-of-file LLM prompt** | A contiguous, copy-paste-friendly block at the top instructs an LLM how to edit the file safely (see §8). |
| **One runtime source of truth** | After load + validate, the app derives the same four logical families (`doctor_overrides`, `shade_overrides`, `routing_overrides`, `argen_modes`) for existing runtime seams—**or** a single internal dict with those keys—without requiring users to maintain four separate files on disk. |
| **LLM workflow** | The user copies the **entire** file into an LLM, states the desired change; the LLM **asks clarifying questions** if needed, then returns the **full updated file** in **one** fenced code block, with no invented keys and stable structure where possible. |
| **Migration safety** | Existing deployments can move from split YAML to unified file **without behavior change** when content is equivalent and validation passes. |

## 3. Recommended overall architecture

**Concept:** A **single YAML document** with a **fixed top-level shape** and **named sections** that map 1:1 to today’s `SUPPORTED_FAMILIES` and validators.

**Loader behavior (future):**

1. Resolve path via existing `CASE_CREATOR_BUSINESS_RULES_DIR` / packaged `business_rules/v1/` discovery (narrow extension: prefer `case_creator_rules.yaml` when present, else fall back to current multi-file layout for backward compatibility during transition).
2. **Parse once** → dict.
3. **Extract sections** → pass each section through the **existing** `validate_*` functions (or a thin `validate_unified_config` that delegates to them).
4. Build **`effective_config`** identical in shape to today’s preview (`doctor_overrides`, `shade_overrides`, `routing_overrides`, `argen_modes`).
5. **Caches** (`doctor_override`, `argen_modes`, etc.) continue to read from that effective snapshot—no change to domain logic if the merged result is unchanged.

**LLM prompt:** Lives **inside the same file** as YAML comments **or** as a dedicated `llm_instructions` string key that the app **ignores at runtime** (stripped before validation) **or** validated as a non-functional metadata field. Prefer **comments-only** for the instruction block so the entire document remains “pure YAML + comments” and the parser never sees fake keys.

**Alternative (if comments are insufficient):** A sibling file `case_creator_rules.LLM_PROMPT.txt` is **not** desired per this plan’s “one file” goal; keep instructions in-file as comments.

## 4. Proposed unified file structure

Top-level order (human-friendly, stable):

1. **`# === LLM EDITING INSTRUCTIONS ===`**  
   Multi-line comment block (§8)—the block a user copies together with the rest of the file **or** the LLM is told to read first.

2. **`# === HUMAN NOTES ===`**  
   Optional freeform comments (restart reminders, org-specific notes). Not parsed.

3. **`unified_version`** (integer)  
   Schema version of the **envelope** (e.g. `1`). Distinct from per-section `version` if kept.

4. **`enabled`** (boolean, optional)  
   Global kill-switch for “all exposed rules” (optional; can defer to per-section `enabled` only).

5. **`doctor_overrides`**  
   Same logical content as today’s `doctor_overrides.yaml` (version, enabled, rules).

6. **`shade_overrides`**  
   Same as today’s shade file.

7. **`routing_overrides`**  
   Same as today’s routing file (`template_family_route_overrides`).

8. **`argen_modes`**  
   Same as today’s `argen_modes` (`contact_model_mode`, etc.).

**Sections evaluated but optional for v1 of unified file:**

| Section | Notes |
|---------|--------|
| **Template override rules** | Already folded into **doctor** outcomes / `template_override_key`; do **not** duplicate as a separate top-level family unless future schema splits “template policy” from “doctor match.” |
| **Destination override rules** | Same as **routing_overrides** today—keep under `routing_overrides`. |
| **Label override rules** | Schema already allows `route_label_override_key` on doctor `action` in some paths; if label overrides expand, they either stay under **doctor** rules or gain a small bounded **`label_overrides`** section later—**plan:** start with doctor-embedded only to avoid scope creep. |

**Metadata:** `unified_version`, optional `last_reviewed`, optional `environment` comment—**comments only** or ignored keys **must** be stripped or namespaced so validation never accepts arbitrary nesting under functional keys.

## 5. Allowed adjustable behaviors

Explicit list of what should remain **user-adjustable** in the unified file (aligned with current bounded exposure):

**Doctor overrides**

- Global `enabled` and per-rule `enabled`.
- **Match:** `contains_any`, `contains_all`, predicates (`abby_dew`, `vd_brier_creek`) where supported.
- **Simple rules:** `when` (bounded clauses), `action.template_override_key` (known template keys only).
- **Multi-outcome rules:** `outcomes[]` with the same bounded `when` / `action` (gated at runtime by `CASE_CREATOR_DOCTOR_OUTCOMES_LIVE` as today).
- **Label-related doctor action** where schema permits: `route_label_override_key` (allowed label enum only).

**Shade overrides**

- `non_argen_shade_markers` list (bounded validation).
- Any other fields already in `validate_shade_overrides` (rules list if present).

**Routing overrides**

- `template_family_route_overrides`: `family_key` ∈ {argen, ai, study, anterior}, `destination_key` ∈ {argen, 1_9} (or string alias as today).

**Argen modes**

- `contact_model_mode`: `off` | `on` (and legacy normalization as today).
- `enabled` for the family.

**Not in scope for “adjustable” expansion in this plan**

- New predicate types, new `when` fields, new template keys, or free-form conditions—those require **schema + code** changes first.

## 6. Behaviors that should remain internal

Keep **code-owned** (not exposed in the unified editable file) unless a future pass deliberately promotes them:

- **Core template selection graph** in `template_utils.select_template` (Abby/VD branches, study/signature ordering, etc.)—YAML mirrors or overrides **narrow** seams only.
- **Serbia / Brier Creek label routing** beyond existing bounded doctor label keys—no “merge broad label behavior into outcomes” without a dedicated design pass.
- **Manual review / unsupported material** gates, allowlists, and import rejection policy.
- **Filesystem paths**, template paths, Evolution API URLs, credentials.
- **Arbitrary DSL** for rules (no eval, no raw SQL, no unbounded expressions).
- **Hint-route rewriting** removed from active path—contact mode remains the narrow `off`/`on` seam documented elsewhere.

## 7. Proposed schema design

**Envelope + embedded families** (illustrative layout only):

```yaml
# === LLM EDITING INSTRUCTIONS ===
# (full text of §8 as comments)

# === HUMAN NOTES ===
# Save file and restart app after editing.

unified_version: 1

doctor_overrides:
  version: 1
  enabled: true
  rules: []

shade_overrides:
  version: 1
  enabled: true
  non_argen_shade_markers: ["C3", "A4"]
  rules: []

routing_overrides:
  version: 1
  enabled: true
  template_family_route_overrides: []

argen_modes:
  version: 1
  enabled: true
  contact_model_mode: "off"
```

**Validation strategy:**

- Either **validate each subtree** with existing functions after extracting keys, or introduce `validate_unified_config(doc)` that:
  - Requires keys `doctor_overrides`, `shade_overrides`, `routing_overrides`, `argen_modes` (or allows omit = default).
  - Rejects unknown **top-level** keys (except ignored metadata if explicitly allowlisted).
- **Comments:** Preserved for humans/LLMs; YAML parser drops them on round-trip—document that LLM should **preserve comment blocks** when possible when returning the full file.

**Versioning:** Bump `unified_version` only when envelope or required sections change; per-family `version` stays aligned with `SCHEMA_VERSION` in code.

## 8. LLM instruction prompt design

Place at the **very top** of the file as a **YAML comment block** (user copies entire file into the LLM). Conceptual text (final wording can be tuned during implementation):

```text
You are helping edit the Case Creator unified business rules YAML below.

Rules you MUST follow:
1. Output MUST be the complete updated YAML file in a single fenced code block (markdown ```yaml ... ```).
2. Do NOT add keys, sections, or comments that are not already present unless the user explicitly asks for a new rule row inside an existing list (e.g. a new doctor rule).
3. Do NOT invent template names, route families, destination keys, or contact_model_mode values other than "off" or "on".
4. Preserve all existing comments and section order when possible; if you must remove a comment, say so in one short note at the top of your reply outside the code block.
5. If the user request is ambiguous or would break validation (unknown template key, wrong type), ask concise follow-up questions FIRST and do NOT output a file until resolved.
6. Never include file system paths, API secrets, or non-YAML content inside the file.
7. After editing, the file must remain valid YAML and must match the Case Creator unified schema (bounded doctor/shade/routing/argen rules only).

The user will paste this entire file below your instructions in the same message.
```

**User workflow:** Paste file → add sentence: “Change X to Y.” → LLM clarifies or returns full file.

## 9. Migration plan from current split files

**Phase A — Preparation (no behavior change)**

- Add `CASE_CREATOR_UNIFIED_CONFIG_PLAN.md` (this doc) and align team on envelope shape.
- Implement a **one-time merge script** (dev-only) or documented manual steps: concatenate four files into one template with comments.

**Phase B — Dual-read (backward compatible)**

- Loader checks for `case_creator_rules.yaml` (name TBD) in `business_rules/v1/`.
- **If unified file exists and validates:** parse sections → populate `effective_config`.
- **Else:** existing multi-file discovery per family (current behavior).

**Phase C — Cutover**

- Ship default repo layout with **either** unified only **or** unified + deprecated split files (loader prefers unified).
- Update operator docs: “edit one file.”

**Phase D — Deprecation**

- After one release cycle with no dual-file edits, remove split-file preference from docs; optionally delete split files from template repo (keep loader fallback for old installs).

**Data migration safety:** Byte-for-byte semantic equivalence: load old four files → build unified → validate → load unified → compare normalized effective dicts in a test.

## 10. Runtime integration plan

1. **Discovery:** Extend `discover_business_rules_base_dir` logic (or loader) to prefer unified filename first.
2. **Read:** Single `yaml.safe_load` for unified; or keep four reads if unified missing.
3. **Validate:** `validate_unified_config` → delegates to `validate_doctor_overrides`, etc., on each subtree.
4. **Preview / errors:** `BusinessRuleConfigPreview` gains optional `source: unified | split` and reports section-level errors with paths like `doctor_overrides.rules[2]`.
5. **Caches:** `clear_*` unchanged; they already key off preview reload.
6. **UI (future):** Single “edit page” loads/saves the one file; export still YAML text.

## 11. Validation and safety plan

| Topic | Approach |
|-------|----------|
| **Schema** | Strict: unknown top-level keys rejected; each family uses existing validators. |
| **Fallback** | If unified file invalid: log/report errors; fall back to split files if present **or** in-memory defaults (current behavior for missing files). |
| **Conflicts** | If both unified and split files exist during transition: **unified wins** after successful validation; log warning if split also present. |
| **LLM output** | Recommend app **does not** auto-apply pasted LLM output; user saves file; app validates on next load. Optional future: “validate only” CLI. |
| **Secrets / paths** | Schema continues to forbid path-like fields in rule families. |
| **Restart** | Human note in file: restart app after edit (current pattern). |

## 12. Recommended phased implementation plan

| Phase | Scope |
|-------|--------|
| **1** | Add `validate_unified_config` + tests; loader dual-read behind feature flag or filename presence; no removal of split files. |
| **2** | Ship unified template in repo; migrate bundled `business_rules/v1` content into one file; keep split files as copies or delete from repo with loader fallback. |
| **3** | Update Case Creator UI / docs to single edit surface; add “export unified” from old installs (tooling). |
| **4** | Remove split-file discovery from loader (major version or ops sign-off). |

## 13. Recommended first implementation pass

**Safest first code-change pass:** Implement **validation-only** `validate_unified_config` in `business_rule_schemas.py` (or adjacent module) plus **unit tests** that:

- Accept a dict matching the envelope and delegate to existing validators.
- Reject unknown top-level keys.
- Prove **equivalence**: merged four canonical fixtures equal unified fixture in normalized output.

**Do not** change the loader or runtime behavior until validation and tests are green—then add **opt-in** dual-read (unified file if present).

---

## Final chat summary

1. **Unified file concept:** One YAML document with a top comment block for LLM instructions, then **`doctor_overrides`**, **`shade_overrides`**, **`routing_overrides`**, and **`argen_modes`** subtrees matching today’s validated shapes; runtime still builds the same effective config.
2. **Main sections:** LLM/human comment headers, optional envelope `unified_version`, the four existing families; template/destination/label adjustments stay **inside** those families (doctor + routing) unless a later pass adds a dedicated bounded section.
3. **Still internal:** Full `template_utils` branching, manual review / unsupported material policy, paths/secrets, unbounded DSL, broad Serbia label logic not yet promoted to schema.
4. **Safest first pass:** Add **`validate_unified_config` + tests** with no loader change; then dual-read unified file when present.
