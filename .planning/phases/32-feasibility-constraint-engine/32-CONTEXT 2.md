# Phase 32: Feasibility & Constraint Engine - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Ensure customer-specific numeric targets are realistic, repairable when safe, and rejected when infeasible. This phase hardens:
- feasibility verdict contract
- canonical constraint families
- repair vs reject posture
- business vs technical visibility of feasibility truth

This phase does **not** reopen:
- action taxonomy
- action grouping
- business-vs-technical identity
- numeric target generation posture
- execution difficulty modeling
- offer-layer semantics
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
- Phase 31 remains authoritative for numeric target generation:
  - actions already carry one canonical `PrimaryNumericTarget`
  - numeric posture is minimum credible change
  - mixed-unit actions expose one primary target plus technical secondary effects
  - Phase 31 emitted feasibility-neutral handoff notes only
- Phase 32 is the first phase that may emit real feasibility truth:
  - clip
  - repair
  - reject
  - dependency-gated provisionality

### Feasibility Verdict Contract
- Canonical action-level verdict set:
  - `valid`
  - `clipped`
  - `repaired`
  - `provisional`
  - `invalid`
- Plan-level verdict should be derived by worst-dominant action/constraint truth.
- Locked plan-level priority order:
  - `invalid`
  - `provisional`
  - `repaired`
  - `valid`
- `clipped` remains an action-level truth.
- At plan level, clipped actions roll up into the broader `valid` or `repaired` family rather than creating a separate top-level plan verdict.
- `clipped` remains acceptable only when semantic meaning is preserved.
- If clipping causes:
  - direction inversion
  - semantic noop
  then the result must become `invalid`.
- `provisional` means:
  - feasibility may be numerically acceptable
  - but the action or plan is still gated by an external dependency
  - such as approval, acceptance, or mandatory external input
- `provisional` is **not** a feasibility failure; it is dependency-gated realism.

### Canonical Constraint Families
- Constraint truth should remain two-layered:
  - `constraint_family`
  - granular `reason_code`
- Locked canonical `constraint_family` set:
  - `capacity`
  - `policy`
  - `dependency`
  - `interaction`
  - `semantic`
  - `documentation`
- Family semantics:
  - `capacity`
    - real-world affordability, payment capacity, income-growth realism, utilization relief realism
  - `policy`
    - engine or policy-domain bounds such as legal ranges or normalized limits
  - `dependency`
    - external approvals, acceptances, or missing outside inputs
  - `interaction`
    - cross-action conflicts, prerequisite failures, incompatible action combinations
  - `semantic`
    - meaning-breaking outcomes such as direction inversion or semantic noop
  - `documentation`
    - missing verification or required supporting documentation
- Numeric clip sources should split cleanly:
  - real-world capacity ceiling -> `capacity`
  - abstract engine/domain bound -> `policy`
- Cross-action conflict and prerequisite failures belong to `interaction`.
- External approval or outside dependency gates belong to `dependency`.

### Repair vs Reject Posture
- Global posture:
  - `repair-if-safe`
  - `reject-if-semantic-break`
- Direct `invalid` cases:
  - direction inversion
  - semantic noop
  - missing mandatory dependency input
  - invalid combination that remains inconsistent after repair attempts
- `repaired` plans may still remain in ranking contention.
- But repaired plans must always sit behind otherwise comparable `valid` plans.
- A plan should die if the primary action meaning is lost.
- A plan may survive if only secondary or technical effects are dropped while the primary business action still holds.
- This means grouped actions should be judged by whether their canonical action meaning survives the repair.

### Business vs Technical Visibility
- Business-facing default feasibility output should show only outcome-level language.
- Business default should not expose:
  - raw `reason_code`
  - raw clip math
  - internal constraint trace details
- Business-facing wording should stay simple:
  - `valid` -> directly feasible / directly applicable
  - `repaired` -> `yumusatilarak uygulanabilir`
  - `provisional` -> `dis bagimlilik nedeniyle kosullu`
- `invalid` should not appear on default product surfaces.
- `invalid` remains visible only in:
  - technical review
  - batch outputs
  - validation artifacts
- Minimum technical reveal set:
  - `constraint_status`
  - `constraint_family`
  - `reason_code`
  - `was_clipped`
  - `repair_applied`
  - `dependency_gate`
  - `semantic_preserved`

### Claude's Discretion
- Exact internal field names for feasibility trace records as long as the locked meanings remain explicit and stable
- Exact shape of plan-level rollup metadata as long as worst-dominant verdict order is preserved
- Exact wording for business outcome labels as long as:
  - repaired means softened-but-usable
  - provisional means dependency-gated
  - invalid stays off default product surfaces
- Exact mapping of existing legacy reason codes into the new `constraint_family` layer as long as every emitted reason can be rolled up cleanly

</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants Phase 32 to start where Phase 31 stops:
  - not generating new targets
  - but deciding whether those numeric targets are realistically achievable
- The feasibility layer should remain product-safe:
  - rich technical trace for analyst/review
  - only outcome labels in default business view
- The most important posture is:
  - preserve meaning if possible
  - reject when the action no longer means what it claimed to mean
- `provisional` must stay separate from outright feasibility failure so approval-gated plans do not get mislabeled as numerically impossible.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [feasibility.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/feasibility.py)
  - already applies target-level feasibility and emits detailed reason codes such as clipping and semantic-loss cases
  - is the main seam for numeric target realism and clip semantics
- [action_constraints.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_constraints.py)
  - already handles prerequisite, conflict, repair-drop, and provisional logic
  - is the natural seam for canonical `interaction` and `dependency` families
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already carries `constraint_status`, `constraint_trace`, `action_status`, `technical_reveal`, and `PrimaryNumericTarget`
  - is the right place to lock a canonical feasibility contract and visibility split
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
  - already ranks `valid`, `repaired`, `provisional`, and `invalid` plans differently
  - is the downstream seam that should reflect the locked precedence without redefining feasibility
- [safety/validator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/safety/validator.py)
  - already converts constraint truth into status reasons and rejection text
  - will need to stay aligned with the new canonical verdict/visibility contract
- [portfolio_validation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/portfolio_validation.py)
  - already distinguishes `valid`, `repaired`, and `provisional` in coverage logic
  - will likely consume the locked feasibility truth without reinterpreting it

### Established Patterns
- Phase 18 already established engine-owned business vs technical visibility:
  - default view stays business-first
  - technical reveal carries internal detail
- Phase 30 already established semantic identity:
  - raw feature language should not leak into default product output
- Phase 31 already established the target-generation boundary:
  - `generation_notes` and `raw_generation_basis` are handoff inputs, not feasibility verdicts
- v1.2 / v1.3 feasibility history already showed the need for:
  - repaired contenders to remain traceable
  - provisional branches to stay distinct from invalid outputs

### Integration Points
- Primary engine seams for Phase 32:
  - `credit-coach/src/credit_coach/recourse/feasibility.py`
  - `credit-coach/src/credit_coach/recourse/action_constraints.py`
  - `credit-coach/src/credit_coach/data/schema.py`
- Important downstream consumers to keep aligned:
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/safety/validator.py`
  - `credit-coach/src/credit_coach/coaching/messaging.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`

</code_context>

<deferred>
## Deferred Ideas

- Difficulty and execution-likelihood scoring over feasible actions belongs to Phase 33
- Explicit institution offer restructuring belongs to Phase 34
- Narrative refresh for repaired/provisional numeric plans belongs to Phase 35
- Product-surface rollout for feasibility-aware numeric plans belongs to Phase 36
- Portfolio proof of feasible numeric-action impact belongs to Phase 37
- Calibration and false-optimism validation belongs to Phase 38
- Pilot integration belongs to Phase 39

</deferred>

---
*Phase: 32-feasibility-constraint-engine*
*Context gathered: 2026-03-21*
