---
phase: 32-feasibility-constraint-engine
verified: 2026-03-21T20:45:00+03:00
status: passed
score: 8/8 must-haves verified
---

# Phase 32: Feasibility & Constraint Engine Verification Report

**Phase Goal:** Decide whether customer-specific numeric targets are realistically achievable, whether they should be clipped or repaired, and when they must be treated as invalid, then expose that truth safely to ranking, product, and proof consumers.  
**Verified:** 2026-03-21T20:45:00+03:00  
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Action-level feasibility now resolves to canonical verdicts `valid | clipped | repaired | provisional | invalid` | ✓ VERIFIED | `feasibility.py`, `schema.py`, and `test_recourse_feasibility.py` |
| 2 | Every feasibility or constraint event can roll up into one canonical `constraint_family` plus granular `reason_code` truth | ✓ VERIFIED | `feasibility.py`, `action_constraints.py`, `test_action_space.py`, and `test_recourse_redesign.py` |
| 3 | Missing mandatory dependency input and semantic-break cases now fail closed as `invalid` | ✓ VERIFIED | `test_recourse_feasibility.py` and runtime invalid-event propagation |
| 4 | Repair is only allowed when semantic meaning survives; composite actions die when the primary anchor disappears | ✓ VERIFIED | `action_constraints.py` and `test_action_space.py` |
| 5 | Repaired plans remain contenders, but valid plans still outrank equivalent repaired plans | ✓ VERIFIED | `planner.py` and `test_planner_denied_objective.py` |
| 6 | Business-facing narrative output shows feasibility outcome labels without exposing raw reason codes | ✓ VERIFIED | `messaging.py` and `test_messaging.py` |
| 7 | Technical reveal retains the minimum feasibility trace set across action-level and plan-level truth | ✓ VERIFIED | `messaging.py`, `run_recourse.py`, and `test_messaging.py` |
| 8 | Portfolio validation now measures canonical feasibility drop reasons instead of relying on legacy ad hoc interpretation | ✓ VERIFIED | `portfolio_validation.py` and `test_portfolio_validation.py` |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `credit-coach/src/credit_coach/recourse/feasibility.py` | target-level verdict normalization and family classification | ✓ EXISTS + SUBSTANTIVE | canonical invalidation, family classification, and missing-input handling |
| `credit-coach/src/credit_coach/recourse/action_constraints.py` | repair-vs-reject posture plus dependency/interactions traces | ✓ EXISTS + SUBSTANTIVE | semantic-anchor protection, provisional dependency gates, and enriched traces |
| `credit-coach/src/credit_coach/data/schema.py` | canonical feasibility contract | ✓ EXISTS + SUBSTANTIVE | feasibility fields added to `PlanAction`; plan-level contract unchanged and explicit |
| `credit-coach/src/credit_coach/coaching/messaging.py` | business-safe feasibility visibility | ✓ EXISTS + SUBSTANTIVE | step-level feasibility labels plus normalized technical reveal |
| `credit-coach/src/credit_coach/evaluation/portfolio_validation.py` | downstream portfolio consumer alignment | ✓ EXISTS + SUBSTANTIVE | canonical raw-to-valid drop reasons and proof-safe feasibility truth |

**Artifacts:** 5/5 verified

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| FEAS-01 | ✓ SATISFIED | - |

**Coverage:** 1/1 verified for Phase 32 scope

## Verification Commands

- `python -m pytest credit-coach/tests/test_recourse_feasibility.py credit-coach/tests/test_action_space.py credit-coach/tests/test_recourse_redesign.py -q`
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_messaging.py credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_recourse_generator_action_budget.py -q`
- `python -m pytest credit-coach/tests/test_recourse_feasibility.py credit-coach/tests/test_action_space.py credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_messaging.py credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_recourse_generator_action_budget.py -q`
- `git diff --check`

## Gaps Summary

**No gaps remain inside the agreed Phase 32 scope.**

Carry-forward note:
- Phase 33 still owns action difficulty and execution modeling beyond feasibility truth.

## Verification Metadata

**Verification approach:** Goal-backward from plans `32-01`, `32-02`, and `32-03`  
**Automated checks:** Python regression suite and diff hygiene checks passed  
**Human checks required:** 0  
**Total verification time:** manual execution session

---
*Verified: 2026-03-21T20:45:00+03:00*
*Verifier: Codex*
