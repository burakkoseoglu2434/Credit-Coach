# Phase 31: Numeric Target Engine - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert canonical action units into customer-specific numeric targets that are precise, readable, and ready for feasibility checking. This phase hardens:
- numeric target posture
- unit families by `action_family`
- canonical `current / target / delta` contract
- the boundary between target generation and later feasibility enforcement

This phase does **not** reopen:
- action taxonomy
- action grouping
- business-vs-technical identity
- full feasibility clip/repair/reject logic
- execution difficulty modeling
- richer offer integration
- expanded product narratives

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Prior Phases
- Phase 30 remains authoritative for semantic identity:
  - top-level taxonomy stays `behavioral | structural | institutional`
  - `action_family` is already canonical
  - grouped action identity is already deterministic
  - `business_view` vs `technical_view` is already engine-owned
- Phase 31 must build numeric targets on top of those locked semantic units instead of reopening taxonomy or serialization identity.
- Phase 32 remains the feasibility phase:
  - clip / repair / reject verdicts do not belong in Phase 31
  - Phase 31 should hand off targets cleanly to feasibility rather than absorb that logic

### Numeric Target Posture
- The target engine should produce the **minimum credible change** rather than an idealized maximum improvement target.
- Phase 31 should emit **one canonical point target** per primary numeric recommendation.
- The default numeric expression should include:
  - absolute target
  - signed delta
- Numeric posture should be:
  - conservative but meaningful
- Targets must not become trivial or no-op recommendations, but they also must not become so aggressive that the engine starts doing feasibility's job early.

### Unit Families
- Unit resolution should be:
  - `action_family` primary
  - feature-specific override allowed when needed
- Canonical unit set stays deliberately small:
  - `currency`
  - `percentage_points`
  - `ratio`
  - `score_points`
  - `months`
  - `boolean_state`
  - `count`
- Locked family-to-unit defaults:
  - `loan_sizing` -> `currency`
  - `debt_restructuring` -> usually `currency`, with feature-specific override to `percentage_points` where needed
  - `income_strength` -> `currency`
  - `documentation` -> `boolean_state`
  - `cashflow_management` -> `percentage_points`
  - `utilization` -> `percentage_points`
  - `payment_discipline` -> `score_points`
  - `limit_management` -> `currency`
  - `hardship_relief` -> `currency`
- Mixed-unit actions must still expose only **one canonical primary numeric target** in Phase 31.
- Secondary numeric effects may remain available only in the technical layer.

### Numeric Target Contract
- Minimum canonical numeric target fields:
  - `metric_key`
  - `unit`
  - `current_value`
  - `target_value`
  - `delta_value`
  - `due_month`
  - `direction`
- `delta_value` must remain signed.
- `direction` must remain explicit even when delta sign already implies it.
- `due_month` should be one canonical month value rather than a range.
- `metric_key` should be:
  - business-friendly
  - deterministic
  - not a raw feature name
- Example posture:
  - semantic action identity remains in `business_view`
  - numeric target contract adds a business-readable metric identity such as `credit_utilization_pct` rather than `revol_util`

### Generation-vs-Feasibility Boundary
- Phase 31 may apply only **semantic sanity** checks during target generation:
  - obvious domain bounds
  - action direction consistency
  - unit conversion correctness
- Phase 31 may still generate a target that is hard but meaningful.
- Phase 31 must **not**:
  - clip
  - repair
  - reject
  - emit final validity verdicts
- Phase 31 should emit a light handoff seam for Phase 32, such as:
  - `generation_notes`
  - `raw_generation_basis`
- That handoff is explanatory only, not a feasibility status.

### Claude's Discretion
- Exact field names for the numeric-target subobject as long as the locked meanings remain explicit and stable
- Exact `metric_key` vocabulary as long as it stays business-friendly, deterministic, and non-raw-feature
- Exact representation of secondary numeric effects as long as:
  - one primary target remains canonical
  - secondary effects stay technical
- Exact representation of generation handoff notes as long as they are non-verdict and Phase 32-friendly

</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants Phase 31 to turn semantic actions into numeric targets without revisiting Phase 30 identity work.
- The canonical posture is:
  - one point target
  - absolute target plus signed delta
  - conservative but meaningful
- Unit families should be controlled and mostly derive from `action_family`.
- Mixed-unit actions such as refinancing should still present one primary numeric target and keep secondary numeric consequences in the technical layer.
- The user explicitly wants Phase 31 to stop short of feasibility verdicts:
  - hard targets are allowed
  - clip / repair / reject belongs to Phase 32

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already carries `current_value`, `target_value`, `delta`, and `time_months` on `PlanAction`
  - now also carries Phase 30 `business_view` and `technical_view`
  - is the natural seam to introduce a typed numeric-target contract without reopening semantic identity
- [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py)
  - now provides canonical `action_family`
  - already stores time horizon hints through `time_months`
  - is the right upstream seam for family-to-unit defaults and feature-level overrides
- [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py)
  - already computes raw `current_value -> target_value` transitions
  - is the main engine seam that currently turns search moves into low-level numeric deltas
  - is the likely place to produce one canonical primary numeric target per action
- [feasibility.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/feasibility.py)
  - already owns clip/repair/reject logic and semantic-loss diagnostics
  - is the explicit downstream boundary Phase 31 must not absorb
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
  - already uses technical-layer values such as `current_value`, `target_value`, and `delta`
  - will become a downstream consumer once numeric targets move from raw effect fields into a more business-readable target contract

### Established Patterns
- Phase 30 already established that:
  - semantic action identity belongs in `business_view`
  - raw effect anchors belong in `technical_view`
- Phase 18 already established:
  - engine-owned product contracts
  - deterministic business-first output plus technical detail on demand
- Phase 20 already established:
  - deterministic phase/checkpoint contract
  - due timing can safely attach to one canonical month without inventing new trajectory semantics

### Integration Points
- Primary engine seams for Phase 31:
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/recourse/action_space.py`
  - `credit-coach/src/credit_coach/recourse/generator.py`
- Important downstream consumers to keep aligned:
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - feasibility seams in `credit-coach/src/credit_coach/recourse/feasibility.py`

</code_context>

<deferred>
## Deferred Ideas

- Feasibility clip / repair / reject logic belongs to Phase 32
- Difficulty and execution realism over numeric targets belongs to Phase 33
- Explicit institution offer restructuring belongs to Phase 34
- Narrative refresh for numeric plans belongs to Phase 35
- Website and product-surface rollout for numeric targets belongs to Phase 36
- Portfolio proof of personalized numeric impact belongs to Phase 37
- Calibration and false-optimism validation belongs to Phase 38
- Pilot integration belongs to Phase 39

</deferred>

---
*Phase: 31-numeric-target-engine*
*Context gathered: 2026-03-21*
