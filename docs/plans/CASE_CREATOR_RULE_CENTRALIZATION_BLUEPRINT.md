CASE CREATOR RULE CENTRALIZATION BLUEPRINT

## 1. Purpose

Rule centralization is the correct immediate step because Case Creator currently mixes business policy with orchestration, file IO, and UI contracts. Centralizing rules first (while keeping them code-based) creates a stable policy layer that:
- preserves current behavior exactly,
- makes decision precedence explicit and testable,
- reduces risk before any folder/module movement,
- prepares a clean seam for later config externalization.

Doing config externalization before centralization would force simultaneous changes to rule ownership, rule representation, and runtime control flow, which is high-risk for this app’s order-sensitive logic.

---

## 2. Behavior Lock

During centralization, these behaviors must remain identical:

1. **Template precedence order**
   - Existing `if/elif` evaluation order in template selection remains authoritative.
   - No branch reordering, collapsing, or “equivalent simplification.”

2. **Doctor-based behavior**
   - Abby/Dew checks remain exact substring semantics.
   - Brier Creek behavior retains current strict/loose split where it exists now.
   - Signature-doctor matching remains Excel-based exact-name semantics.

3. **Shade behavior**
   - Shade conversion map, shade ranking, Vita-prefix stripping, and dedupe semantics remain unchanged.
   - Non-Argen shade exception criteria (`C3`/`A4`) remain unchanged.

4. **Material/route extraction**
   - Service-description keyword matching and route/material outcomes remain unchanged.
   - Modeless toggle semantics remain unchanged.

5. **Destination behavior**
   - Template-family-to-destination-key mapping stays identical.
   - Current AI routing behavior remains unchanged.
   - Serbia/designer label behavior remains unchanged.

6. **Argen paperwork/contact-model behavior**
   - Current modeless/contact-model related decisions remain unchanged.
   - Current zip/no-zip behavior remains unchanged.

7. **Manual-review gates**
   - Multi-unit gate outcomes and messages remain unchanged.
   - Unsupported material/manual import outcomes remain unchanged.
   - Jotform/manual override behavior remains unchanged.

8. **Scanner behavior**
   - 3Shape/iTero/Sirona scanner heuristics remain unchanged.
   - Existing scan keyword classification behavior remains unchanged.

9. **Naming and suffix behavior**
   - Case suffix generation (`os`, `i`) remains unchanged.
   - Output naming conventions remain unchanged.

10. **Log compatibility lock**
   - Routing-critical backend log text remains unchanged so UI panel routing stays intact.

---

## 3. Proposed Rule Module Responsibilities

### `domain/rules/doctor_rules.py`
**Owns**
- Doctor-name predicates and doctor group membership checks.
- Abby/Dew logic.
- Brier Creek/Serbia-related predicates.
- Signature doctor evaluation wrapper contract (even if Excel read helper remains elsewhere initially).

**Does not own**
- Template selection precedence.
- Destination selection final decision.
- UI log labels.

### `domain/rules/shade_rules.py`
**Owns**
- Shade normalization helpers.
- Shade conversion constants/mappings.
- Shade ranking/priority constants.
- Shade exception predicates (e.g., non-Argen shade checks).

**Does not own**
- Material extraction from services.
- Template final selection.

### `domain/rules/material_rules.py`
**Owns**
- Service-description keyword constants for material/route extraction.
- Material family predicates (`adz` vs `envision`).
- Route family extraction (`argen_envision`, `argen_adzir`, `regular`, modeless flags).
- Material allowlist policy constants used by manual-review decisions.

**Does not own**
- Path resolution or filesystem destination values.
- Template final precedence engine.

### `domain/rules/scanner_rules.py`
**Owns**
- Scanner keyword constants and scanner classification predicates.
- Scan filename keyword buckets (study/prep/antagonist etc.).
- Naming heuristics constants for folder pattern matching.
- iTero scoring helper policy constants.

**Does not own**
- Actual filesystem walking/copying.
- Final scanner source selection side effects.

### `domain/rules/routing_rules.py`
**Owns**
- Route key policies linking template family/category to destination route keys.
- Route labeling helper predicates (designer/serbia/argen/ai labels) as pure policy.
- Route-key-level defaults and fallback constants.

**Does not own**
- Absolute path construction.
- Template selection internals.

### `domain/rules/template_rules.py`
**Owns**
- Template family constants and mapping artifacts.
- Pure predicates for template branch conditions.
- Branch descriptors/rule entries in an ordered form (without executing global precedence itself).

**Does not own**
- Final ordered evaluator loop orchestration.
- XML generation or template file loading.

### `domain/rules/manual_review_rules.py`
**Owns**
- Manual-review gate predicates:
  - multi-unit detection,
  - unsupported material/route gate,
  - Jotform/manual criteria policy.
- Manual-review reason keys and message-key constants.

**Does not own**
- UI-facing message rendering.
- Failure file writing or exception handling.

### `domain/rules/naming_rules.py`
**Owns**
- Case suffix policy (`os`, `i`) and naming helpers.
- Route-sensitive naming conventions.
- Stable output naming token rules.

**Does not own**
- Destination absolute path creation.
- Filesystem writes.

### `domain/rules/rule_models.py`
**Owns**
- Shared typed policy models for rule evaluation IO.
- Decision result structs/enums/keys (e.g., template decision, destination decision, manual review result).
- Standard rule context object (inputs used by selectors).

**Does not own**
- Rule execution logic itself.

---

## 4. Proposed Decision Module Responsibilities

### `domain/decisions/template_selector.py`
**Lives here**
- Ordered evaluation of template rules in exact current precedence order.
- Consumes normalized rule context + rule predicates.
- Returns template decision result (template key/path + matched rule id/branch metadata).

**Not here**
- Raw Evolution parsing.
- Filesystem side effects.
- Destination selection logic.

### `domain/decisions/destination_selector.py`
**Lives here**
- Ordered evaluation from template/routing context to destination route key.
- Applies route-label decisions (designer vs serbia etc.) exactly as current policy.
- Returns destination decision result (route key + label key + rationale code).

**Not here**
- Converting route keys to absolute paths.
- Template branch precedence decisions.

### `domain/decisions/manual_review_selector.py`
**Lives here**
- Ordered evaluation of manual-review gates.
- Returns explicit manual-review decision object:
  - `requires_manual_review` bool,
  - reason key,
  - behavior-preserving message key(s).

**Not here**
- UI message formatting.
- Exception raising/file writes.

---

## 5. Current Logic to Future Module Mapping

### From `template_utils.py`

- `is_signature_doctor` -> `doctor_rules.py`
  - Signature doctor predicate contract (with same matching semantics).
- `is_abby_dew` -> `doctor_rules.py`
- `is_vd_brier_creek` -> `doctor_rules.py`
- `is_non_argen_shade` -> `shade_rules.py`
- `select_template`:
  - branch condition predicates -> `template_rules.py`
  - branch order execution -> `template_selector.py`
  - template family constants -> `template_rules.py`
- `map_material_to_xml` -> `material_rules.py` (or shared material policy helper referenced by XML pipeline)
- `inject_shade_into_materials`:
  - placeholder token constant -> `shade_rules.py` or `template_rules.py`
  - file mutation function remains infrastructure/template pipeline (not rules module).

### From `case_processor_final_clean.py`

- `STUDY_SCAN_KEYWORDS` -> `scanner_rules.py`
- scan keyword buckets in `rename_scans` (`UPPER_KEYWORDS`, `LOWER_KEYWORDS`, `PREP_KEYWORDS`, `ANTAG_KEYWORDS`) -> `scanner_rules.py`
- scanner inference checks (`3shape`, `itero`, `sirona`) -> `scanner_rules.py`
- manual gates in `process_case`:
  - multi-unit detection -> `manual_review_rules.py`
  - unsupported material route gate -> `manual_review_rules.py` + `material_rules.py`
  - Jotform manual branch predicate -> `manual_review_rules.py`
- destination mapping block (template filename -> target root category) -> `routing_rules.py` + execution in `destination_selector.py`
- serbia/designer label block -> `routing_rules.py` + `destination_selector.py`
- `should_zip` policy predicate -> `routing_rules.py` (or `naming_rules.py` if tied to output mode policy; preferred `routing_rules.py`)
- suffix logic (`os`, `i`) -> `naming_rules.py`
- scanner folder pattern helpers for 3Shape (`base_name`, `alt_name`, regex policy) -> `scanner_rules.py` constants/predicates
- iTero nested folder score policy -> `scanner_rules.py`

### From `evo_to_case_data.py`

- `DISABLE_MODELESS` policy toggle -> `material_rules.py` (or `rule_models.py` policy config surface)
- `_SHADE_CONVERSIONS`, `_SHADE_ORDER`, `_SHADE_RANK` -> `shade_rules.py`
- `_tokenize_shades`, `_strip_all_vita_prefixes`, `_normalize_case`, `_canon_key`, `_apply_conversion`, `_best_by_priority`, `_pick_single_shade` -> `shade_rules.py`
- `_route_from_services` -> `material_rules.py`
- `_material_from_services` -> `material_rules.py`
- `_needs_model`, `_is_modeless_from_services` -> `material_rules.py`
- `_first_shade_raw`, `_first_tooth`:
  - tooth extraction helper can remain case-data mapping layer,
  - shade extraction helper paired with `shade_rules.py`.
- route/model/material hint assembly logic in `build_case_data_from_evo`:
  - route/material policy calls into `material_rules.py`,
  - shade normalization calls into `shade_rules.py`.

---

## 6. Rule Family Inventory

### 1) Doctor keyword and doctor group rules
- Current location: `template_utils.py`, `case_processor_final_clean.py`
- Why together: all are name/location textual predicates influencing routing/template behavior.
- Future config candidate: **strong** (keyword lists and doctor-group overrides).

### 2) Signature doctor logic
- Current location: `template_utils.is_signature_doctor`
- Why together: doctor-policy family; affects same decision paths.
- Future config candidate: **strong** (data source likely table/list).

### 3) Shade normalization and shade exception rules
- Current location: `evo_to_case_data.py`, `template_utils.py`
- Why together: all shade transformations + exception checks are one policy domain.
- Future config candidate: **strong** (mapping table + ordered scale + exception list).

### 4) Material and route extraction rules
- Current location: `evo_to_case_data.py`, `case_processor_final_clean.py`
- Why together: service keyword parsing and route/material families form one policy chain.
- Future config candidate: **strong** (keyword mapping + route policy table).

### 5) Template family rules
- Current location: `template_utils.select_template`
- Why together: single precedence-sensitive decision matrix.
- Future config candidate: **strong** (ordered rule list with explicit precedence).

### 6) Destination routing and path-key rules
- Current location: `case_processor_final_clean.py`
- Why together: route family outputs should be key-based policy, path-resolution separate.
- Future config candidate: **strong** (mapping table + override list).

### 7) Argen paperwork and contact-model mode rules
- Current location: `evo_to_case_data.py` (modeless toggle/hints), `template_utils.py`, `case_processor_final_clean.py` (`should_zip`)
- Why together: shared Argen mode policy across template and packaging outcomes.
- Future config candidate: **strong** (mode selector + booleans + override rules).

### 8) Manual-review gate rules
- Current location: `case_processor_final_clean.py`
- Why together: all “do not auto-process” conditions are one policy surface.
- Future config candidate: **strong** (gate list + reason mapping).

### 9) Naming and suffix rules
- Current location: `case_processor_final_clean.py`
- Why together: output identity and naming conventions are one policy domain.
- Future config candidate: **medium** (mapping table likely sufficient).

### 10) Scanner keyword rules
- Current location: `case_processor_final_clean.py`
- Why together: scanner detection/classification keywords and score heuristics are tightly related.
- Future config candidate: **medium-strong** (keyword lists and scoring weights).

---

## 7. Recommended Centralization Order

Safest order (lowest coupling first, precedence-sensitive last):

1. **`shade_rules.py`**
   - Mostly pure transforms/constants from `evo_to_case_data.py`.
   - High value, low side-effect risk.

2. **`doctor_rules.py`**
   - Isolated predicates; minimal IO side effects except signature lookup wrapper.

3. **`material_rules.py`**
   - Centralizes route/material extraction and toggles used across selectors.

4. **`manual_review_rules.py` + `manual_review_selector.py`**
   - Pulls fail-fast gates into explicit selector contract.

5. **`naming_rules.py`**
   - Suffix and naming policy extraction with clear outputs.

6. **`routing_rules.py` + `destination_selector.py`**
   - Route-key mapping and label policy, still separate from filesystem paths.

7. **`scanner_rules.py`**
   - More coupled with file-ops; centralize policy constants/predicates before moving mechanics.

8. **`template_rules.py` + `template_selector.py`**
   - Most precedence-sensitive/highest risk; centralize last after support rule modules are stable.

Why this order:
- Front-load pure predicates and mappings.
- Delay the highest-order decision chain (`select_template`) until supporting policy seams are already deterministic and tested.

---

## 8. Suggested Internal Interfaces

### Core context model (in `rule_models.py`)
- **`RuleContext`** should carry normalized fields already used by current logic:
  - doctor name, signature flag,
  - shade raw/normalized/usable flags,
  - material family, route hints, modeless flags,
  - scanner classification,
  - has_study/is_anterior/is_ai,
  - service summary hints relevant to manual-review gates.

### `doctor_rules` interface shape
- Predicate functions returning booleans and optional reason keys:
  - `is_signature_doctor(context) -> bool`
  - `is_abby_dew(context) -> bool`
  - `is_brier_creek_variant(context) -> bool`

### `shade_rules` interface shape
- Pure transforms + predicates:
  - `normalize_shade(raw) -> NormalizedShadeResult`
  - `is_non_argen_shade(shade) -> bool`

### `material_rules` interface shape
- Extraction + policy:
  - `extract_material_route_hints(services) -> MaterialRouteHints`
  - `is_supported_auto_material_route(hints) -> bool`

### `template_selector` consumption contract
- Consumes `RuleContext` + rule predicates/constants from `template_rules`.
- Returns `TemplateDecision`:
  - `template_key` (logical key),
  - `template_relative_path` (or resolved key to be resolved later),
  - `matched_rule_id`,
  - optional debug fields.

### `routing_rules` vs path resolution
- `routing_rules` should return **route keys**, not absolute paths.
  - Example conceptual keys: `ARGEN`, `DESIGNER_1_9`, `AI_ALIAS_TO_1_9`.
- Absolute path resolution remains outside rule modules (config/infrastructure layer).

### `destination_selector` output
- `DestinationDecision`:
  - `destination_route_key`,
  - `route_label_key` (designer/serbia/argen/ai log category),
  - `matched_rule_id`.

### `manual_review_selector` representation
- `ManualReviewDecision`:
  - `requires_manual_review: bool`
  - `reason_key: str | None`
  - `message_key: str | None`
  - optional `detail_key` (for second line detail messages).

### `naming_rules` output
- `NamingDecision`:
  - `case_id_suffix: str`
  - `final_case_id: str`
  - `naming_flags` (e.g., argen/iTero markers).

Interface design principle:
- selectors return stable decision objects with keys/reasons;
- rendering (strings, paths, side effects) stays outside selectors.

---

## 9. Future Config Readiness Notes

### Doctor rules
- Likely future type: **keyword list + doctor-group override list**
- Candidate status: strong.

### Signature doctor logic
- Likely future type: **mapping table/list source reference**
- Candidate status: strong.

### Shade rules
- Likely future type: **mapping table + ordered enum scale + exception keyword list**
- Candidate status: strong.

### Material/route rules
- Likely future type: **service-keyword mapping table + route mode selector**
- Candidate status: strong.

### Template rules
- Likely future type: **ordered override rule list**
- Candidate status: strong.

### Destination/routing rules
- Likely future type: **route-key mapping table + destination override list**
- Candidate status: strong.

### Argen contact-model/paperwork mode
- Likely future type: **boolean toggle(s) + mode selector**
- Candidate status: strong.

### Manual-review gates
- Likely future type: **gate rule list with reason mappings**
- Candidate status: strong.

### Naming/suffix rules
- Likely future type: **small mapping table**
- Candidate status: medium.

### Scanner keyword rules
- Likely future type: **keyword lists + scoring weight map**
- Candidate status: medium-strong.

### Remain internal code candidates
- Highly technical filesystem traversal and copy/zip mechanics (not business policy) should likely remain internal code.

---

## 10. First Execution Pass Recommendation

Safest first code-change pass after this blueprint:

1. Create empty module skeletons:
   - `domain/rules/rule_models.py`
   - `domain/rules/shade_rules.py`
   - `domain/rules/doctor_rules.py`
   - `domain/rules/material_rules.py`
   - `domain/decisions/manual_review_selector.py`
2. Move only pure constants and pure predicate/transform helpers first:
   - shade conversion constants/helpers from `evo_to_case_data.py`,
   - doctor predicates from `template_utils.py`,
   - material/route extraction helpers from `evo_to_case_data.py`.
3. Keep old call sites and behavior by using compatibility imports/wrappers.
4. Add parity tests/assertions for moved helpers before any selector-order migration.

This first pass centralizes low-risk rule primitives only; it intentionally avoids moving template precedence engine, destination mapping engine, scanner mechanics, and output path logic until primitive rules are validated.

