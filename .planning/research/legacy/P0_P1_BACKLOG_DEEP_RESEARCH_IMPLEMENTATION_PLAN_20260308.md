# CREDIT COACH - Deep Research Backlog and Execution Plan (P0/P1)
Date: 2026-03-08
Owner: Credit Coach product + ML platform
Scope: Convert 10 known product gaps into implementable backlog with evidence, technology choices, code touchpoints, KPI gates, and test plans.

## 1) Current Baseline and Why This Plan Exists
Reference metrics from latest production-like runs:
- denied_to_approved_lift: 0.0928
- denied_high_risk_lift: 0.0000
- denied_reliability_violation_rate: 1.0000
- denied_ci_violation_rate: 1.0000
- denied_worst_margin_violation_rate: 1.0000
- dice_success_rate: 0.0000
- latency_p95_ms: 286.88
- latency_p99_ms: 1573.52
- fairness_approval_gap_after: 0.0843
- fairness_equalized_odds_gap_after: 0.1163
- error_rate: 0.0000

Interpretation:
- System is operational and can pass release smoke, but core business KPI for hardest segment is failing.
- The primary bottleneck is not only model quality, but objective-design mismatch and candidate-search quality under uncertainty constraints.

## 2) Research Method and Selection Rules
Method used for this backlog:
1. Prioritize primary sources for algorithms (paper, official docs, official repos).
2. Prioritize regulator primary sources for legal/compliance requirements.
3. Map each source to a concrete code-level change in this repository.
4. Define acceptance using measurable KPI gates, not subjective quality claims.

Evaluation criteria used per idea:
- Recourse validity under uncertainty.
- Actionability and feasibility in credit operations.
- Fairness and explainability compliance impact.
- Compute and latency cost.
- Operational auditability.

## 3) P0/P1 Backlog Summary

| ID | Gap | Priority | Target outcome | Primary KPI gate |
|---|---|---|---|---|
| B1 | High-risk conversion gap | P0 | Convert denied high-risk customers | denied_high_risk_lift >= 0.03 (pilot) |
| B2 | Robust gate failures in hard denied | P0 | Reduce CI/reliability/worst-margin fails | denied_ci_violation_rate <= 0.80 |
| B3 | Low candidate diversity (DiCE inactive) | P0 | Multi-generator search diversity | dice_success_rate >= 0.15 |
| B4 | Fairness scope too narrow | P0 | Multi-segment fairness control | per-segment approval_gap <= 0.10 |
| B5 | Evaluation leakage risk | P0 | Strict split and OOT discipline | split compliance = 100% |
| B6 | No closed-loop business outcome | P1 | Real default/repayment impact tracking | 90-day outcome report each cycle |
| B7 | Telemetry not mandatory in prod | P0 | Full observability and audit readiness | telemetry enabled in 100% prod runs |
| B8 | Tail latency sensitivity | P0 | Stable p95/p99 under load | p99 <= 1800ms for 3 consecutive runs |
| B9 | Regulatory explanation depth | P0 | Compliant adverse action language | reason completeness = 100% |
| B10 | Governance maturity gap | P1 | Enterprise rollout controls | approval workflow compliance = 100% |

## 4) Detailed Backlog Design

### B1 - High-risk segment conversion redesign (P0)
Problem evidence:
- denied_high_risk_lift = 0.0 while global lift is positive.

Research synthesis:
- One-shot recourse often fails realism and feasibility in high-risk populations.
- Longitudinal counterfactual work shows temporal constraints improve plausibility.
- Robust and causal recourse papers indicate objective must include uncertainty-aware penalties, not only mean PD reduction.
- AReS shows subgroup-level summaries are useful to diagnose systematic recourse failures.

Recommended design:
1. Add `high_risk_objective` profile with stronger weights on gate pass terms.
2. Add multi-step transition planner (weekly or monthly steps), not single jump.
3. Expand high-risk action catalog with restructuring primitives:
- installment smooth trajectory
- utilization compression trajectory
- staged debt consolidation proxy
- optional collateral/guarantor placeholders controlled by policy
4. Add explicit high-risk policy constraints and per-step feasibility checks.

Code touchpoints:
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/recourse/action_space.py`
- `src/credit_coach/recourse/feasibility.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `configs/recourse.yaml`

KPI and acceptance:
- denied_high_risk_lift >= 0.03 (pilot), >= 0.06 (scale).
- high_risk_gate_pass_rate >= 0.15.
- high_risk_recourse_success_gap <= 0.08.

Test plan:
1. A/B: control vs high-risk profile on 1000 customers with fixed seed.
2. Stress scenario replay (macro shocks) for high-risk subgroup only.
3. Regression check: global fairness and latency must not exceed budget.

### B2 - Robust gate bottleneck reduction (P0)
Problem evidence:
- denied_ci_violation_rate, denied_reliability_violation_rate, denied_worst_margin_violation_rate are at or near 1.0.

Research synthesis:
- Split conformal gives distribution-free uncertainty baseline.
- Mondrian/partitioned conformal improves subgroup calibration behavior.
- Conformal Risk Control provides a framework for constraining risk-like losses.
- Banking model risk guidance emphasizes periodic revalidation and effective challenge.

Recommended design:
1. Add segment-conditional uncertainty profiles (`near`, `mid`, `high`).
2. Move from global conformal width to risk-band conditional widths.
3. Add denied-only optimizer term for worst-case margin and CI excess.
4. Schedule out-of-time recalibration cadence (monthly or quarterly).

Code touchpoints:
- `src/credit_coach/safety/statistical.py`
- `src/credit_coach/safety/validator.py`
- `src/credit_coach/recourse/generator.py`
- `configs/safety.yaml`

KPI and acceptance:
- denied_ci_violation_rate <= 0.80 (P0), <= 0.65 (P1).
- denied_reliability_violation_rate <= 0.85 (P0), <= 0.70 (P1).
- denied_worst_margin_violation_rate <= 0.85 (P0), <= 0.70 (P1).

Test plan:
1. Calibration quality by risk band.
2. OOT backtest on frozen split.
3. Bootstrap confidence interval stability by seed.

### B3 - Multi-generator candidate pool and diversity (P0)
Problem evidence:
- dice_success_rate = 0.0 and source diversity is weak.

Research synthesis:
- DiCE supports diverse candidates with explicit diversity objective.
- CARLA offers benchmark recourse methods and interfaces.
- FACE stresses path feasibility in high-density regions.

Recommended design:
1. Introduce `candidate_orchestrator`: Internal + DiCE + rule templates (+ optional CARLA method).
2. Add reranker objective with novelty term:
- gate_pass_prob
- action_cost
- similarity_penalty
- novelty_bonus
3. Enforce minimum per-source quota for denied population.
4. Track source entropy and action-level diversity.

Code touchpoints:
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/recourse/dice_baseline.py`
- `src/credit_coach/coaching/planner.py`
- `configs/recourse.yaml`

KPI and acceptance:
- dice_success_rate >= 0.15.
- best_source_internal_rate <= 0.85.
- candidate_pool_diversity_index >= 0.30.

Test plan:
1. Candidate pool ablation matrix by generator combination.
2. Timeout and fallback behavior test for DiCE.
3. Quality vs latency Pareto comparison.

### B4 - Fairness expansion to intersectional segments (P0)
Problem evidence:
- Current fairness tracking is mostly single-group oriented.

Research synthesis:
- Fairlearn MetricFrame supports multiple sensitive and control features.
- Fairlearn guidance highlights low-support subgroup risk.
- Aequitas and AIF360 provide richer group disparity diagnostics.
- Regulatory expectations require reasons and outcomes that are accurate and explainable, not only aggregate parity.

Recommended design:
1. Extend fairness configuration to segment sets:
- home_ownership
- income_band
- risk_band
- age_band (or compliant proxy design)
- intersections: income_band x risk_band, home_ownership x risk_band
2. Add minimum-support rule per segment.
3. Add fairness gates both global and per segment.
4. Add mitigation policy options (threshold post-processing only with explicit audit flag).

Code touchpoints:
- `src/credit_coach/evaluation/fairness.py`
- `src/credit_coach/cli/run_fairness.py`
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `configs/default.yaml`

KPI and acceptance:
- approval_gap <= 0.10 for every reportable segment.
- equalized_odds_gap_delta <= +0.01 after recourse policy updates.
- segment coverage compliance = 100%.

Test plan:
1. Segment matrix report with confidence intervals.
2. Low-support segment suppression and warning logic tests.
3. Fairness regression tests in CI for each release candidate.

### B5 - Leakage-safe evaluation and split protocol (P0)
Problem evidence:
- Risk of optimistic offline estimates if calibration/test boundaries are weak.

Research synthesis:
- scikit-learn leakage guidance: all fit operations must stay within train folds.
- Time-aware split is mandatory where temporal drift is expected.

Recommended design:
1. Enforce strict 4-way split: train/validation/calibration/test.
2. Conformal calibration must use only calibration split.
3. Add OOT split mode with cohort timestamp.
4. Add pipeline checks preventing transform/model fit on non-train partitions.

Code touchpoints:
- `src/credit_coach/cli/run_train.py`
- `src/credit_coach/data/split.py`
- `src/credit_coach/model/calibrate.py`
- `src/credit_coach/model/evaluate.py`
- `configs/model.yaml`

KPI and acceptance:
- split protocol compliance = 100%.
- OOT artifact present for every candidate = 100%.
- |AUC_test - AUC_OOT| <= 0.03 and |ECE_test - ECE_OOT| <= 0.02.

Test plan:
1. Unit tests for split boundaries.
2. CI gate that fails on leakage signature.
3. Reproducibility check with fixed seeds.

### B6 - Offline to online outcome feedback loop (P1)
Problem evidence:
- Lift is measured on model decision outcomes, not realized repayment behavior.

Research synthesis:
- MRM guidance requires outcomes analysis and continuous challenge.
- Off-policy evaluation literature can de-risk policy changes before full rollout.

Recommended design:
1. Build decision-outcome fact table keyed by decision_id.
2. Add delayed labels (30/60/90-day proxies).
3. Add treatment/control policy buckets for live evaluation.
4. Add offline policy evaluation module (IPS/DR baseline, then SWITCH-like estimator if needed).

Code touchpoints:
- `src/credit_coach/storage/models.py`
- `src/credit_coach/storage/repository.py`
- `src/credit_coach/portfolio/impact.py`
- `src/credit_coach/retraining/train_job.py`
- `src/credit_coach/cli/run_monitoring.py`

KPI and acceptance:
- 90-day portfolio outcome report published each cycle.
- treatment not worse than control on default proxy beyond tolerance.
- expected margin delta tracked per segment.

Test plan:
1. Synthetic delayed-label pipeline integration test.
2. Backfill consistency test (idempotent writes).
3. OPE confidence interval sanity tests.

### B7 - Mandatory telemetry in production profile (P0)
Problem evidence:
- Smoke can pass while telemetry is disabled.

Research synthesis:
- OpenTelemetry + OTLP is standard for metrics/traces/logs transport.
- Prometheus histogram guidance is required for quantile/SLO correctness.

Recommended design:
1. Require telemetry enabled in production smoke profile.
2. Export mandatory metrics set:
- lift funnels
- denied gate violation rates
- generator source shares
- latency histogram buckets
- failure reason taxonomy
3. Add exporter health and ingestion lag gates.
4. Add alert playbook and severity mapping.

Code touchpoints:
- `src/credit_coach/ops/telemetry.py`
- `src/credit_coach/ops/monitoring.py`
- `src/credit_coach/cli/run_production_smoke.py`
- `configs/default.yaml`

KPI and acceptance:
- telemetry enabled = 100% in prod runs.
- exporter success ratio >= 99%.
- metric ingest lag p95 <= 60s.

Test plan:
1. Local OTLP collector integration test.
2. Metrics cardinality budget test.
3. Failure injection (exporter down) and alert path validation.

### B8 - Tail latency hardening and deterministic fallback (P0)
Problem evidence:
- p99 is sensitive to small search-budget changes.

Research synthesis:
- Tail latency must be controlled via hard budgets and bounded fallback.
- Dynamic task mapping patterns support controlled parallel workload execution.

Recommended design:
1. Add hard per-customer compute budget.
2. Add circuit breaker to deterministic fallback plan.
3. Add bounded parallelism and queue backpressure controls.
4. Add timeout taxonomy and fallback reason metrics.

Code touchpoints:
- `src/credit_coach/cli/run_batch_recourse_eval.py`
- `src/credit_coach/recourse/generator.py`
- `src/credit_coach/ops/monitoring.py`
- `configs/recourse.yaml`

KPI and acceptance:
- p95 <= 400ms and p99 <= 1800ms for 3 consecutive 1000-customer runs.
- timeout_or_fallback_rate <= 2%.
- error_rate <= 0.5%.

Test plan:
1. Load tests at 200/500/1000 batches.
2. Stress with lowered compute budget.
3. Verify deterministic fallback reproducibility.

### B9 - Regulatory explanation layer and reason-code system (P0)
Problem evidence:
- Technical plan exists, but adverse-action reasoning is not yet fully structured for audits.

Research synthesis:
- ECOA/Reg B requires specific principal reasons.
- CFPB 2022-03 and 2023-03 clarify black-box complexity is not an excuse.
- Model cards and policy cards improve governance traceability.

Recommended design:
1. Build reason-code dictionary mapped to actual model and policy factors.
2. Add adverse action generation template with:
- principal reasons
- factor details
- remediation hints (compliant, non-misleading)
3. Publish model card + recourse policy card each release.
4. Add legal QA checks for vague or generic reason leakage.

Code touchpoints:
- `src/credit_coach/coaching/messaging.py`
- `src/credit_coach/policy/engine.py`
- `src/credit_coach/cli/run_audit_verify.py`
- `src/credit_coach/cli/run_governance_report.py`

KPI and acceptance:
- adverse_action_reason_completeness = 100%.
- specific_reason_validation_pass_rate >= 99%.
- model_card_and_policy_card published each candidate.

Test plan:
1. Explanation unit tests for top denied scenarios.
2. Lint tests against banned vague reason phrases.
3. Audit sample manual review checklist.

### B10 - Governance hardening (P1)
Problem evidence:
- Release process works, but enterprise change controls are not fully formalized.

Research synthesis:
- SR 11-7, OCC handbook, and BCBS239 require governance, lineage, and challenge.
- AI regulation trend increases need for technical documentation and incident handling.

Recommended design:
1. Formal approval workflow: model owner + risk + compliance + ops.
2. Immutable release package:
- model hash
- config hash
- data snapshot hash
- test evidence hashes
3. Champion-challenger rollout plus rollback triggers.
4. Quarterly governance drill including rollback rehearsal.

Code touchpoints:
- `src/credit_coach/retraining/governance.py`
- `src/credit_coach/model/registry.py`
- `src/credit_coach/utils/hashing.py`
- `src/credit_coach/cli/run_governance_report.py`

KPI and acceptance:
- approval workflow compliance = 100%.
- release package completeness = 100%.
- rollback drill pass = 100% quarterly.

Test plan:
1. Simulated bad-release rollback scenario.
2. Artifact integrity check in CI.
3. Audit trail replay from any release id.

## 5) Cross-Cutting View: Technology Gap vs Algorithm Gap vs Agent Need
Technology gap status:
- Medium. Core stack is adequate; main issue is orchestration, observability, and governance depth.

Algorithm gap status:
- High. Objective functions and candidate search are not sufficiently aligned with hard denied/high-risk conversion goals.

Should an autonomous agent be added now?
- Not as first fix for conversion KPI.
- Priority should stay on objective redesign, uncertainty-aware optimization, and recourse candidate diversity.
- Agent can be added later for operations automation only:
1. automatic experiment scheduling
2. anomaly triage for metrics
3. governance checklist automation

## 6) Phase Plan (Execution Order)

### Phase 0 - Readiness (2-3 days)
1. Lock KPI contract in `ops/kpi_contract.py` and smoke gates.
2. Freeze baseline artifacts and seeds.
3. Prepare A/B templates for all P0 workstreams.

### Phase 1 - P0 Conversion Core (1-2 weeks)
1. B1 high-risk redesign.
2. B2 robust gate optimization.
3. B3 candidate orchestrator.
4. Daily 1000-customer evaluation and delta dashboard.

### Phase 2 - P0 Safety and Reliability (1 week)
1. B4 fairness expansion.
2. B5 split leakage hardening.
3. B7 telemetry mandatory.
4. B8 tail latency controls.
5. B9 explanation compliance layer.

### Phase 3 - P1 Institutionalization (2-4 weeks)
1. B6 outcome feedback loop and OPE.
2. B10 governance and rollout institutionalization.

## 7) KPI Gate Contract (Release NO_GO unless all pass)
Mandatory gates for production candidate:
1. denied_to_approved_lift >= 0.10
2. denied_high_risk_lift >= 0.03
3. denied_ci_violation_rate <= 0.80
4. denied_reliability_violation_rate <= 0.85
5. dice_success_rate >= 0.15
6. p95 <= 400ms and p99 <= 1800ms
7. fairness per segment within defined thresholds
8. telemetry enabled and exporter success >= 99%
9. adverse action reason completeness = 100%
10. release artifact completeness = 100%

## 8) Similar Business Model Patterns and Practical Adaptation
Observed patterns from lending AI vendors:
- Approval and risk must be optimized jointly, not as separate objectives.
- Compliance artifacts (reasoning, fairness, governance) are product requirements, not post-hoc documents.
- Integration-first architecture (decision layer, not core replacement) accelerates production rollout.

How to apply here:
1. Keep Credit Coach as modular decision and recourse layer.
2. Hard-wire compliance outputs into the serving path.
3. Treat high-risk conversion as the first business KPI, not a side metric.

## 9) Source Index
Primary research and recourse:
- Actionable Recourse (Ustun et al., 2019): https://arxiv.org/abs/1809.06514
- DiCE paper: https://arxiv.org/abs/1905.07697
- DiCE repo: https://github.com/interpretml/DiCE
- DiCE docs: https://interpret.ml/DiCE/
- CARLA repo: https://github.com/carla-recourse/CARLA
- FACE paper: https://arxiv.org/abs/1909.09369
- AReS (NeurIPS 2020): https://proceedings.neurips.cc/paper/2020/hash/8ee7730e97c67473a424ccfeff49ab20-Abstract.html
- Robust causal recourse (ICML 2022): https://proceedings.mlr.press/v162/dominguez-olmedo22a.html
- Longitudinal counterfactuals (2024): https://arxiv.org/abs/2403.00105
- Robust CE survey (IJCAI 2024): https://www.ijcai.org/proceedings/2024/894

Uncertainty and calibration:
- MAPIE docs: https://mapie.readthedocs.io/
- MAPIE Mondrian docs: https://mapie.readthedocs.io/en/v0.9.0/_modules/mapie/mondrian.html
- Conformal Risk Control (ICLR 2024): https://research.google/pubs/conformal-risk-control/

Fairness tooling:
- Fairlearn intersecting groups: https://fairlearn.org/main/user_guide/assessment/intersecting_groups.html
- Fairlearn ThresholdOptimizer: https://fairlearn.org/main/api_reference/generated/fairlearn.postprocessing.ThresholdOptimizer.html
- Aequitas: https://github.com/dssg/aequitas
- AIF360: https://github.com/IBM/AIF360/

Modeling and eval discipline:
- sklearn leakage pitfalls: https://scikit-learn.org/1.5/common_pitfalls.html
- sklearn TimeSeriesSplit: https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
- XGBoost monotonic constraints: https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html

Observability and operations:
- OpenTelemetry Python exporters: https://opentelemetry.io/docs/languages/python/exporters/
- Prometheus histograms: https://prometheus.io/docs/practices/histograms/
- Prometheus instrumentation: https://prometheus.io/docs/practices/instrumentation/
- FastAPI workers: https://fastapi.tiangolo.com/deployment/server-workers/
- Uvicorn deployment: https://www.uvicorn.org/deployment/
- Airflow dynamic task mapping: https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html

Regulation and governance:
- Fed SR 11-7: https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
- OCC Bulletin 2011-12: https://www.occ.gov/news-issuances/bulletins/2011/bulletin-2011-12.html
- OCC Model Risk Handbook (2021): https://occ.treas.gov/publications-and-resources/publications/comptrollers-handbook/files/model-risk-management/index-model-risk-management.html
- BCBS239: https://www.bis.org/publ/bcbs239.htm
- CFPB Circular 2022-03: https://www.consumerfinance.gov/compliance/circulars/circular-2022-03-adverse-action-notification-requirements-in-connection-with-credit-decisions-based-on-complex-algorithms/
- CFPB Circular 2023-03: https://www.consumerfinance.gov/compliance/circulars/circular-2023-03-adverse-action-notification-requirements-and-the-proper-use-of-the-cfpbs-sample-forms-provided-in-regulation-b/
- CFPB Reg B 1002.9: https://www.consumerfinance.gov/rules-policy/regulations/1002/9/
- 12 CFR 1002.9 text: https://www.law.cornell.edu/cfr/text/12/1002.9
- EU AI Act official text (Regulation 2024/1689): https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
- NIST AI RMF 1.0: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10

Documentation standards:
- Model Cards paper: https://arxiv.org/abs/1810.03993
- Model Card Toolkit repo: https://github.com/tensorflow/model-card-toolkit
- Datasheets for Datasets: https://arxiv.org/abs/1803.09010

Industry reference signals:
- Upstart IR updates: https://ir.upstart.com/
- Upstart lender platform: https://www.upstart.com/lenders/personal-lending-lender-branded
- Zest AI underwriting: https://www.zest.ai/product/underwriting

