# Phase 45 — Winner Integrity Hard Stop Context

**Last updated:** 2026-03-24
**Status:** Discussed and locked
**Milestone:** `v2.2 Winner Integrity & Consumer Consistency`
**Requirements:** `WINT-01`, `WINT-02`, `WINT-03`

<domain>
## Phase Boundary

Phase 45 does **not** redesign:

- Phase 40.5 deterministic decision ownership semantics
- Phase 41 cohort / calibration math or reporting structure
- Phase 42 planner-quality and source-mix semantics
- Phase 42.5 recommendation validity taxonomy or warning posture
- Phase 43 operator packet semantics
- any decision thresholds or approval-rate tuning

Phase 45 **does** own:

- a hard-stop winner-selection contract that guarantees invalid recommendations can never become the selected winner
- deterministic fallback behavior when the preferred valid pool collapses
- explicit `no_valid_winner` behavior instead of fake invalid winner selection
- selected-surface integrity for `best_plan_id`, `selected_best_flag`, and no-valid-winner artifact truth
- additive integrity diagnostics and validation outputs needed to prove the hard-stop works

Guardrails:

- invalid winner prevention is the only north star for this phase
- widening changes candidate-set scope only; it does not redesign ranking semantics
- single-customer and batch flows must keep one chooser contract
- operator packet cleanup, dice competitiveness tuning, and approval uplift remain later-phase work

</domain>

<decisions>
## Implementation Decisions

### 1. Hard-Stop Selection Contract

- Canonical hard rule:
  - `invalid recommendation can never become selected winner`
- This rule has no source exception:
  - `dice`
  - `internal`
  - `rule`
  - `fallback`
- `warning` contenders remain rankable with existing penalty semantics.
- `invalid` contenders are not allowed to survive winner selection.
- When validity filtering empties the preferred pool, the planner must widen only across valid contenders in this fixed order:
  1. valid `constraint_eligible + non_rejected`
  2. valid `constraint_eligible`
  3. valid `non_rejected`
  4. valid `all`
- The planner must never fall back to the original invalid pool after validity filtering.

### 2. No-Valid-Candidate Contract And Downstream Integrity

- Planner return contract should become explicit rather than relying on a silent `None`.
- Preferred shape:
  - `best_plan: PlanRecord | None`
  - `selection_meta: {...}`
- If no valid contender exists, canonical outcome is:
  - `best_plan = None`
  - `selection_outcome = no_valid_winner`
- In `no_valid_winner` cases, raw truth must be explicit and null-safe:
  - `best_plan_id = null`
  - `best_plan_source = null`
  - `best_action_count = 0`
  - `plan_contract_pass = 0`
  - `recommendation_validity_status = null`
  - `selection_outcome = no_valid_winner`
  - `no_valid_candidate_available = 1`
- Fake invalid residuals must not leak into summary truth.
- `customer_plans.csv` semantics in `no_valid_winner` state:
  - every row has `selected_best_flag = 0`
  - this is expected and must not be treated as parity corruption
- Hard integrity rule:
  - if `best_plan_id != null`
  - exactly one row must have `selected_best_flag = 1`
  - that row must have `plan_id == best_plan_id`
  - that row's `recommendation_validity_status != invalid`
  - `best_plan_source` must match that same selected row

### 3. Widening Semantics, Ranking Integrity, And Batch Symmetry

- Widening changes only the candidate set; it does not redesign ranking.
- Existing ranking semantics remain intact inside the widened valid pool:
  - current planner ordering
  - source tie-break
  - denied-mode sorting
  - warning penalty
  - planner-quality ordering
- Canonical trace field:
  - `selection_stage`
- Allowed values:
  - `preferred_valid`
  - `widened_constraint_valid`
  - `widened_non_rejected_valid`
  - `widened_any_valid`
  - `no_valid_winner`
- Supporting diagnostics should remain additive:
  - `invalid_candidates_removed_count`
  - `preferred_pool_invalid_exhausted`
  - `selected_from_widened_valid_pool`
- `choose_best_plan(...)` remains the single owner for both:
  - single-customer flows
  - batch / collection flows
- Batch and single-customer selection must consume the same:
  - widening logic
  - `selection_meta`
  - `no_valid_winner` semantics
- `warning` plans remain valid contenders in widened pools.
- `no_valid_winner` should only happen when no `valid` or `warning` contender remains.

### 4. Artifact Contract Additions And Validation Surface

- Minimum additive artifact fields for raw summary and flat metrics:
  - `selection_outcome`
  - `selection_stage`
  - `invalid_candidates_removed_count`
  - `preferred_pool_invalid_exhausted`
  - `no_valid_candidate_available`
  - `selected_from_widened_valid_pool`
- `selection_outcome` vocabulary is intentionally small:
  - `selected_valid_winner`
  - `no_valid_winner`
- `customer_plans.csv` keeps existing validity fields and aligns `selected_best_flag` to the no-valid-winner contract.
- Required collection-level aggregate lenses:
  - `selected_invalid_winner_count`
  - `selected_invalid_winner_rate`
  - `no_valid_winner_count`
  - `widened_valid_selection_rate`
  - `preferred_pool_invalid_exhaustion_rate`
- Validation posture is mandatory and phase-exit critical:
  - unit tests for widened-valid and no-valid-winner planner behavior
  - integration tests for `best_plan_id` / `selected_best_flag` / parity semantics
  - large-sample reruns for:
    - `pilot_mixed`
    - `risk_band_balanced`
    - `offer_needed_balanced`
- Primary exit criterion:
  - `selected_invalid_winner_count = 0`
- Additional exit checks:
  - `selected_invalid_winner_rate = 0`
  - `0` selected `dice` winners with `recommendation_validity_status = invalid`

### Claude's Discretion

- Exact Python type used for the explicit planner result wrapper
- Whether helper diagnostics are stored as a dataclass, typed dict, or schema model
- Whether additive collection lenses are emitted as both counts and rates by default or rate is derived from the count
- Exact naming of internal helper functions, as long as public artifact vocabulary remains locked

</decisions>

<specifics>
## Specific Ideas

- The current dominant bug must be treated as a fail-open selection bug, not a scoring bug.
- The hard-stop should preserve existing scoring and ranking semantics inside valid pools rather than introducing a new planner.
- `selection_outcome` should stay compact while `selection_stage` carries the detailed widening path.
- `no_valid_winner` is a valid expected-empty state, not an implicit corruption state.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py): single chooser owner; already carries constraint preference, non-rejected preference, validity filtering, empty-contender filtering, and ranking logic
- [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py): canonical invalid/warning filtering seam; taxonomy is already locked and should be consumed, not redesigned
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): summary and raw artifact writer that currently mirrors best-plan truth into roadmap outputs
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py): batch path that also consumes `choose_best_plan(...)` and must stay symmetric
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): `selected_best_flag`, parity checks, and collection summary seam
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py): already supports `best_plan_id` absence through existing no-viable-plan bridge semantics

### Established Patterns
- Planner-quality and validity layers are additive consumers of one selected winner, not alternate decision systems.
- Raw summary remains the canonical source that downstream flat and consumer surfaces mirror.
- Integrity diagnostics are typically added as explicit summary fields and rolled up into collection metrics rather than inferred in UI layers.
- Batch and single-customer logic should share one chooser implementation rather than reimplementing selection behavior.

### Integration Points
- `choose_best_plan(...)` needs the hard-stop and widening contract
- `run_recourse.py` and `run_batch_recourse_eval.py` need to consume the explicit selection result contract
- `run_customer_artifact_collection.py` parity rules need an expected-empty selected-best state for `no_valid_winner`
- raw summary / flat metrics serialization needs additive `selection_outcome` and `selection_stage` fields

</code_context>

<deferred>
## Deferred Ideas

- Dice-lane competitiveness and policy comparison beyond winner integrity belong to Phase 46.
- Operator packet blocker/action coherence belongs to Phase 48.
- Threshold widening and approval-rate optimization remain out of scope until selected-winner integrity is proven.

</deferred>

---

*Phase: 45-winner-integrity-hard-stop*
*Context gathered: 2026-03-24*
