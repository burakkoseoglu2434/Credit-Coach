# Phase 54: Action Semantics Taxonomy - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Define a canonical, feature-agnostic, typed action taxonomy that expands the solution space and enables multi-path recourse generation without breaking trust contracts. The taxonomy must be typed, atomic, owner-aware, and feature-agnostic, with a fixed category set and clear canonical action schema definition.

</domain>

<decisions>
## Implementation Decisions

### Action Abstraction Model
- **D-01:** Actions are NOT feature-based. They are canonical abstractions (e.g. `reduce_balance`, `increase_limit`, `consolidate_debt`). Multiple features can map to the same action.

### Action Structure
- **D-02:** Actions are atomic (no composite actions at the taxonomy level). Composite strategies will be formed at the plan-generation stage in later phases.

### Action Schema (Canonical Contract)
- **D-03:** Each action MUST include the following fields: `action_key`, `action_type`, `action_category`, `action_owner` (customer | institution | hybrid), `primary_features_impacted`, `dice_eligible` (boolean), `heuristic_only` (boolean), `requires_numeric_target` (boolean).

### Taxonomy Categories & Semantics
- **D-04:** Fixed category set: `utilization_capacity`, `burden_reduction`, `delinquency_cleanup`, `credit_structure`, `income_trust`, `application_parameters`, `institution_relief`.
- **D-05:** Ownership semantics must dictate movement unlock: `customer` (executable directly by user), `institution` (requires bank/system action), `hybrid` (requires both).

### Execution Lane Boundary
- **D-06:** DICE only operates on numeric/controllable features. The heuristic lane handles real-world institutional or structural actions. Both MUST share the same action taxonomy.

### No Regression Rule
- **D-07:** The taxonomy must be additive only. Strictly NO changes to planner selection semantics, validity taxonomy, decision ownership, or operator packet logic.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Action Taxonomy Constraints
- `.planning/PROJECT.md` — Adhere to trust baselines (winner integrity, DICE validity, selected-surface consistency, operator coherence).

No other external specs provided for this phase. Requirements fully captured in decisions above.
</canonical_refs>

<deferred>
## Deferred Ideas

- Feature → action mapping — deferred to Phase 55
- DICE expansion — deferred to Phase 56
- Heuristic lane expansion — deferred to Phase 57
- Multi-path generation — deferred to Phase 58
- Rendering / Frontend implementation — deferred to Phase 59

</deferred>
