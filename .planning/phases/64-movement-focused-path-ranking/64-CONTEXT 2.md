# Phase 64: Movement-Focused Path Ranking - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 64 refines how already-valid plans are ranked for recoverable customers so the selected path better reflects realistic threshold-reaching movement.

This phase owns:
- a recoverable-only movement-focused ranking refinement
- additive movement ranking fields and reason codes
- deterministic tie-break behavior for threshold progress vs realism
- additive propagation of ranking truth into runtime and audit artifacts

This phase does not own:
- planner or chooser redesign
- winner-integrity, validity, or gate-contract changes
- threshold policy redesign
- new recourse modes
- new action types, new data sources, or model retraining
- customer/operator-facing narrative redesign

Guardrail:
- ranking may change only after the existing trust and validity filters have done their work
- limited mode remains unchanged and informational
- false confidence is worse than conservative under-selection

</domain>

<decisions>
## Implementation Decisions

### Ranking scope and activation
- First-wave movement-focused ranking should apply only when all of the following are true:
  - denied-target ranking context is active
  - `recoverable_flag = true`
  - `recourse_mode = "full"`
- Limited mode should remain unchanged and informational in this phase.
- Non-recoverable customers should continue to use the existing empty-state-safe Phase 63 posture with no Phase 64 ranking behavior layered on top.
- If a customer is not in recoverable/full mode, the current shipped ranking posture should remain the fallback.
- Phase 64 should therefore be implemented as a recoverable-only additive ranking layer, not as a global planner rewrite.

### Ranking contract shape
- The minimal additive contract should be:
  - one new path/plan-level `movement_score`
  - one heuristic `threshold_reach_probability`
  - a small ordered rule set that consumes them
- Do not replace the existing planner tuple sort with a monolithic new score-only system.
- Recommended ranking order for recoverable/full-mode candidates:
  - existing trust and validity gates remain first
  - threshold-reaching advantage comes next
  - `movement_score` breaks ties among similarly valid candidates
  - realism / simplicity / path-type preference resolves near-ties
  - existing source tie-break logic remains last
- This keeps the ranking easy to audit because each layer answers a different question:
  - is it valid?
  - can it realistically close the gap?
  - how strong is the movement?
  - if movement is similar, which path is more executable and less dependency-heavy?

### Canonical movement-ranking signal set
- The minimal deterministic signal set that should directly affect ordering is:
  - `approval_gap`
  - `threshold_reach_possible`
  - `threshold_reach_probability`
  - `expected_pd_improvement`
  - `plan_execution_probability`
  - `approval_dependent_plan_probability`
  - action-set complexity / simplicity
  - path type
- These signals should remain diagnostic-only in first wave:
  - `recoverability_score`
  - `path_count`
  - `rankable_path_count`
  - path diversity or semantic richness on their own
- Rationale:
  - `recoverability_score` is a customer-level gating signal, not a path-level selector
  - path count and diversity help explain the search space but should not outrank better threshold progress
  - ranking should optimize realistic movement, not variety for its own sake

### Threshold-reaching priority
- `threshold_reach_possible` should be a first-class ranking advantage for recoverable/full-mode customers.
- Phase 64 should also emit a more graded heuristic:
  - `threshold_reach_probability`
- First-wave interpretation:
  - paths with stronger threshold-reaching evidence should rank above paths that merely look rich or diverse
  - paths that do not materially close the approval gap should be demoted, not necessarily deleted
- The ranking should explicitly resist selecting cosmetically strong but movement-weak paths.
- Recommended practical policy:
  - if one path can plausibly close the threshold gap and another cannot, the threshold-reaching path should usually win
  - when multiple paths look threshold-capable, the one with better realistic movement should win
  - when no path looks threshold-capable, the phase may still rank within the valid pool, but movement strength should remain explicit and conservative

### Simplicity versus aggressiveness
- Phase 64 should optimize for **best realistic movement**, not raw maximum movement in isolation.
- If a more complex hybrid or institution-assisted path materially improves threshold reach relative to a simpler customer-only path, it may rank higher.
- But simplicity should not be only a last-resort tie-breaker; it should be a primary negative input inside `movement_score`.
- First-wave policy:
  - threshold-reaching advantage outranks simplicity when the movement gap is material
  - simplicity should decide near-ties and prevent marginally stronger but much harder paths from winning
  - complexity penalties should be deterministic and based on already-shipped realism signals:
    - action count / action-group count
    - mean and peak difficulty
    - follow-through readiness
    - approval dependency
- This means the selected path should represent the strongest believable movement, not the most ambitious-looking plan.

### Path-type treatment
- Path types remain:
  - `customer_only`
  - `institution_assisted`
  - `hybrid`
- First-wave policy:
  - when movement is comparable, prefer `customer_only`
  - `institution_assisted` and `hybrid` should pay a mild ranking penalty unless they deliver a clear threshold-reaching advantage
  - institution-heavy paths should not outrank customer-only paths on cosmetic richness or path diversity alone
- Path type should not be a hard exclusion in Phase 64.
- It should instead behave like a realism prior:
  - self-executable wins when movement is similar
  - dependency-heavy wins only when it provides materially better recoverable-customer movement

### Deterministic movement policy
- Phase 64 should add a recoverable/full-mode movement policy, not a new planner regime.
- Recommended deterministic policy:
  - keep the current validity / contender / winner integrity ordering unchanged
  - among valid candidates in recoverable/full mode, compute `movement_score`
  - set `threshold_reach_priority_flag = 1` for paths that are plausibly threshold-reaching
  - prefer higher `threshold_reach_priority_flag`
  - then prefer higher `movement_score`
  - then prefer simpler, less dependency-heavy paths
  - then preserve existing source and cost tie-break behavior
- `movement_score` should favor:
  - stronger expected threshold progress
  - stronger execution realism
  - fewer / simpler actions
  - lower institutional dependency when movement is otherwise close
- `movement_score` should not reward path variety, semantic richness, or multi-path abundance directly.

### Additive output contract
- Minimum additive field set for Phase 64:
  - `movement_score`
  - `threshold_reach_probability`
  - `threshold_reach_priority_flag`
  - `movement_rank_reason_codes`
  - `selected_path_movement_strength`
- `selected_path_movement_strength` should stay compact and categorical:
  - `strong`
  - `moderate`
  - `weak`
- `movement_rank_reason_codes` should explain why a path ranked where it did, with small stable vocabulary such as:
  - `THRESHOLD_REACH_PRIORITY`
  - `THRESHOLD_REACH_UNLIKELY`
  - `HIGH_EXPECTED_MOVEMENT`
  - `EXECUTION_REALISM_ADVANTAGE`
  - `SIMPLE_ACTION_SET_ADVANTAGE`
  - `CUSTOMER_ONLY_TIEBREAK`
  - `INSTITUTION_DEPENDENCY_PENALTY`
- Additive surfaces to update first:
  - runtime summary / selected path summary
  - `metrics_summary`
  - flat customer metrics / collection artifacts
  - cohort evidence and evaluation outputs
- Customer-facing and operator-facing wording should stay unchanged in this phase unless existing technical/debug surfaces already expose additive fields safely.

### Claude's Discretion
- Exact formula details for `movement_score`, as long as threshold-reaching progress dominates and the implementation stays deterministic.
- Exact calibration of “material movement advantage” versus “near-tie”, as long as the planner remains conservative.
- Whether the new ranking layer is encoded as a dedicated helper or integrated into existing recoverable/full-mode sort-key assembly, as long as auditability stays clear.

</decisions>

<specifics>
## Specific Ideas

- Keep limited mode completely unchanged in Phase 64.
- Treat recoverable/full mode as the only surface where movement-focused ranking is allowed in the first wave.
- Prefer a small ordered rule set over a broad ranking rewrite.
- Movement relevance should matter more than path variety.
- Threshold-reaching evidence should outrank semantically rich but movement-weak plans.
- Customer-only paths should win near-ties, but institution-assisted or hybrid paths may still win when they provide clearly better realistic movement.
- Preserve trust contracts at all costs; ranking must sit inside the existing winner-integrity and validity envelope.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py): already contains layered deterministic ranking helpers (`_denied_sort_key`, `_execution_rank_penalty`, `_execution_defensibility_score`, `_phase_aware_priority_score`) that can host a recoverable/full-mode movement refinement without replacing chooser structure.
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py): already computes the path-relevant primitives this phase needs, including `expected_pd_improvement`, execution probability, approval-dependent probability, difficulty, follow-through readiness, and trajectory consistency.
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): already passes `denied_mode`, `segment_context`, and `denied_objective_cfg` into both `choose_best_plan(...)` and `build_recourse_path_records(...)`, which is the cleanest seam for a recoverable/full-mode ranking layer.
- [pathing.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/pathing.py): already uses `choose_best_plan(...)` to pick representative plans per path and to rank path representatives, so Phase 64 can improve both plan and path selection by changing one shared ranking seam.
- [recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py): already provides the canonical `approval_gap`, `threshold_reach_possible`, `recoverable_flag`, and reason-code fields that Phase 64 should consume rather than reinterpret.
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) and [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already propagate selected-path and gate truth into flat artifacts and cohort evidence, making them the right downstream surfaces for additive movement-ranking fields.

### Established Patterns
- The repo prefers ordered deterministic sort keys over opaque composite ranking logic.
- Trust-critical screening happens before richer ranking; Phase 64 should keep that ordering.
- Phase 63 established `recoverable_flag` plus `recourse_mode=full|limited` as the canonical routing seam, so Phase 64 should consume those fields rather than inventing a second activation rule.
- Existing planner logic already balances expected improvement against execution realism, which means Phase 64 should refine and retune that balance for recoverable/full-mode customers rather than starting over.
- Customer and operator narratives are treated separately from technical truth; this phase should propagate ranking facts additively and leave wording unchanged.

### Integration Points
- Add the recoverable/full-mode branch inside [choose_best_plan(...)](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py) so the same logic governs selected plan choice and path-representative ranking.
- Thread the activation context through the existing runtime call sites in [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) rather than creating a second ranking entrypoint.
- Emit the new movement-ranking fields into runtime summary and synced metrics first, then let existing collection and cohort pipelines consume them additively.
- Keep selected-surface, operator packet, and explanation-pack consumers on their existing honesty contracts; they may read additive movement fields later, but should not change narrative behavior in Phase 64.

</code_context>

<deferred>
## Deferred Ideas

- Applying movement-focused ranking to limited-mode customers
- Threshold-policy redesign or broader recoverable-band changes
- New planner architecture or new chooser stages
- New action types or institution-heavy strategy expansion
- Customer-facing or operator-facing copy changes based on movement strength
- Any probabilistic model or learned ranker for path ordering

</deferred>

---

*Phase: 64-movement-focused-path-ranking*
*Context gathered: 2026-04-07*
