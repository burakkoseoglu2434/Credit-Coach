# Phase 45: Winner Integrity Hard Stop - Research

**Researched:** 2026-03-26
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that guarantees invalid recommendations can never survive winner selection, while preserving existing decision ownership and ranking semantics?

## Planning Basis

Phase 45 decisions were discussed in-session and are now locked in [45-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/45-winner-integrity-hard-stop/45-CONTEXT.md). For this planning pass the authoritative inputs are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [45-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/45-winner-integrity-hard-stop/45-CONTEXT.md)
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
- [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py)

This is sufficient because the repo already has:

- deterministic decision ownership from Phase 40.5
- additive calibration and collection rollups from Phase 41
- source-mix and empty-contender semantics from Phase 42
- recommendation validity taxonomy from Phase 42.5
- operator packet semantics from Phase 43

The missing layer is no longer validity annotation. The missing layer is **hard-stop enforcement, no-valid-winner truth propagation, and selected-surface integrity**.

## Executive Summary

Phase 45 should be planned as a **winner-integrity enforcement phase**, not as a planner redesign phase.

The safest shape is:

`existing chooser semantics -> validity hard-stop -> explicit selection result -> raw/flat propagation -> collection integrity checks -> large-sample rerun proof`

The code scan shows five important truths:

1. [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py) already owns candidate preference, ranking, and tie-break behavior, so Phase 45 should fix fallback behavior there rather than inventing a second chooser
2. [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py) already correctly distinguishes `valid`, `warning`, and `invalid`, so Phase 45 should consume the existing taxonomy instead of reworking it
3. [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) and [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py) both consume `choose_best_plan(...)`, so the winner-integrity fix must be shared and explicit
4. [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already knows how to treat `best_plan_id` absence as no-viable-plan truth, so `no_valid_winner` can be introduced without reopening decision semantics
5. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) currently treats missing selected rows as parity corruption, so Phase 45 must explicitly add an expected-empty selected state

## Concrete Repo Findings

### 1. The dominant bug is a fail-open planner fallback

In [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py), invalid candidates are filtered from the preferred set, but the filtered set only replaces `candidates` when non-empty. That means an empty valid-filtered preferred pool silently revives the original invalid pool.

This is the core integrity bug. It is not a scoring bug, a validity-taxonomy bug, or a decision-policy bug.

### 2. The fix must preserve existing ranking semantics

The current chooser already encodes:

- constraint preference
- non-rejected preference
- denied-mode ranking
- planner-quality ordering
- warning penalty semantics
- source tie-break semantics

Phase 45 should keep all of that and only change the candidate set that survives to ranking.

### 3. `no_valid_winner` can reuse existing decision bridges

[ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already derives no-viable-plan behavior from:

- missing `best_plan_id`
- `best_action_count == 0`
- `plan_contract_pass == 0`

That means Phase 45 can introduce an explicit `selection_outcome = no_valid_winner` without adding a new decision state.

### 4. Collection integrity currently assumes a selected row always exists

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) currently treats an empty `selected_best_flag` set as a parity mismatch.

Phase 45 must split these cases:

- corruption:
  - `best_plan_id != null` and selected row missing
- expected empty:
  - `selection_outcome = no_valid_winner`
  - `best_plan_id = null`
  - `selected_best_flag.sum() == 0`

### 5. Large-sample reruns are now executable locally

The recent sample-CSV fallback means Phase 45 can rely on deterministic large-sample reruns for:

- `pilot_mixed`
- `risk_band_balanced`
- `offer_needed_balanced`

This is important because the phase exit criterion is not just unit correctness. It is also:

- `selected_invalid_winner_count = 0`
- `0` selected `dice` winners with `recommendation_validity_status = invalid`

## What Phase 45 Must Deliver

### 1. Hard-stop selection enforcement

The chooser must:

- reject invalid contenders absolutely
- widen only to valid pools in the locked order
- return an explicit `no_valid_winner` result instead of selecting an invalid plan

### 2. Explicit selection result contract

The planner should return:

- `best_plan`
- `selection_meta`

so downstream code can distinguish:

- selected valid winner
- widened valid selection
- no valid winner

without guesswork.

### 3. Raw / flat integrity propagation

Single-customer, batch, and collection paths must all propagate:

- `selection_outcome`
- `selection_stage`
- invalid-removal diagnostics
- no-valid-winner null semantics

while keeping `best_plan_id` and `selected_best_flag` strict and non-contradictory.

### 4. Collection-level integrity proof

Phase 45 must add enough aggregate collection metrics to prove the hard-stop works:

- invalid selected winner count/rate
- no-valid-winner count
- widened valid selection rate
- preferred-pool invalid exhaustion rate

### 5. Regression-protected rerun closure

The phase needs:

- unit tests for widened-valid and no-valid-winner paths
- integration tests for `best_plan_id` / `selected_best_flag` semantics
- large-sample rerun proof across all three active cohort policies

## Recommended Plan Shape

The cleanest plan split is:

1. `45-01` — hard-stop chooser contract and explicit selection result
2. `45-02` — downstream raw/flat/collection integrity propagation
3. `45-03` — regression closure and large-sample rerun proof
