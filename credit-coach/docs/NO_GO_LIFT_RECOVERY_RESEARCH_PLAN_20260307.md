# NO_GO Lift Recovery - Research and Implementation Plan (2026-03-07)

## 1) Current decision and bottleneck

Current release decision is `NO_GO` because `G0_BATCH_RECOURSE_KPI` fails on lift, while latency/fairness/error are within gate limits.

Latest failing smoke snapshot:
- Run: `artifacts/runs/20260307_141427_61bbd0_c280d7/tables/production_smoke_report.csv`
- `denied_to_approved_lift = 0.004219` (target: `>= 0.05`)
- `approval_gap_delta = +0.002049` (PASS)
- `equalized_odds_gap_delta = 0.0` (PASS)
- `latency_p95_ms = 19.32` (PASS)
- `latency_p99_ms = 206.26` (PASS)
- `error_rate = 0.0` (PASS)

Root-cause concentration from batch run `20260307_141346_b7e022_2a7cb1`:
- `denied_count = 237`
- `denied_with_gate_pass_plan = 1`
- `denied_not_approved_root_cause = reliability_gate` share `99.58%`

Additional segmentation of denied set (same run):
- By risk band (`base_pd`):
  - near (`tau..tau+0.10`): `43`, gate-pass `1` (2.33%)
  - mid (`tau+0.10..tau+0.25`): `16`, gate-pass `0`
  - high (`> tau+0.25`): `178`, gate-pass `0`
- By income quartile:
  - q1: `79`, gate-pass `0`
  - q2: `57`, gate-pass `0`
  - q3: `55`, gate-pass `0`
  - q4: `46`, gate-pass `1`

Interpretation:
- Problem is not latency or fairness regression.
- Problem is denied conversion under reliability gate, especially high-risk denied segment.
- Current one-shot plan generation is not producing enough robust margin in hard denied cohorts.

## 2) Research synthesis for requested changes

### 2.1 Segment-based recourse feasibility and fairness

Findings:
- Actionability and feasibility should be explicit, constrained, and cost-aware rather than unconstrained counterfactual moves.
- Group-level recourse parity matters: if recourse burden differs by segment, aggregate lift may look acceptable but product is not robust or fair.

Design implication:
- Do not relax global safety gates.
- Relax only action caps in a controlled, segment-aware way (income/risk bands), with hard global bounds and fairness guardrails.

### 2.2 Multi-step (time-aware) recourse

Findings:
- Recent time-aware recourse work shows one-shot recommendations can become invalid over time; temporal/adaptive planning is required.
- Sequential setting with re-planning improves realism under drift, shocks, and execution uncertainty.

Design implication:
- Add weekly staged optimizer and gate-aware re-planning objective.
- Keep final decision with existing validator; optimize path to pass validator, not only nominal PD.

### 2.3 Denied-focused robust objective

Findings:
- Robust recourse literature shows minimum-cost solutions are often not robust to uncertainty.
- In our data, dominant failure cause is reliability gate, so objective must directly optimize CI/reliability/worst-margin constraints.

Design implication:
- Add denied-specific objective that penalizes gate violations directly.
- Rank candidates by gate-pass likelihood first, then cost/sparsity.

## 3) Target architecture changes (no code yet)

### 3.1 Segment-based cap relaxation (requested item 1)

Goal:
- Recover lift by expanding feasible action space only for segments where current caps are too tight.

Proposed segmentation:
- `income_band`: quartiles over `annual_inc` on current batch sample (`q1..q4`)
- `risk_band` based on `base_pd`:
  - `near`: `tau < base_pd <= tau + 0.10`
  - `mid`: `tau + 0.10 < base_pd <= tau + 0.25`
  - `high`: `base_pd > tau + 0.25`

Cap multiplier formula:
- For each actionable feature `f`:
  - `cap_eff(f, i) = cap_base(f) * m_income(income_band_i) * m_risk(risk_band_i)`
- Constraints:
  - `cap_eff` clamped to global hard limits
  - only in denied-target mode
  - never relax immutable/direction rules

Initial multiplier policy (starting point):
- `near`: mild expansion (1.0 to 1.2)
- `mid`: medium expansion (1.1 to 1.4)
- `high`: stronger expansion (1.2 to 1.8)
- income-aware damping:
  - lower income bands: prioritize debt-reduction and utilization features over pure income jumps

Files to change later:
- `configs/recourse.yaml`
- `configs/recourse_feasibility.yaml`
- `src/credit_coach/recourse/feasibility.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/cli/run_recourse.py`

Telemetry to add:
- `segment_caps_applied` (0/1)
- `income_band`, `risk_band`
- `cap_multiplier_income`, `cap_multiplier_risk`

### 3.2 Internal planner weekly staged optimization (requested item 2)

Goal:
- Replace single jump with stepwise, week-by-week trajectory that is more likely to satisfy robust gates.

Planner concept:
- State `x_t` = feature vector at week `t`
- Action `a_t` = small feasible action bundle
- Transition `x_{t+1} = T(x_t, a_t)`
- Weekly horizon `H` (e.g., 6 or 12 weeks)

Denied objective per trajectory (minimize):
- `J = sum_{t=1..H} [w_ci * v_ci(t)^2 + w_rel * v_rel(t)^2 + w_worst * v_worst(t)^2]`
- `+ w_cost * total_cost + w_sparse * total_actions`

Where:
- `v_ci(t) = max(0, ci_high_t - tau)`
- `v_rel(t) = max(0, min_reliability - reliability_t)`
- `v_worst(t) = max(0, min_worst_margin - worst_margin_t)`

Search strategy:
- Beam search over weekly action bundles (small beam width, strict budget)
- Keep top-K trajectories by `J`
- Emit best final plan as `PlanRecord`
- Save trajectory diagnostics as separate table (`weekly_trajectory_debug.csv`)

Leverage existing modules:
- `src/credit_coach/coaching/loop.py` (weekly dynamics and replan logic)
- `src/credit_coach/coaching/reviewer.py` (replan triggers)

Files to change later:
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/coaching/planner.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/cli/run_recourse.py`
- optional config: `configs/recourse.yaml`

### 3.3 Denied-specific reliability objective (requested item 3)

Goal:
- Directly optimize what fails today: reliability gate components.

Current gap:
- Generator has robust score and gate penalty, but denied cohorts still collapse at reliability gate.
- Candidate ranking/selection must become gate-pass-first for denied segment.

Proposed denied objective config block:
- `robust.denied_objective.enabled: true`
- `weights: {ci, reliability, worst_margin, cost, sparsity}`
- `squared_violation: true`
- `segment_adaptive_weights` optional by risk band

Selection policy change:
- For denied customers:
  - primary sort: total denied objective
  - secondary sort: fewer actions, lower cost
- For non-denied customers:
  - keep current policy

Files to change later:
- `configs/recourse.yaml`
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/coaching/planner.py`
- `src/credit_coach/safety/validator.py` (only if extra diagnostics needed)

## 4) Experiment and rollout plan (implementation phase sequence)

Execution order (mandatory):
1. Phase A: Segment caps only
2. Phase B: Segment caps + weekly staged optimizer
3. Phase C: Segment caps + weekly optimizer + denied objective
4. Phase D: Tune weights/caps with fairness and latency guardrails

For each phase:
- Run `pytest -q`
- Run batch dry-run on `n=200`
- Run full batch on `n=1000` (`sample_seed=42`)
- Run `run_production_smoke`

Primary acceptance for GO:
- `denied_to_approved_lift >= 0.05`
- `approval_gap_delta <= +0.01`
- `equalized_odds_gap_delta <= +0.01`
- `latency_p95_ms <= 500`
- `latency_p99_ms <= 2000`
- `error_rate <= 0.005`

Additional safety checks to prevent hidden regressions:
- `denied_not_approved_top_root_cause_share(reliability_gate)` should decrease materially from current `~0.996`
- `recourse_success_gap <= 0.10`
- `recourse_cost_gap <= 500`
- no segment should carry near-zero lift while others improve sharply (segment-lift skew monitor)

## 5) Test plan (to implement with code)

Unit tests:
- Segment multiplier application and hard clamping logic
- Denied objective monotonicity:
  - higher `ci_high` violation => worse score
  - lower reliability => worse score
  - worse worst-margin => worse score
- Weekly staged optimizer deterministic path under fixed random seed

Integration tests:
- Batch recourse run includes new segment and trajectory diagnostics columns
- `choose_best_plan` denied mode respects new objective
- No regression in existing recourse redesign tests

Performance tests:
- n=1000 with `n_workers=1` and `n_workers=5`
- verify no p95/p99 gate breach after staged optimizer

## 6) Risk controls

Risks:
- Over-relaxing caps can improve lift but hurt fairness or produce unrealistic plans.
- Weekly optimizer can increase compute cost and tail latency.
- Denied objective overfit can reduce diversity and increase repeated plan templates.

Mitigations:
- Keep hard global feasibility limits.
- Add per-customer search time budget and candidate pool pruning.
- Keep phase-wise ablations and rollback to previous config profile.

Rollback rule:
- If any G0 sub-gate (except lift during tuning) regresses beyond threshold, revert to previous stable profile immediately.

## 7) Concrete coding backlog for next step

Ticket P0-1:
- Add `segment_caps` config and segment context plumbing in batch and single-customer recourse flows.

Ticket P0-2:
- Extend feasibility application with segment multipliers and hard clamp safeguards.

Ticket P0-3:
- Add denied objective scoring path in generator and denied-first ranking in planner.

Ticket P1-1:
- Add weekly staged optimizer in generator using small beam search and trajectory diagnostics.

Ticket P1-2:
- Add tests for segment caps, denied objective monotonicity, staged optimizer regression.

Ticket P1-3:
- Add segment-level funnel report table (`denied_lift_by_income_risk.csv`).

## 8) Reference links used in this research

Academic/technical recourse:
- https://arxiv.org/abs/1809.06514
- https://arxiv.org/abs/1905.07697
- https://arxiv.org/abs/1909.09369
- https://arxiv.org/abs/1909.03166
- https://proceedings.mlr.press/v162/dominguez-olmedo22a.html
- https://arxiv.org/abs/2309.06969
- https://arxiv.org/abs/2410.08007

Libraries/docs:
- https://interpret.ml/DiCE/notebooks/DiCE_model_agnostic_CFs.html
- https://github.com/carla-recourse/CARLA
- https://mapie.readthedocs.io/en/stable/
- https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html

Governance/regulatory:
- https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
- https://www.bis.org/publ/bcbs239.htm
- https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/
- https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX%3A32024R1689
