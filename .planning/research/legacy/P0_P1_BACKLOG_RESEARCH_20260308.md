# CREDIT COACH - P0/P1 Backlog (Research-Backed) - 2026-03-08

## 1) Baseline (Current State)
Reference run (treatment): `20260308_010749_837f33_55b99a`
Reference smoke run: `20260308_010845_0ed7c7_a7319d` (overall `GO`)

Current key metrics:
- `denied_to_approved_lift = 0.0928`
- `denied_high_risk_lift = 0.0`
- `latency_p95_ms = 286.88`
- `latency_p99_ms = 1573.52`
- `error_rate = 0.0`
- `fairness_approval_gap_after = 0.0843`
- `fairness_equalized_odds_gap_after = 0.1163`
- `denied_reliability_violation_rate = 1.0`
- `denied_ci_violation_rate = 1.0`
- `denied_worst_margin_violation_rate = 1.0`
- `dice_success_rate = 0.0`

Interpretation:
- System now passes release gate, but still has structural weaknesses in hardest risk segments, robustness diagnostics, and governance depth.

## 2) P0/P1 Backlog Summary

| ID | Backlog Item | Priority | Why Now | Core KPI Gate (acceptance) |
|---|---|---|---|---|
| B1 | High-risk segment conversion redesign | P0 | `denied_high_risk_lift=0.0` | `denied_high_risk_lift >= 0.03` (pilot), then `>= 0.06` |
| B2 | Robust-gate bottleneck reduction | P0 | denied hard-cases fail robustness gates | `denied_ci_violation_rate <= 0.80`, `denied_reliability_violation_rate <= 0.85` |
| B3 | Candidate diversity + multi-generator pool | P0 | `dice_success_rate=0.0` | `dice_success_rate >= 0.15`, source entropy increase >= 30% |
| B4 | Multi-attribute fairness expansion | P0 | single-feature fairness is inadequate | all tracked segments: `approval_gap <= 0.10`, EO delta <= 0.01 |
| B5 | Leakage-safe model evaluation protocol | P0 | calibration/test separation risk | strict split compliance = 100%, OOT report mandatory |
| B6 | Offline-to-online outcome loop | P1 | no real repayment-grounded optimization | 90-day policy delta report published each cycle |
| B7 | Mandatory telemetry in prod profile | P0 | telemetry currently optional | prod runs: `require_telemetry_enabled=true` and exporter success >= 99% |
| B8 | Tail-latency hardening | P0 | p99 sensitive to config | 3 consecutive 1000-batch runs: `p99 <= 1800`, `p95 <= 400` |
| B9 | Regulatory explanation layer | P0 | adverse-action explainability depth | adverse action reason completeness = 100% |
| B10 | Model/policy governance hardening | P1 | release controls not yet enterprise-grade | approval workflow compliance = 100%, rollback drill pass |

## 3) Detailed Backlog Items (Research + Implementation)

### B1 - High-risk segment conversion redesign (P0)
Problem:
- Total lift is good, but highest-risk denied segment is not converted.

Research signal:
- Robust recourse methods show minimum-cost recourse can fail under uncertainty and must be explicitly robustness-aware.
- Longitudinal counterfactual literature shows one-shot recourse can be implausible; multi-step temporal constraints improve realism.
- AReS/global recourse summaries are effective for subgroup diagnosis and policy-level bias surfacing.

Implementation plan:
1. Add `high_risk_objective` block in recourse config with explicit weights for `ci`, `reliability`, and subgroup fairness penalty.
2. Introduce `multi_step_high_risk_planner` with week-by-week or month-by-month transitions and stricter feasibility rules.
3. Extend action catalog for high-risk customers with restructuring-aware actions (installment smoothing, utilization compression trajectory, collateral/guarantor placeholders where allowed by policy).
4. Add high-risk-only funnel metrics: `high_risk_denied_with_candidate`, `high_risk_gate_pass`, `high_risk_approved`.

KPI gates:
- `denied_high_risk_lift >= 0.03` in pilot (P0), `>= 0.06` in scale-up (P1).
- High-risk fairness constraints: `high_risk_recourse_success_gap <= 0.08`.

### B2 - Robust-gate bottleneck reduction (P0)
Problem:
- Denied hardest cases show near-total gate failure (`ci/reliability/worst_margin` violations very high).

Research signal:
- Conformal methods are suitable for uncertainty control and can be adapted by subgroup partitioning (Mondrian-style).
- Model risk standards (SR 11-7/OCC handbook) emphasize ongoing outcomes analysis and effective challenge, not static calibration.

Implementation plan:
1. Add segment-conditional uncertainty profiles: `uncertainty_profile: near|mid|high`.
2. Use adaptive conformal by score-bin and optional Mondrian partition by risk band.
3. Run quarterly out-of-time conformal recalibration with frozen holdout.
4. Add denied-target optimizer term that penalizes worst-case margin violations more aggressively in high-risk band.

KPI gates:
- `denied_ci_violation_rate <= 0.80`.
- `denied_reliability_violation_rate <= 0.85`.
- `denied_worst_margin_violation_rate <= 0.85`.

### B3 - Candidate diversity + multi-generator pool (P0)
Problem:
- Internal planner dominates almost all plans; DiCE path is effectively inactive.

Research signal:
- DiCE supports random/genetic/kdtree and explicitly targets diverse actionable CFs.
- CARLA and Alibi provide alternative recourse/counterfactual generation baselines useful for portfolio diversity.

Implementation plan:
1. Build `candidate_orchestrator` to merge Internal + DiCE + Rule templates (+ optional CARLA baseline).
2. Add reranker objective: `gate_pass_prob - cost - similarity_penalty + novelty_bonus`.
3. Add plan diversity metrics: source entropy, feature-action Jaccard distance, subgroup coverage.
4. Re-enable DiCE fallback policies with strict timeout budgets and non-zero minimum traffic share.

KPI gates:
- `dice_success_rate >= 0.15`.
- `best_source_internal_rate <= 0.85`.
- `candidate_pool_diversity_index >= 0.30`.

### B4 - Multi-attribute fairness expansion (P0)
Problem:
- Fairness currently anchored to one attribute; intersectional risk is under-observed.

Research signal:
- Fairlearn MetricFrame supports intersecting groups and explicitly warns to track group counts.
- Aequitas provides practical audit flows for disparity and threshold-based mitigation.
- CFPB ECOA guidance requires specific and accurate adverse-action reasons regardless of model complexity.

Implementation plan:
1. Replace single fairness group config with `fairness.segment_sets`:
   - `home_ownership`
   - `income_band`
   - `risk_band`
   - intersections: `income_band x risk_band`, `home_ownership x risk_band`.
2. Add minimum support rule per segment: `n >= min_segment_n` (or confidence interval width constraint).
3. Add segment-level gates in smoke report, not only global aggregate.
4. Add mitigation fallback: group-aware threshold or post-processing only when disparity breaches hard limits.

KPI gates:
- For every reportable segment/intersection: `approval_gap <= 0.10`.
- `equalized_odds_gap_delta <= 0.01` globally and for protected segment bundles.
- segment coverage compliance: 100% (no silent segment drop).

### B5 - Leakage-safe model evaluation protocol (P0)
Problem:
- Evaluation process still needs stricter anti-leakage discipline in split and calibration workflow.

Research signal:
- scikit-learn pitfall docs: fitting transforms on non-train data causes optimistic bias.
- TimeSeriesSplit guidance: for temporal data, future leakage must be prevented.

Implementation plan:
1. Enforce 4-way split contract: `train / validation / calibration / test`.
2. Move conformal calibration to dedicated calibration split only (never test).
3. Add time-based split mode for credit cohorts (OOT mandatory for release candidates).
4. Add CI check that fails if any transformer/model `fit` touches non-train partitions.

KPI gates:
- Split protocol compliance = 100%.
- OOT report artifact present = 100%.
- `|AUC_test - AUC_OOT| <= 0.03`, `|ECE_test - ECE_OOT| <= 0.02`.

### B6 - Offline-to-online outcome loop (P1)
Problem:
- Current lift is decision-level; real repayment/default improvement loop is missing.

Research signal:
- MRM standards require outcomes analysis and continuous model challenge, not only static pre-deploy metrics.
- Mature lending platforms publicly emphasize continuous portfolio optimization and policy iteration.

Implementation plan:
1. Create `decision_outcome_fact` table keyed by decision id and delayed repayment labels.
2. Add online policy buckets: control vs treatment for selected segments.
3. Add 30/60/90-day portfolio KPIs: delinquency, charge-off proxy, realized margin.
4. Add causal/off-policy evaluation layer before full treatment rollout.

KPI gates:
- 90-day realized delinquency delta available for each release.
- Pilot treatment: no worse than control on default proxy while preserving lift.

### B7 - Mandatory telemetry in prod profile (P0)
Problem:
- Pipeline can pass with telemetry disabled.

Research signal:
- OpenTelemetry exporter docs and Prometheus practices support production-grade metric transport and SLO monitoring.

Implementation plan:
1. Set production smoke profile `require_telemetry_enabled=true`.
2. Export mandatory metrics: lift, gate violations, recourse gaps, latency histogram buckets, failure reasons.
3. Add telemetry health gate: exporter success ratio and end-to-end lag.
4. Add alert playbooks for SLO breaches.

KPI gates:
- Telemetry enabled and exported in 100% production runs.
- Export success >= 99%.
- Metric ingest lag p95 <= 60s.

### B8 - Tail-latency hardening (P0)
Problem:
- Tail latency shifts sharply with budget/quota tuning.

Research signal:
- Prometheus histogram guidance for quantile/SLO monitoring.
- FastAPI/Uvicorn worker guidance indicates explicit worker/process sizing is required for stable serving.
- Airflow dynamic task mapping supports runtime-scaled orchestration for batch recourse workloads.

Implementation plan:
1. Hard per-customer compute budget with deterministic cutoff behavior.
2. Circuit breaker: if planner exceeds stage budget, fallback to safe deterministic template plan.
3. Capacity profile tuning by worker/process count and queue backpressure.
4. Add dynamic batch orchestration for large runs (mapped tasks + bounded parallelism).

KPI gates:
- `p95_latency <= 400ms` and `p99_latency <= 1800ms` across 3 consecutive 1000-customer runs.
- Timeouts/fallback rate <= 2%.

### B9 - Regulatory explanation layer (P0)
Problem:
- Technical recommendations exist, but legally robust adverse-action reasoning is not yet formalized enough.

Research signal:
- ECOA/Reg B requires specific principal reasons for adverse action.
- CFPB circulars explicitly state black-box complexity is not an excuse for missing reasons.
- Model card framework is now standard for transparent model documentation.

Implementation plan:
1. Build `reason_code_dictionary` mapped to model factors and policy constraints.
2. Generate adverse action payload with top principal reasons + remediation hints (actionable but compliant).
3. Add `model_card` and `recourse_policy_card` artifacts per release.
4. Add legal QA test set for explanation quality and consistency.

KPI gates:
- Adverse-action payload completeness = 100%.
- Specific-reason validation pass rate >= 99% on audit sample.
- Model card/policy card published for every production candidate.

### B10 - Governance hardening (P1)
Problem:
- Technical release works, but enterprise governance is not fully institutionalized.

Research signal:
- SR 11-7, OCC handbook and BCBS239 all require strong governance, lineage, auditability, and effective challenge.
- EU AI Act trajectory increases pressure for traceability and high-risk controls in credit-related contexts.

Implementation plan:
1. Define approval workflow: model owner, risk, compliance, ops sign-off.
2. Enforce immutable release package: model hash, config hash, data hash, validation evidence.
3. Add champion-challenger policy with rollback triggers.
4. Quarterly governance drill: rollback rehearsal + audit chain verification.

KPI gates:
- Approval workflow compliance = 100%.
- Release artifact completeness = 100%.
- Rollback drill success = 100% per quarter.

## 4) Phased Execution Plan

Phase A (P0 Core, 2-4 weeks):
1. B1, B2, B3, B4, B5, B7, B8, B9 implementation skeleton and metrics instrumentation.
2. 1000-customer nightly batch with automatic gate report publication.
3. Freeze a production profile with all P0 gates hard-fail.

Phase B (P0 Stabilization, 2-3 weeks):
1. Hyperparameter/profile sweeps under fixed data snapshot.
2. Confirm 3 consecutive successful smoke runs.
3. Complete legal/compliance review on explanation outputs.

Phase C (P1 Institutionalization, 4-8 weeks):
1. B6 delayed outcomes loop and policy impact reporting.
2. B10 governance and controlled rollout architecture.
3. Expand risk committee reporting pack with BCBS239-compatible lineage sections.

## 5) Similar Business Model Patterns (How They Can Be Applied)

Observed market pattern:
- AI lending marketplaces (e.g., Upstart) emphasize bank partnership scale, automation, and faster digital underwriting flows.
- Lending AI providers (e.g., Zest AI) emphasize approval-risk optimization, fairness messaging, and deep LOS integrations.

Pragmatic adaptation for this project:
1. Keep underwriting + recourse as a decisioning layer that is integration-first (not monolithic core replacement).
2. Treat fairness and explanation as first-class product surfaces, not only compliance artifacts.
3. Add portfolio-level optimization loop (decision quality + operational SLAs + realized loss outcomes).

## 6) Source Index (Primary and Official where possible)

Recourse / Counterfactuals:
- Actionable Recourse (FAccT 2019 / arXiv): https://arxiv.org/abs/1809.06514
- DiCE paper (FAccT 2020): https://arxiv.org/abs/1905.07697
- DiCE repo: https://github.com/interpretml/DiCE
- DiCE docs: https://interpret.ml/DiCE/
- DiCE model-agnostic notebook: https://interpret.ml/DiCE/notebooks/DiCE_model_agnostic_CFs.html
- CARLA repo: https://github.com/carla-recourse/CARLA
- Alibi counterfactual docs: https://docs.seldon.io/projects/alibi/en/stable/methods/CF.html
- AReS (NeurIPS 2020): https://proceedings.neurips.cc/paper/2020/hash/8ee7730e97c67473a424ccfeff49ab20-Abstract.html
- Learning Models for Actionable Recourse (NeurIPS 2021): https://proceedings.neurips.cc/paper_files/paper/2021/hash/9b82909c30456ac902e14526e63081d4-Abstract.html
- Adversarially robust causal recourse (ICML 2022): https://proceedings.mlr.press/v162/dominguez-olmedo22a.html
- Longitudinal Counterfactuals (2024): https://arxiv.org/abs/2403.00105

Uncertainty / Conformal:
- MAPIE docs: https://mapie.readthedocs.io/
- MAPIE Mondrian CP module docs: https://mapie.readthedocs.io/en/v0.9.0/_modules/mapie/mondrian.html

Fairness Tooling:
- Fairlearn intersecting groups docs: https://fairlearn.org/main/user_guide/assessment/intersecting_groups.html
- Aequitas repo: https://github.com/dssg/aequitas

Model evaluation and leakage:
- scikit-learn common pitfalls (data leakage): https://scikit-learn.org/1.5/common_pitfalls.html
- scikit-learn TimeSeriesSplit: https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.TimeSeriesSplit.html

Observability and ops:
- OpenTelemetry Python exporters: https://opentelemetry.io/docs/languages/python/exporters/
- Prometheus histograms guidance: https://prometheus.io/docs/practices/histograms/
- Prometheus instrumentation practices: https://prometheus.io/docs/practices/instrumentation/
- Airflow dynamic task mapping: https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html
- FastAPI deployment concepts: https://fastapi.tiangolo.com/deployment/server-workers/
- Uvicorn deployment settings: https://www.uvicorn.org/deployment/

Regulation / governance:
- Federal Reserve SR 11-7: https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
- OCC Bulletin 2011-12: https://www.occ.gov/news-issuances/bulletins/2011/bulletin-2011-12.html
- OCC Model Risk handbook (2021): https://occ.treas.gov/publications-and-resources/publications/comptrollers-handbook/files/model-risk-management/index-model-risk-management.html
- BCBS 239 principles: https://www.bis.org/publ/bcbs239.htm
- CFPB circular on black-box adverse action: https://www.consumerfinance.gov/about-us/newsroom/cfpb-acts-to-protect-the-public-from-black-box-credit-models-using-complex-algorithms/
- CFPB Regulation B §1002.9: https://www.consumerfinance.gov/rules-policy/regulations/1002/9/
- 12 CFR 1002.9 text: https://www.law.cornell.edu/cfr/text/12/1002.9
- EU AI Act text (Regulation 2024/1689): https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng
- NIST AI RMF 1.0: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10

Business model references:
- Upstart lender platform page: https://www.upstart.com/lenders/personal-lending-lender-branded
- Upstart company overview: https://www.upstart.com/about
- Example Upstart partnership release: https://ir.upstart.com/news-releases/news-release-details/liberty-savings-bank-selects-upstart-personal-lending/
- Zest AI underwriting page: https://www.zest.ai/product/underwriting
- Zest AI company page: https://www.zest.ai/

