# Phase 59: Action Semantics Rendering - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 59 renders the now-stable semantic action and path outputs into deterministic, human-readable recommendation text.

This phase owns:
- deterministic rendering of selected recommendation text from canonical action and primary-target truth
- deterministic rendering of institution-side condition text where institution support or approval matters
- deterministic path-level summary rendering for selected and alternative paths
- wording separation for customer-facing vs operator-facing surfaces
- suppression of weak, generic, or semantically empty recommendation text
- additive schema and artifact fields needed to carry rendered action/path text safely
- regression proof that rendering stays aligned with selected-plan truth, selected-path truth, and operator packet coherence

This phase does **not** own:
- planner redesign
- decision-policy redesign
- contender-gating redesign
- winner-selection redesign
- path-identity redesign
- probabilistic or fuzzy copy generation
- new action taxonomy, feature mapping, DICE logic, or institution-rule logic
- broader cohort evaluation beyond rendering-focused regressions

Guardrail:
- Rendering must remain a deterministic consumer of shipped truth contracts, not a second engine that invents recommendation meaning.

</domain>

<decisions>
## Implementation Decisions

### 1. Exact Scope Of Phase 59

- Phase 59 starts after Phase 58 path construction and after the existing selected-plan decision has already been made.
- The phase renders already-owned truth from:
  - canonical `action_key`
  - canonical `action_owner`
  - primary numeric target payload
  - offer / approval truth
  - selected plan projection
  - path identity and path rank
- Rendering should improve legibility and semantic precision, not change what the system selected or why it selected it.
- The main output is one deterministic render layer for:
  - selected recommendation text
  - selected institution condition text
  - alternative path summaries
  - operator-facing path wording

### 2. Problem Statement

- The system can now generate safe semantic actions, safe DICE candidates, safe institution-rule candidates, and grouped multi-path outputs.
- But the human-readable wording still reflects older narrative defaults that were built before:
  - canonical action ownership was explicit
  - institution/hybrid lanes existed as first-class paths
  - multi-path artifacts were available
- As a result:
  - selected recommendation text can be serviceable but not yet canonical-action-aware
  - alternative paths exist structurally but do not yet have one deterministic summary language
  - customer and operator surfaces risk diverging in wording detail even when they share the same truth
- Phase 59 fixes that by making rendering deterministic, action-aware, path-aware, and contract-safe.

### 3. Rendering Targets

#### Selected recommendation text

- Own one canonical render path for the selected action recommendation.
- The selected recommendation must still come from the selected winning plan, not from path-level reinterpretation.
- The default customer-facing selected action should remain concise, directive, and metric-aware.

#### Alternative path summaries

- Every rankable path should expose one deterministic summary derived from its representative plan.
- Alternative-path summaries are additive context; they do not replace selected-plan truth.
- Non-rankable approval-shell paths may carry diagnostic wording, but they must not read like executable recommendations.

#### Customer-facing wording

- Customer wording must say what to do, what target matters, and whether institution support is required.
- Customer wording must stay:
  - clear
  - concise
  - non-judgmental
  - free of internal model jargon

#### Operator-facing wording

- Operator wording may be more explicit about:
  - path type
  - approval dependency
  - offer maturity
  - why the path is distinct
- Operator wording must still be derived from the same engine-owned render truth as customer wording.

### 4. Rules For Numeric Phrasing

- Numeric phrasing remains deterministic and template-driven.
- Prefer `current -> target` wording when both values are finite and semantically meaningful.
- Do not lead with abstract deltas when a before/after statement is available.
- Use one primary numeric statement per rendered action or path summary.
- Metric labels must come from one canonical map keyed by `metric_key`, not from ad hoc freeform strings.

#### Metric phrasing rules

- Percent-style metrics:
  - render as `from X% to Y%` or `keep below Y%`
  - example: `Reduce credit utilization from 63% to below 45%.`
- Currency-style metrics:
  - render as `reduce from X units to Y units` when both ends are known
  - otherwise render as `reduce by X units`
- Count-style metrics:
  - render as `from 3 accounts to 1 account` when the before/after truth exists
- Verification-state / boolean-style metrics:
  - render as state transition language, not `0 -> 1`
  - example: `Complete income verification.`
- Timing hints remain separate from the main action sentence unless the target itself is time-based.

### 5. Rules For Before/After Target Rendering

- If `current_value` and `target_value` are both valid:
  - render current first, then target
  - do not append a duplicate delta unless operator-specific wording explicitly needs it
- If only the target is valid:
  - render a target-only imperative
- If the target is threshold-shaped:
  - prefer `below`, `above`, or `at least` wording over awkward equality phrasing
- If the metric is categorical or stateful:
  - use the end-state wording only
- If no meaningful target can be rendered:
  - suppress numeric phrasing rather than emitting generic filler

### 6. Rules For Customer vs Institution vs Hybrid Wording

#### `customer_only`

- First sentence is a direct customer action.
- Institution language should be absent unless it is genuinely needed as a supporting note.
- The recommendation must read as executable by the customer today.

#### `institution_assisted`

- Customer-facing wording must stay honest about dependency:
  - `if eligible`
  - `if approved`
  - `when institution support is available`
- Do not phrase institution-assisted paths like guaranteed approvals.
- Operator wording may name the institution dependency more explicitly than customer wording.

#### `hybrid`

- The rendered path must name both sides of the route.
- Default shape:
  - sentence one: customer action or customer preparation
  - sentence two: institution-side support needed for the route to fully land
- Hybrid wording must not collapse into pure customer language or pure institution language.

### 7. Rules For Suppressing Weak Or Generic Language

- Do not emit default-visible recommendation text that only says:
  - `improve profile`
  - `take action`
  - `follow the plan`
  - `make progress`
  - `recommended path`
  - `improve outcome`
- Every rendered action recommendation must contain at least one of:
  - canonical action identity
  - primary metric movement
  - concrete state-change wording
- Every rendered path summary must contain:
  - path type or dependency posture
  - dominant action thesis
  - one concrete expected movement or condition
- If a path or action cannot meet those standards:
  - suppress the weak text
  - keep the structural artifact
  - expose a bounded diagnostic marker instead of fake business wording

### 8. Rules For Path-Level Summary Generation

- Path summaries are rendered from the representative plan only.
- Path member variants must not each produce separate business summaries.
- One deterministic path summary should include:
  - path label or path-type posture
  - dominant action thesis
  - one primary metric or state transition
  - institution dependency statement when relevant
- Alternative paths must be rendered in `path_rank` order.
- The selected path and alternative paths must use the same rendering primitives so wording style stays aligned.

#### First-wave path summary shapes

- `customer_only`:
  - `Reduce revolving pressure by lowering utilization from X to Y.`
- `institution_assisted`:
  - `If approved, use an installment structure to make monthly payments more manageable.`
- `hybrid`:
  - `Lower revolving pressure and pair it with institution support so the repayment path becomes sustainable.`

These are render patterns, not freeform prose examples; Phase 59 should encode them as deterministic templates.

### 9. Consistency With Selected Projection

- The selected recommendation projection from Phase 47 remains authoritative for selected consumer truth.
- Phase 59 may improve how that projection text is generated, but it must not create a second selected-text source.
- `selected_recommendation_text` and `selected_institution_condition` must be derived from the same step/path render payload used in:
  - `customer_roadmap.json`
  - flat selected summary
  - operator packet short view
- Operator packets must continue consuming the selected projection rather than regenerating recommendation language independently.
- Empty-state behavior remains frozen:
  - if `selection_outcome = no_valid_winner`, do not render fake selected recommendation text
  - do not generate persuasive alternative-path copy that implies executable paths exist when none are rankable

### 10. Required Outputs And Artifacts

- Code outputs:
  - deterministic action render helpers keyed by canonical action and primary target truth
  - deterministic path-summary render helpers keyed by `RecoursePathRecord`
  - customer/operator wording adapters that reuse one render core
- Customer artifacts:
  - upgraded `narrative.steps[*].primary_recommendation`
  - upgraded `narrative.steps[*].institution_condition`
  - rendered summaries in `customer_paths.json`
  - additive path-summary fields in `customer_roadmap.json`
  - additive selected render fields in flat summary outputs only if derived from the same selected projection contract
- Operator artifacts:
  - operator packet short-view wording stays aligned with selected projection
  - additive operator-facing path summary text where useful, without changing packet truth ownership
- Schema outputs:
  - additive localized path-summary fields on path-level records
  - optional additive render-version fields for traceability

### 11. Acceptance Criteria

- `REND-01`
  - selected recommendation text is metric-aware and canonical-action-aware
  - before/after phrasing is deterministic where data supports it
- `REND-02`
  - no broken, generic, or semantically empty recommendation text appears in selected or path summaries
  - institution-assisted and hybrid wording stay dependency-honest
- `REND-03`
  - selected plans produce coherent narrative summaries
  - selected-path and alternative-path text are aligned with the same render core
  - selected-surface consistency and operator packet coherence remain green

### 12. Recommended Implementation Order

1. Harden the render primitive layer in `messaging.py` around canonical action, action owner, and primary-target phrasing.
2. Add deterministic render helpers for path summaries using `RecoursePathRecord` and representative-plan truth.
3. Extend schema additively for localized path-summary fields and optional render-version traceability.
4. Integrate rendered path summaries into `run_recourse.py` and customer artifacts without changing selected-plan ownership.
5. Keep `operator_review.py` consuming the same selected render outputs rather than generating parallel copy.
6. Add focused rendering tests for:
   - metric phrasing
   - institution/hybrid dependency wording
   - weak-language suppression
   - selected-path consistency
7. Re-run selected-surface and operator-packet regressions before closing the phase.

</decisions>

<specifics>
## Specific Ideas

- Phase 59 should build forward from Phase 35, not replace it.
- The existing `action_summary` / `primary_recommendation` / `institution_condition` separation is still the right shape.
- The biggest new capability is path-aware rendering, not broader narrative creativity.
- The best first-wave output is:
  - stronger step-level primary recommendation phrasing
  - clear institution condition phrasing
  - deterministic alternative-path summary cards
- Website-facing layout or UX redesign is out of scope here; Phase 59 only owns engine-side rendering truth.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
  - already owns deterministic narrative composition
  - already formats primary numeric targets, timing hints, offer state, and step narratives
  - is the primary implementation seam for Phase 59
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already defines `LocalizedText`, `RoadmapStepNarrative`, and `RecoursePathRecord`
  - is the natural home for additive path-render fields
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
  - already projects selected recommendation text and selected institution condition from narrative steps
  - already writes `customer_paths.json`
  - is the correct integration seam for rendered path summaries
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
  - already consumes selected projection and narrative steps
  - should remain a consumer, not become a second rendering engine

### Established Patterns

- Rendering is already engine-owned and deterministic.
- Product-safe wording already separates:
  - customer action
  - institution condition
  - offer narrative
  - technical reveal
- Selected projection is already a frozen trust seam from Phase 47.
- Operator packet coherence is already a frozen trust seam from Phase 48.

### Integration Points

- Primary engine seams:
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/ops/operator_review.py`
- Key regression suites:
  - `credit-coach/tests/test_messaging.py`
  - `credit-coach/tests/test_selected_surface_consistency.py`
  - `credit-coach/tests/test_operator_packet_coherence.py`
  - `credit-coach/tests/test_customer_artifact_collection.py`
  - new Phase 59 rendering-focused tests for path summaries and generic-language suppression

</code_context>
