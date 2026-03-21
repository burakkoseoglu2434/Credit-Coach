# Phase 31: Numeric Target Engine - Research

**Researched:** 2026-03-21
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so canonical semantic actions become customer-specific numeric targets that are readable, deterministic, and cleanly handed off to feasibility without reopening Phase 30 semantics?

## Planning Basis

Phase 31 now has a locked `31-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/30-action-semantics-hardening/30-CONTEXT.md`
- `.planning/phases/31-numeric-target-engine/31-CONTEXT.md`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/recourse/action_space.py`
- `credit-coach/src/credit_coach/recourse/generator.py`
- `credit-coach/src/credit_coach/recourse/feasibility.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/tests/test_action_space.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_recourse_feasibility.py`

This is sufficient because Phase 31 is not inventing a new planning stack. The repo already has:

- canonical semantic action identity from Phase 30
- raw numeric effect fields on `PlanAction`
- generator seams that already compute customer-specific `current_value -> target_value` transitions
- a downstream feasibility seam that already owns clipping, repair, rejection, and semantic-loss checks

The missing piece is not whether numbers exist at all, but whether those numbers are promoted into a first-class, business-readable target contract.

## Executive Summary

The codebase already has the low-level ingredients for numeric targets:

- `PlanAction` already carries `current_value`, `target_value`, `delta`, and `time_months`
- `generator.py` already creates customer-specific numeric deltas
- `action_space.py` already carries `action_family`, `direction`, and baseline time hints
- `feasibility.py` already owns the later clip/repair/reject boundary

What is still missing is the Phase 31 contract:

1. there is no explicit numeric-target object that separates business-readable target meaning from raw feature deltas
2. units are implicit rather than canonical and `action_family`-driven
3. mixed-unit actions still look like many feature effects instead of one primary numeric target plus secondary technical effects
4. the handoff between target generation and feasibility is not explicit enough; Phase 31 could easily start stealing Phase 32 scope if left loose

Phase 31 should therefore be planned as:

`numeric target contract -> engine generation integration -> downstream handoff and regression closure`

## Existing Assets We Can Reuse

### Semantic foundation is already locked

- `credit-coach/src/credit_coach/recourse/action_space.py`
  - now provides stable:
    - `action_key`
    - `action_class`
    - `action_family`
    - deterministic grouped semantics
  - is the right seam for:
    - family-to-unit defaults
    - metric-key defaults or overrides
    - due-month hints carried forward from action timing

### Raw numeric effect fields already exist

- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` already carries:
    - `current_value`
    - `target_value`
    - `delta`
    - `time_months`
  - now also carries Phase 30:
    - `business_view`
    - `technical_view`
  - is the right seam for:
    - introducing a typed primary numeric-target subobject
    - introducing secondary numeric effects in the technical branch
    - keeping semantic identity and numeric target meaning adjacent but distinct

### Generator already computes customer-specific targets

- `credit-coach/src/credit_coach/recourse/generator.py`
  - already turns candidate search moves into per-customer target values
  - already knows:
    - feature direction
    - current value
    - raw target value
    - action month / phase timing
  - is the correct seam for:
    - selecting one canonical primary numeric target per action
    - assigning `metric_key`, `unit`, `due_month`, `direction`
    - emitting generation notes without feasibility verdicts

### Feasibility seam already exists and must remain downstream

- `credit-coach/src/credit_coach/recourse/feasibility.py`
  - already owns:
    - target clipping
    - semantic-loss detection
    - repaired / clipped / invalid logic
  - is the main scope guard for Phase 31:
    - target engine may apply semantic sanity
    - target engine must not emit feasibility verdicts

### Messaging and roadmap already consume structured engine truth

- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`

These consumers already handle business vs technical layers. That means Phase 31 can safely add a numeric-target contract engine-side and let later phases render richer product language on top of it.

## What Phase 31 Must Deliver

### 1. Canonical numeric-target contract

Phase 31 must add one explicit numeric-target object carrying:

- `metric_key`
- `unit`
- `current_value`
- `target_value`
- `delta_value`
- `due_month`
- `direction`

This object should be business-readable and deterministic, not just another raw feature delta blob.

### 2. Family-driven unit resolution

Phase 31 must make unit selection controlled:

- `action_family` is the default driver
- feature-specific overrides are allowed
- the unit enum remains small and closed

This is the bridge between semantic action identity and later feasibility or UI behavior.

### 3. One primary numeric target per action

Mixed-unit actions such as refinancing or restructuring must not force the default contract to carry several equally primary targets.

Phase 31 should instead lock:

- one canonical primary numeric target
- optional secondary numeric effects in the technical layer

This preserves readability and keeps Phase 32 feasibility focused.

### 4. Clean generation-to-feasibility boundary

Phase 31 must apply only:

- direction sanity
- domain sanity
- unit sanity

It must not decide:

- clipped vs valid
- repaired vs invalid
- infeasible vs acceptable

Instead it should add a small handoff seam such as:

- `generation_notes`
- `raw_generation_basis`

## Recommended Plan Split

### Plan 31-01 — Numeric target contract and unit catalog

Focus on:

- adding a typed numeric-target object to the engine schema
- defining deterministic `metric_key` and unit semantics
- attaching family-driven defaults and feature overrides to the action catalog layer

### Plan 31-02 — Generator integration and feasibility handoff

Focus on:

- emitting one primary numeric target per action from the generator
- preserving signed deltas and canonical due month
- emitting non-verdict generation notes for Phase 32
- keeping mixed-unit secondary effects technical-only

### Plan 31-03 — Runtime consumer alignment and regression closure

Focus on:

- serializing numeric targets through roadmap and runtime artifacts
- aligning messaging and downstream consumers to the new target contract
- protecting the boundary so Phase 31 adds numeric meaning without feasibility verdicts

## Main Risks

### Risk 1: Numeric targets stay raw-feature-shaped

If Phase 31 only renames existing fields and never creates a true target contract, later phases still inherit model-native rather than product-safe numeric meaning.

Mitigation:

- introduce a typed numeric-target object rather than overloading raw technical fields

### Risk 2: Units drift across action families

If unit choice is inferred ad hoc inside generator logic, the same action family may serialize inconsistently across customers and later UI paths.

Mitigation:

- resolve units from the catalog seam first, with explicit feature overrides

### Risk 3: Mixed-unit actions become unreadable

If one action exposes multiple co-equal primary targets, product and feasibility layers lose clarity.

Mitigation:

- one primary numeric target per action
- secondary numeric effects technical-only

### Risk 4: Phase 31 absorbs feasibility logic

If target generation starts clipping, repairing, or rejecting, the milestone sequence collapses and Phase 32 loses purpose.

Mitigation:

- keep Phase 31 to semantic sanity only
- emit generation notes, not validity verdicts

## Recommended Validation Shape

Existing regression seams are sufficient for Nyquist-compliant planning:

- `credit-coach/tests/test_action_space.py`
  - protect family-driven unit and metric metadata defaults
- `credit-coach/tests/test_recourse_redesign.py`
  - protect generator and runtime action-to-target contract serialization
- `credit-coach/tests/test_messaging.py`
  - protect downstream narrative consumption of primary numeric targets
- `credit-coach/tests/test_recourse_feasibility.py`
  - protect the boundary that feasibility still owns clipping and rejection semantics

## Planning Recommendation

Proceed with Phase 31 now. Phase 30 already stabilized semantic identity; the correct next move is to turn those semantic actions into one numeric target contract per action before touching feasibility, execution difficulty, or offer structure.

---
*Phase: 31-numeric-target-engine*
*Researched: 2026-03-21*
