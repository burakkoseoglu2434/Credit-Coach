# Phase 42: Planner Quality & Source Mix - Research

**Researched:** 2026-03-23
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that makes candidate selection more honest and competitive by removing empty winners, standardizing source provenance, and measuring internal-vs-`dice` planner quality without changing the shipped Phase 40.5 decision owner?

## Planning Basis

Phase 42 decisions were discussed in-session and locked into `42-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/42-planner-quality-source-mix/42-CONTEXT.md`
- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/evaluation/decision_calibration.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/tests/test_planner_denied_objective.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_customer_artifact_collection.py`

This is sufficient because the repo already has:

- null-free and parity-safe customer artifact truth from Phase 40
- one deterministic decision owner from Phase 40.5
- collection-root calibration artifacts from Phase 41
- operator-safe packaging from Phase 43
- existing source-entropy, best-source-rate, and candidate-pool diagnostics in the batch runner

The gap is no longer missing decision logic. The gap is missing **planner honesty, contender filtering, and source-mix provenance discipline**.

## Executive Summary

Phase 42 should be planned as a **planner-quality recovery and provenance-hardening phase**, not as a decision redesign.

The safest shape is:

`candidate generation -> contender diagnostics -> empty filter -> source-aware best-plan selection -> source/diversity/maturity reporting`

The code scan shows four important truths:

1. batch evaluation already knows more about source mix than single-customer recourse does
2. best-plan selection is not yet explicitly aware of empty semantic shells or source provenance as first-class truth
3. source-mix honesty is currently stronger in aggregate analytics than in the producer-side plan contract
4. action class/family and offer maturity ingredients already exist, so diversity and maturity hardening can be layered on without inventing a new contract family

The clean split for this phase is therefore:

`source truth + contender filtering -> lane competitiveness + reporting -> diversity and offer maturity hardening`

## Existing Assets We Can Reuse

### Batch runner already has source-mix metrics

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `_plan_source(...)`
  - `_candidate_source_entropy(...)`
  - `_candidate_pool_diversity_index(...)`
  - `best_source_*_rate`

This is the right seam for:

- source taxonomy standardization
- collection-level source metrics
- recovery-lane wording

### Planner already owns deterministic best-plan selection

- `credit-coach/src/credit_coach/coaching/planner.py`
  - `choose_best_plan(...)`
  - `_prefer_non_rejected(...)`
  - `_prefer_constraint_eligible(...)`

This is the right seam for:

- contender bucket filtering
- near-tie source preference
- action diversity and maturity penalties

### Single-customer runner already serializes candidate pools

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - writes `candidate_pool.csv/json`
  - emits `best_plan_source`
  - serializes plan rows and roadmap summary

This is the right seam for:

- explicit `plan_source` propagation
- customer-level source counts and presence flags
- parity between single-customer and batch outputs

### Calibration and operator layers already consume additive metrics

- `credit-coach/src/credit_coach/evaluation/decision_calibration.py`
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
- `credit-coach/src/credit_coach/ops/operator_review.py`

These are the right seams for:

- source-mix rollups under the existing collection root
- diversity and offer-maturity supporting metrics
- honest downstream reporting without becoming a second decision system

## Concrete Repo Findings

### 1. Source taxonomy is richer in batch than in single-customer flow

Batch already distinguishes:

- `internal`
- `dice`
- `rule`
- `fallback`

Single-customer recourse still mostly infers `internal` vs `dice` from `plan_id`. Phase 42 should promote source provenance into an explicit producer-owned field instead of relying on string heuristics.

### 2. Empty-winner protection is stronger at decision time than at contender time

Phase 40.5 guarantees `step_count == 0 -> REJECTED`, but contender pools can still carry semantically empty or approval-shell-heavy plans deep enough to distort best-plan selection. Phase 42 should push honesty earlier:

`generate -> diagnose -> filter -> select`

### 3. Main planner competitiveness is not yet isolated from recovery lanes

Current batch outputs already compute best-source rates, but they can still be read too optimistically because `rule` and `fallback` live in the same headline space. Phase 42 should formalize:

- main quality axis = `internal vs dice`
- recovery lanes = `rule`, `fallback`

### 4. Diversity and offer maturity data already exist but are not yet planner-quality guardrails

The repo already carries:

- `action_class`
- `action_family`
- `approval_pending_action_count`
- `offer_family`
- `offer_maturity`

That means Phase 42 can add anti-collapse warnings and maturity-aware contender penalties without changing the customer-facing decision contract.

## What Phase 42 Must Deliver

### 1. Explicit source provenance

All candidate and best-plan outputs should converge on one canonical source contract:

- explicit `plan_source`
- customer-level source counts and presence flags
- collection-level source rates and supporting source-lens breakdowns

### 2. Empty contender removal before best-plan selection

Planner quality will remain untrustworthy until:

- zero-action contenders
- semantically empty contenders
- pure shell paths

are removed from the winner path before best-plan selection.

### 3. Honest lane competitiveness

Phase 42 should answer:

- can `internal` beat `dice` on real contenders?
- how often do recovery lanes rescue the system?
- are best wins driven by meaningful actionable candidates or by brittle fallback paths?

### 4. Anti-collapse diversity and maturity guardrails

The system should surface when winners collapse to one action type or when contender quality is inflated by immature institution-side offers.

## Recommended Plan Split

### Plan 42-01 — Source truth and empty contender filtering

Focus on:

- explicit `plan_source`
- backward-compatible source normalization
- contender bucket classification
- empty contender removal before selection

### Plan 42-02 — Lane competitiveness and source-mix reporting

Focus on:

- internal-vs-`dice` competitiveness metrics
- near-tie source preference
- recovery-lane wording
- customer and collection source-mix outputs

### Plan 42-03 — Diversity, offer maturity, and regression closure

Focus on:

- action diversity metrics
- anti-collapse warnings
- offer maturity penalties and lane metrics
- additive packaging and regression closure
