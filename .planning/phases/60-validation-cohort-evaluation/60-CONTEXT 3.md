# Phase 60: Validation & Cohort Evaluation - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 60 validates the expanded v2.4 solution space at cohort level. It measures whether the completed Phase 54-59 work materially changes movement potential, path diversity, and actionable recommendation quality, while preserving the locked v2.2 trust baseline.

This phase owns:
- cohort-level measurement of movement-potential changes after the expanded action space, institution/hybrid lane, multi-path generation, and deterministic rendering are in place
- population-level evidence for path diversity, non-utilization action coverage, institution/hybrid path availability, and selected-path mix
- required evaluation runs and evidence artifacts that make those results auditable
- summary tables and evaluation outputs that compare the current expanded runtime against the already-shipped trust baseline
- explicit regression proof that winner integrity, contender quality, selected-surface consistency, and operator packet coherence remain intact during cohort evaluation

This phase does not own:
- trust-rule redesign
- planner-semantic redesign
- new action taxonomy work
- new feature/action mappings
- new DICE action types
- new heuristic or institution action types
- rendering redesign
- decision-policy redesign

Guardrail:
- Phase 60 is an evaluation phase, not a capability-expansion phase. It must measure the current system faithfully, not widen or reinterpret it.

</domain>

<decisions>
## Implementation Decisions

### 1. Exact Scope Of Phase 60

- Phase 60 starts after the system already supports:
  - canonical action taxonomy
  - deterministic feature -> action mapping
  - expanded DICE action space
  - heuristic / institution lane
  - deterministic grouped paths
  - deterministic action/path rendering
- The job of Phase 60 is to answer one narrow question:
  - did the expanded solution space create materially different cohort-level movement evidence without breaking trust?
- Phase 60 must treat the current runtime as fixed and evaluate it through the existing batch / calibration / artifact pipelines.
- Evaluation must be additive:
  - new cohort metrics and evidence outputs are allowed
  - changing how plans are generated, ranked, validated, or rendered is not allowed

### 2. Problem Statement

- Up through Phase 59, v2.4 expanded the reachable recommendation space and made that space intelligible:
  - more canonical actions
  - more mapped features
  - more DICE-supported action types
  - institution-assisted and hybrid lanes
  - grouped alternative paths
  - deterministic rendering
- But none of that matters unless cohort evidence shows the expanded space actually changes:
  - movement potential
  - the availability of non-utilization strategies
  - the rate of institution/hybrid paths
  - the diversity of selected routes
  - the selected-path distribution across cohorts
- The v2.3 movement diagnosis already established that threshold-only and outcome-rule-only changes did not safely create movement. Phase 60 must test whether the capability expansion from Phases 54-59 changes that diagnosis.
- The phase fails if it produces impressive-looking new metrics at the expense of trust regressions or if it mixes evaluation with new capability work.

### 3. First-Class Validation Lenses

#### Movement potential

- This is the primary lens for Phase 60.
- It must answer whether the expanded action/path space creates more cohort-level safe movement than the previously shipped trust baseline.
- Required measurements:
  - change in non-empty contender share
  - change in approved-or-conditional contender share
  - change in execution-aware value distribution
  - change in movement bottleneck diagnosis, especially whether `structural_cohort_limited` softens for any meaningful cohort slice
- Movement potential is measured at population level, not through anecdotal per-customer examples.

#### Path diversity

- Phase 60 must treat multi-path evidence as first-class, not as a side metric.
- Required measurements:
  - `multi_path_rate`
  - `path_count`
  - `rankable_path_count`
  - `action_diversity_index`
- This lens exists to prove whether Phase 58 pathing plus Phase 57 institutional/hybrid lanes created meaningfully different routes rather than cosmetic alternatives.

#### Non-utilization action rate

- This is a first-class metric because v2.3 and pre-v2.4 behavior were dominated by utilization-heavy routes.
- Required measurement:
  - `non_utilization_action_rate`
- This lens is the clearest proof that the system widened beyond the old utilization-centric recommendation space.

#### Institution / hybrid path rate

- This lens measures whether the new institution-assisted and hybrid capability actually appears in valid cohort outputs.
- Required measurements:
  - `institution_action_rate`
  - `institution_assisted_path_count`
  - `hybrid_path_count`
  - share of selected paths that are `institution_assisted` or `hybrid`
- This lens must remain descriptive only. It must not be used to justify relaxing trust gates for institution-bearing candidates.

#### Selected path distribution

- Phase 60 must elevate selected-path mix to a phase-level evidence output.
- Required measurements:
  - selected path distribution across `customer_only`, `institution_assisted`, `hybrid`
  - selected-plan source distribution (`internal`, `dice`, `rule`)
  - selected-path distribution by relevant cohort slices
- This lens exists to answer whether the winner surface actually changes, not just the candidate pool.

### 4. Required Cohort Runs And Evidence Outputs

#### Required cohort populations

- Phase 60 must evaluate at least these populations:
  - canonical denied population
  - high-risk denied population
  - near-threshold / approval-like mix already used by the batch selection and calibration flows
- If the codebase already defines those slices in existing selection/evaluation artifacts, Phase 60 should reuse them rather than create new cohort logic.

#### Required run structure

- Phase 60 must run the current expanded runtime through the existing batch evaluation path and produce full evidence artifacts for:
  - whole denied cohort
  - high-risk denied subset
  - pilot-mixed / cohort-selected evaluation slice where current collection and calibration artifacts are already standardized
- Each run must preserve the current trust gates and output contract.
- The phase should compare:
  - current v2.4 expanded runtime evidence
  - existing trust/movement summaries from the already-established calibration and movement-guardrail flows
- Phase 60 is allowed to add baseline-comparison tables, but not a new alternate planner or alternate decision regime.

#### Required evidence outputs

- One canonical cohort-evaluation summary JSON/Markdown output that pulls together:
  - movement potential metrics
  - path diversity metrics
  - selected-path distribution
  - trust-regression status
- Existing artifact families must be reused and extended where needed:
  - candidate-quality summary artifacts
  - movement guardrail evidence
  - customer artifact collection calibration outputs
  - batch evaluation summary outputs
- Evidence must remain export-first and file-based.

### 5. Required Artifacts And Summary Tables

#### Required artifacts

- Phase 60 must produce or extend:
  - batch cohort metrics summary
  - candidate-quality summary artifact
  - selected-path distribution artifact
  - movement-potential summary artifact
  - movement guardrail summary / review artifact
  - one Phase 60 verification artifact that explicitly states whether the expanded action space changed cohort-level movement evidence

#### Required summary tables

- **Movement Potential Table**
  - population
  - non-empty contender share
  - approved-or-conditional contender share
  - mean execution-aware value
  - dominant movement bottleneck

- **Path Diversity Table**
  - population
  - `multi_path_rate`
  - mean `path_count`
  - mean `rankable_path_count`
  - mean `action_diversity_index`

- **Action Coverage Table**
  - population
  - `non_utilization_action_rate`
  - `institution_action_rate`
  - offer-ready contender share
  - approval-shell-only share

- **Selected Path Distribution Table**
  - population
  - selected `customer_only` share
  - selected `institution_assisted` share
  - selected `hybrid` share
  - selected source distribution (`internal`, `dice`, `rule`)

- **Trust Regression Table**
  - suite / invariant
  - status
  - evidence source
  - notes

#### Required written summary

- The human-readable summary must answer:
  - did movement potential improve at all?
  - where did it improve?
  - was the improvement mostly from non-utilization routes, institution/hybrid routes, or both?
  - did selected-path mix actually shift?
  - did any trust-critical output regress?

### 6. Acceptance Criteria

- Phase 60 is only complete when all of the following are true:
  - required cohort runs finish successfully using the current expanded runtime
  - first-class movement, path-diversity, action-coverage, and selected-path-distribution evidence artifacts are written
  - summary tables exist for denied and high-risk denied populations at minimum
  - the evidence explicitly states whether `structural_cohort_limited` remains dominant or meaningfully softens
  - trust-regression proof still passes for:
    - winner integrity
    - contender quality
    - selected-surface consistency
    - operator packet coherence
  - no new action types, planner semantics, or trust-logic changes are introduced under the guise of evaluation
- Phase 60 does **not** require a positive business outcome to pass.
- It may validly conclude either:
  - "expanded space created measurable movement improvement"
  - or "expanded space still does not materially break the structural bottleneck"
- What matters is that the conclusion is evidence-backed and trust-safe.

### 7. Recommended Implementation Order

- **Step 1:** Freeze the evaluation boundary
  - confirm the phase will use the current v2.4 runtime exactly as shipped through Phase 59
  - confirm no planner / trust / action-space changes are allowed inside Phase 60

- **Step 2:** Standardize cohort populations
  - identify the canonical denied, high-risk denied, and pilot-mixed / calibration-ready slices already used in the repo
  - lock those as the authoritative Phase 60 evaluation populations

- **Step 3:** Consolidate metric sources
  - reuse existing path metrics from `recourse/pathing.py`
  - reuse candidate-quality and selected-path metrics from `run_batch_recourse_eval.py`
  - reuse movement diagnosis from `evaluation/decision_calibration.py`
  - reuse artifact collection outputs from `run_customer_artifact_collection.py`

- **Step 4:** Build one cohort-evidence assembly layer
  - add the missing summary artifact(s) and tables that combine movement, path diversity, action coverage, and selected-path distribution in one place

- **Step 5:** Run evaluation and capture evidence
  - execute required cohort runs
  - materialize machine-readable outputs plus one operator-readable Markdown summary

- **Step 6:** Run trust-regression proof in parallel with cohort evidence generation
  - keep this as an explicit gate, not an implicit assumption

- **Step 7:** Write final interpretation
  - state clearly whether v2.4 changed cohort-level movement evidence
  - state clearly whether the trust baseline remained intact

### Claude's Discretion

- Exact filenames for the Phase 60 aggregate summary artifacts
- Whether the final evidence assembly lives closer to `run_batch_recourse_eval.py`, `run_customer_artifact_collection.py`, or a small evaluation helper module
- Exact cohort-table formatting, as long as the required evidence categories remain first-class and audit-friendly

</decisions>

<specifics>
## Specific Ideas

- Treat Phase 60 as the answer to the v2.3 question: "Did expanding the recommendation space change the structural bottleneck, or only make the current no-safe-uplift diagnosis more richly explained?"
- Prefer explicit population tables over one blended global average.
- Keep movement diagnosis and trust-regression reporting side-by-side so no one can mistake higher path diversity for safe business movement unless both are true.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/recourse/pathing.py`: already computes `path_count`, `rankable_path_count`, `multi_path_flag`, `action_diversity_index`, `non_utilization_action_rate`, `institution_action_rate`, and selected-path identity fields.
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`: already aggregates candidate-quality population metrics, selected-path category rates, and candidate-source breakdowns for denied and high-risk denied populations.
- `credit-coach/src/credit_coach/evaluation/decision_calibration.py`: already owns movement-guardrail diagnosis, bottleneck summary, and review Markdown generation.
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`: already assembles calibration artifacts, movement-guardrail outputs, operator briefing summaries, and collection-level evidence files.

### Established Patterns
- Evaluation artifacts are export-first, file-based, and paired as machine-readable JSON/CSV plus human-readable Markdown.
- Movement diagnosis is already framed through `dominant_movement_bottleneck` and `movement_guardrail_summary`; Phase 60 should extend that seam rather than replace it.
- Selected-path distribution is already serialized through `selected_path_type`, `selected_path_id`, and related summary fields; Phase 60 should consume those as evidence instead of reconstructing path labels post hoc.
- Trust regressions are already enforced by explicit pytest suites; Phase 60 should keep using suite-based proof rather than inventing qualitative trust checks.

### Integration Points
- Batch-level cohort evaluation should connect to `run_batch_recourse_eval.py` candidate-quality summary and batch outputs.
- Collection-level evidence should connect to `run_customer_artifact_collection.py` calibration and summary artifact generation.
- Movement interpretation should connect to `build_movement_guardrail_evidence(...)` and `build_movement_guardrail_review_markdown(...)`.
- Final phase verification should connect to the existing trust suites covering selected-surface consistency, operator packet coherence, customer artifact parity, and winner integrity.

</code_context>

<deferred>
## Deferred Ideas

- Any attempt to loosen trust rules if cohort movement remains weak
- Any attempt to add new action types or new institution strategies based on Phase 60 findings
- Any planner or decision-policy redesign motivated by Phase 60 results

Those are follow-on phases, not part of Phase 60 itself.

</deferred>

---
*Phase: 60-validation-cohort-evaluation*
*Context gathered: 2026-04-04*
