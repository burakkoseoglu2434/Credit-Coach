# Phase 58: Multi-Path Recourse Generation - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 58 adds a deterministic path layer above the existing validated candidate pool so the system can expose multiple distinct, internally coherent, rankable recourse paths per customer instead of treating every contender as part of one flat list.

This phase owns:
- deterministic grouping of already-generated safe candidates into distinct recourse paths
- first-wave path typing for:
  - `customer_only`
  - `institution_assisted`
  - `hybrid`
- deterministic path identity, path signature, and near-duplicate suppression
- path-level ranking based on existing validated plan scoring semantics
- additive schema and artifact support for path catalogs and selected-path traceability
- batch and per-customer metrics that measure whether multi-path generation is actually happening
- regression proof that winner integrity, DICE contender quality, selected-surface consistency, and operator packet coherence remain intact

This phase does not own:
- planner redesign
- decision-policy redesign
- trust-contract redesign
- relaxation of validity, contender, or lane-quality gates
- probabilistic clustering, fuzzy grouping, or similarity models
- new action taxonomy work
- new feature-to-action mapping work
- new DICE safety semantics
- new institution-rule semantics beyond what Phase 57 already locked

Guardrail:
- Phase 58 must transform the existing safe candidate space into multiple deterministic solution paths without changing which individual plans are valid, eligible, or winner-selectable.

</domain>

<decisions>
## Implementation Decisions

### 1. Exact Scope Of Phase 58

- Phase 58 introduces a deterministic path-construction layer after all existing candidate-generation and candidate-gating steps have already run.
- Path construction operates on already-serialized `PlanRecord` contenders; it does not generate new action semantics and it does not bypass existing plan validation.
- The phase must produce:
  - path membership for eligible plans
  - one representative plan per path
  - a stable path ranking
  - additive artifacts that expose all distinct paths for a customer
- The phase must preserve current single-winner behavior while making the winner traceable to one selected path.
- Phase 58 is complete when path construction is deterministic, duplicate-resistant, auditable, and visible in both single-customer artifacts and batch evaluation outputs.

### 2. Problem Statement

- The current system can already generate multiple safe candidates from internal, DICE, and rule lanes, but it still treats them as one flat contender pool.
- That flat pool is sufficient for choosing one winner, but it is not sufficient for showing the customer or the operator that multiple different solution routes exist.
- As a result, materially different strategies can be hidden behind score ordering, and near-duplicate candidates can crowd out genuinely different alternatives.
- Phase 58 solves this by turning the post-gate candidate pool into a deterministic catalog of distinct recourse paths, where each path represents one coherent way forward and remains rankable under existing scoring rules.

### 3. Canonical Path Types To Support First

#### `customer_only`

- Definition:
  - all actionable movement in the path is customer-executable
  - no action in the representative plan requires institutional approval, institution-generated terms, or institution-side offer acceptance
- Typical membership:
  - internal plans
  - DICE plans that serialize to customer-controlled canonical actions
- Classification rule:
  - representative plan contains zero institution-owned actions
  - representative plan contains zero hybrid-owned actions
  - representative plan has `offer_plan = false`

#### `institution_assisted`

- Definition:
  - the path thesis depends primarily on institution-owned actions or institution-generated terms
  - the customer may need to accept or respond, but the main movement depends on institutional action
- Typical membership:
  - `credit_limit_adjustment`
  - `installment_plan`
  - `settlement_discount`
- Classification rule:
  - representative plan contains at least one institution-owned actionable step
  - representative plan contains zero customer-owned actionable steps that materially change the thesis
  - representative plan is not classified as hybrid

#### `hybrid`

- Definition:
  - the path requires material customer execution and material institution cooperation in the same coherent route
- Typical membership:
  - `debt_consolidation`
  - mixed customer-paydown plus institution-term paths when both are required to define the route
- Classification rule:
  - representative plan contains at least one customer-owned actionable step and at least one institution-dependent or hybrid-owned actionable step
  - or the representative plan contains one hybrid-owned canonical action whose semantics already encode both sides

Lock:
- Path type is derived from canonical action ownership and offer dependency semantics, not from generation lane alone.
- `plan_source` remains important provenance, but it must not be reused as `path_type`.

### 4. Rules For Grouping Candidate Actions And Plans Into Distinct Paths

- Grouping happens after:
  - recommendation-validity enforcement
  - DICE contender gating
  - rule contender gating
  - planner-quality contender classification
- Only non-empty candidates may enter path grouping.
- Only actionable candidates may produce rankable paths.
- `APPROVAL_SHELL_ONLY` candidates may remain visible in raw diagnostics, but they do not count as rankable Phase 58 paths.

#### Path-building unit

- The grouping unit is the full `PlanRecord`, not a free-floating action fragment.
- A path is a set of one or more plans that express the same strategic thesis using the same dominant action identity and materially the same movement pattern.

#### Deterministic grouping key

- Every eligible plan must be assigned a deterministic path signature derived from:
  - `path_type`
  - ordered canonical actionable `action_key` set
  - ordered `action_owner` mix
  - ordered primary target `metric_key` set
  - offer dependency pattern:
    - `offer_plan`
    - `offer_maturity`
    - `requires_institutional_approval`
  - dominant institutional family when present:
    - `offer_family`
    - `dominant_offer_type`
- The signature must ignore volatile scoring fields such as score, predicted PD, or execution probability so reruns do not create new path identities for the same strategic route.

#### Coherence rule

- Plans may belong to the same path only when they share one dominant thesis.
- A dominant thesis is preserved when the candidate differences are limited to bounded strategy or horizon variation around the same canonical action bundle.
- Plans must split into different paths when any of the following changes:
  - path type changes
  - dominant canonical action bundle changes
  - primary target metric set changes materially
  - institution dependency pattern changes materially
  - hybrid vs institution-assisted semantics change

#### Path representative

- Each path must expose one representative plan.
- The representative is the best-ranked actionable plan inside that path under the existing plan-ordering semantics.
- Path rank is the global order of representatives, not a new scoring policy.

### 5. How To Prevent Near-Duplicate Paths

- First dedupe at the plan level using existing candidate controls and the new path signature.
- Then dedupe at the path level using deterministic equivalence, not fuzzy distance.

#### Duplicate collapse rules

- Two plans collapse into the same path when all of the following match:
  - same `path_type`
  - same normalized actionable `action_key` bundle
  - same primary target `metric_key` bundle
  - same approval / offer dependency state family
  - same dominant institution family when applicable
- Differences in horizon, strategy label, score, or minor target magnitude do not create a new path if the strategic route is unchanged.

#### Mandatory split rules

- Paths must remain separate when any of the following differs:
  - customer-only vs institution-assisted vs hybrid category
  - utilization-relief route vs delinquency-resolution route vs consolidation route
  - rankable offer path vs non-offer customer path
  - institution offer family changes in a way the operator would interpret as a different negotiation route

#### Duplicate guardrail

- Phase 58 must not emit multiple ranked paths that only restate the same action thesis with cosmetic variation.
- If only one deterministic thesis survives duplicate collapse, the customer legitimately has one path, not a forced multi-path output.

### 6. Path Identity In Schema And Artifacts

- Path identity must be additive and traceable at both plan level and path level.

#### Plan-level additive fields

- Add to `PlanRecord`:
  - `path_id`
  - `path_type`
  - `path_signature`
  - `path_rankable_flag`
  - `path_representative_flag`
  - `path_rank`
- These fields annotate how a plan participates in pathing without changing any existing trust or scoring fields.

#### Path-level record

- Introduce a new path record schema, for example `RecoursePathRecord`, containing:
  - `path_id`
  - `customer_id`
  - `path_type`
  - `path_signature`
  - `rankable_flag`
  - `path_rank`
  - `representative_plan_id`
  - `member_plan_ids`
  - `member_source_counts`
  - `action_keys`
  - `primary_metric_keys`
  - `offer_plan`
  - `offer_maturity`
  - `selected_path_flag`
- The path record is the canonical unit for alternative-path artifacts.

#### Artifact representation

- Add a dedicated customer artifact such as `customer_paths.json`.
- Add path columns to `candidate_pool.csv/json` and `plans.json`.
- Add selected-path summary fields to `metrics.json`.
- Keep existing roadmap and operator packet surfaces backward-compatible by adding path context rather than replacing current selected-plan fields.

### 7. How Paths Coexist With Existing Winner Selection

- Global winner selection remains plan-based and unchanged.
- The existing decision policy still runs over the eligible actionable candidate plans.
- Path construction must happen before artifact finalization, but it must not replace `choose_best_plan`.
- After the best plan is selected:
  - derive `selected_path_id` from the best plan
  - mark that path as `selected_path_flag = true`
  - expose the remaining ranked paths as alternatives
- The selected winner should also be the representative plan of its path, because representative selection uses the same within-path ranking semantics.

Lock:
- Phase 58 does not introduce path-level winner voting, path-level policy thresholds, or path-level overrides.
- Paths are an additive organization layer over valid plans, not a new decision engine.

### 8. Required Outputs And Artifacts

- Code outputs:
  - deterministic path typing utility
  - deterministic path-signature builder
  - path-grouping and representative-selection module
  - artifact writers for path outputs
- Customer artifacts:
  - `customer_paths.json`
  - augmented `plans.json`
  - augmented `candidate_pool.csv`
  - augmented `candidate_pool.json`
  - additive selected-path summary in `customer_roadmap.json`
  - additive path metrics in `metrics.json`
- Batch outputs:
  - path-aware evaluation fields in batch recourse outputs
  - metrics for:
    - `multi_path_rate`
    - `action_diversity_index`
    - `non_utilization_action_rate`
    - `institution_action_rate`
    - `selected_plan_category_distribution`
- Test outputs:
  - deterministic path grouping tests
  - path dedupe tests
  - representative-selection tests
  - selected-winner-to-selected-path consistency tests
  - regressions for trust baseline invariants

### 9. Acceptance Criteria

- A customer with materially different safe candidate theses receives multiple distinct path records, not just multiple flat candidates.
- A customer with only one surviving strategic thesis receives exactly one path after duplicate collapse.
- `customer_only`, `institution_assisted`, and `hybrid` classification is deterministic and reproducible from canonical action semantics.
- Near-duplicate candidates collapse into one path when the strategic thesis is unchanged.
- Different strategic routes remain separated even when they share some features or score closely.
- Every rankable path has exactly one actionable representative plan.
- The selected winner remains selected by the existing plan-level decision policy.
- `selected_path_id` always matches the selected winner's `path_id`.
- Winner integrity, DICE contender quality, selected-surface consistency, and operator packet coherence continue to pass unchanged.
- Batch evaluation exposes the new path metrics and proves path generation is not merely duplicating utilization-only variants.

### 10. Recommended Implementation Order

1. Add additive schema for plan-level path fields and the new path-level record.
2. Implement deterministic path typing from canonical action ownership and offer semantics.
3. Implement deterministic path-signature construction and duplicate-collapse rules.
4. Build a path-grouping module that accepts already-gated candidate plans and returns:
   - grouped paths
   - representative plans
   - selected-path traceability
5. Integrate path annotations into `run_recourse.py` without changing current winner-selection logic.
6. Add `customer_paths.json` and extend existing artifacts with path columns and selected-path summary fields.
7. Extend batch recourse evaluation with path-aware metrics and reporting.
8. Add focused unit tests for typing, grouping, dedupe, and representative selection.
9. Run regression suites covering winner integrity, DICE quality, selected-surface consistency, operator packet coherence, and candidate diversity.

### Claude's Discretion

- Exact module split for path utilities versus artifact helpers
- Exact naming of the new path record class and writer helpers
- Exact column order for path fields in CSV and JSON outputs
- Exact metric field names beyond the locked requirement-level names, as long as they remain additive and deterministic

</decisions>

<specifics>
## Specific Ideas

- Pathing should be built as a deterministic organization layer on top of existing validated `PlanRecord` objects rather than as a replacement for candidate generation.
- The cleanest first implementation is likely one new pathing module plus additive schema/artifact updates, not a planner rewrite.
- The selected customer surface should remain single-path-first, with alternative paths exposed as additive context rather than a new primary UX contract.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- [`PlanRecord` schema](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py): already carries planner-quality, offer, and lane-gating metadata that Phase 58 can reuse instead of inventing a new trust object.
- [`annotate_plan_planner_quality`, `filter_empty_contenders`, `filter_selectable_contenders`, `choose_best_plan`](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py): already define the post-gate candidate semantics that path construction must sit above.
- [`run_recourse.py`](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): already owns candidate pool assembly, winner selection, metrics building, and artifact writing, so it is the main integration point for path outputs.
- [`run_batch_recourse_eval.py`](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py): will need the same path logic and metrics surfaced at batch level.

### Established Patterns

- Lane-specific quality gates happen before planner contention and must remain authoritative.
- Contender selection is based on actionable `PlanRecord` objects, not abstract action clusters.
- Candidate pool metrics are already additive and summary-oriented, which makes path metrics a natural extension.
- Selected-surface and operator-packet logic already expects one chosen plan, so Phase 58 must annotate that plan's path rather than replace the selection contract.

### Integration Points

- Candidate assembly to path grouping:
  - after `validated + dice_records + rule_records`
  - after DICE and rule planner-eligibility splits
  - after planner-quality contender annotation
- Winner traceability:
  - after `choose_best_plan`
  - before roadmap / metrics / customer artifact serialization
- Artifact extension:
  - `_plan_to_row`
  - `_build_bundle_plans_df`
  - `_build_customer_metrics_summary`
  - `write_customer_artifact_bundle`
- Batch extension:
  - batch evaluation summaries that currently reason about candidate diversity and source mix

</code_context>

<deferred>
## Deferred Ideas

- Customer-facing UX redesign for browsing multiple paths
- Path-specific narrative generation beyond lightweight additive summaries
- Path-level experimentation, probabilistic ranking, or learned clustering
- New action families or planner-policy changes driven by what path metrics reveal

</deferred>

---

*Phase: 58-multi-path-recourse-generation*
*Context gathered: 2026-04-04*
