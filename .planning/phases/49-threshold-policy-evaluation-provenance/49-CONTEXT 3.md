# Phase 49: Threshold Policy Evaluation & Provenance - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Evaluate bounded threshold-policy candidates against the shipped `v2.2` decision baseline, keep every candidate analysis-only, and persist exact policy provenance into collection and pilot-facing evidence artifacts. This phase does not promote a new live policy yet, does not change action semantics, and does not reopen any shipped trust layer from Phases `40` through `48`.

</domain>

<decisions>
## Implementation Decisions

### Baseline policy contract
- The live baseline remains the shipped decision owner in [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py), with `decision_policy_version = v2.1_phase_40_5`.
- Phase 49 must treat that live policy as the only runtime truth. Candidate threshold policies are analysis-only and cannot overwrite per-customer decision truth, selected surfaces, or operator packet outputs.
- The baseline comparison contract mirrors the current live gates exactly:
  - reject floor stays owned by existing `zero_step / no_viable_plan / invalid_best_path / expected_pd_improvement < 0.01 / realization_anchor < 0.10`
  - approve gate stays anchored to `decision_confidence >= 0.60`, `realization_anchor >= 0.50`, `expected_pd_improvement >= 0.02`, readiness in `{now, week_4}`, and the existing `approval_ready_4w or strong_execution` plus current offer-maturity exclusions
  - conditional gate stays anchored to `decision_confidence >= 0.40`, `realization_anchor >= 0.20`, and `expected_pd_improvement >= 0.01`

### Candidate bounded threshold levers
- Phase 49 may tune only the existing numeric gate minima already modeled in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py):
  - `approved_realization_min`
  - `approved_improvement_min`
  - `approved_confidence_min`
  - `conditional_realization_min`
  - `conditional_improvement_min`
  - `conditional_confidence_min`
- Phase 49 may not change:
  - readiness taxonomy or readiness labels
  - offer-maturity taxonomy
  - `zero_step`, `raw_contract_pass`, `parity_pass`, `data_issue`, or invalid-winner hard-stop behavior
  - DICE, planner-quality, or selected-surface semantics
- Default candidate ladder should stay small and deterministic:
  - shipped baseline row from `v2.1_phase_40_5`
  - `analysis_mild_relax_v2_3a`
    - approved: realization `0.49`, improvement `0.019`, confidence `0.58`
    - conditional: realization `0.19`, improvement `0.009`, confidence `0.35`
  - `analysis_relaxed_v2_3a`
    - approved: realization `0.48`, improvement `0.018`, confidence `0.55`
    - conditional: realization `0.18`, improvement `0.008`, confidence `0.30`
  - `analysis_strict_control_v2_3a`
    - approved: realization `0.55`, improvement `0.025`, confidence `0.68`
    - conditional: realization `0.22`, improvement `0.012`, confidence `0.45`
- The strict profile is a control, not a promotion target. The phase exists to test whether bounded relaxation can safely improve `APPROVED + CONDITIONAL` yield.

### Provenance and comparison contract
- Provenance must distinguish live decision truth from analysis policy truth:
  - `decision_policy_version` remains the policy that produced the actual customer decision
  - `policy_version_evaluated` remains the baseline policy version of the evaluated run
  - `candidate_policy_versions_compared` lists all analysis candidate profiles
- Add one deterministic candidate catalog artifact for replayability, for example `calibration/policy_profile_catalog.json`, containing exact thresholds for the baseline mirror and every candidate profile.
- Add one recommendation-level evaluation summary for the run, with fields equivalent to:
  - `recommended_candidate_policy_version`
  - `recommended_candidate_status = shortlisted | blocked | no_safe_uplift`
  - `recommended_candidate_reason`
- Candidate policy rows in `policy_comparison.csv` remain explicitly `analysis_only = 1`.
- If no candidate safely improves yield, the correct output is explicit `no_safe_uplift`, not silent fallback or implicit promotion.

### Guardrails and acceptance posture
- Phase 49 is an evaluation-and-proof phase, not a live policy-promotion phase.
- Candidate policy comparison must keep all shipped `v2.2` trust counters clean:
  - no selected invalid winners
  - no selected-surface drift
  - no operator packet coherence regressions
- Primary evidence cohorts remain:
  - `pilot_mixed`
  - `risk_band_balanced`
  - `offer_needed_balanced`
- Primary comparison outputs must show:
  - `approved_share`
  - `conditional_share`
  - `approve_plus_conditional_share`
  - `rejected_share`
  - `internal_needs_review_share`
  - `false_positive_proxy`
  - decision shift matrix
  - segment breakdown over at least `risk_band`, `expected_readiness`, `conditional_type`, `offer_needed_flag`, and `decision_confidence_band`
- Phase 49 is complete when it can either:
  - shortlist one or more bounded candidate policies for Phase 50+, or
  - produce an explicit evidence-backed `no_safe_uplift` conclusion

### Claude's Discretion
- Exact artifact filenames beyond the required comparison set, as long as one candidate-catalog artifact and one recommendation summary artifact exist.
- Whether candidate profile metadata is stored in JSON, markdown + JSON, or additive manifest fields, as long as replay and audit are deterministic.
- Exact naming of “mild relax” versus “relaxed” candidate profiles, as long as the policy ladder stays small, deterministic, and consistent across artifacts.

</decisions>

<specifics>
## Specific Ideas

- Use the shipped `v2.2` baseline as the trust floor and make Phase 49 prove whether bounded numeric gate changes can move the funnel before any live promotion.
- Keep the candidate ladder intentionally small; this phase is about interpretable policy evidence, not broad search.
- Treat offer/readiness as measured segment lenses in Phase 49, not as new decision levers yet. Their decision-rule use opens in Phase 50.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py): already owns `DEFAULT_CANDIDATE_POLICIES`, `_candidate_policy_row(...)`, `false_positive_proxy`, `build_policy_comparison(...)`, readiness distribution, and decision shift matrix generation.
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already writes `policy_comparison.csv`, `decision_shift_matrix.csv`, `segment_breakdown.csv`, `calibration_review.md`, and carries `policy_version_evaluated` plus `candidate_policy_versions_compared` into the collection manifest and summary.
- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py): already compares policy versions between refresh runs and is the natural downstream consumer for a future preferred-policy promotion.
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py): already validates expected policy version consistency across collection, explanation packs, and pilot package surfaces.
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py): remains the sole owner of live decision truth and the shipped baseline policy version.

### Established Patterns
- Phase 41 already established the shadow-calibration contract: candidate policies are analysis-only and never overwrite raw customer decision truth.
- Collection manifests and summaries are the canonical place for cohort purpose, policy version, candidate versions compared, and calibration summary metadata.
- Large-sample reruns on `pilot_mixed`, `risk_band_balanced`, and `offer_needed_balanced` are the standard proof surface for policy and funnel claims.
- Pilot refresh and QA flows already expect explicit policy version provenance, so Phase 49 should extend those contracts rather than invent a second packaging path.

### Integration Points
- Extend [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) so candidate policy catalogs and recommendation summaries are deterministic and replayable.
- Extend [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) so policy-profile provenance and candidate recommendations land in manifest, summary, and calibration artifacts.
- Reuse [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) only as a downstream consumer of policy provenance, not as a place to redefine evaluation logic.
- Keep [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) and [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) untouched except for additive provenance fields if absolutely required.

</code_context>

<deferred>
## Deferred Ideas

- Expanding recommendation/action semantics beyond the current numeric action space belongs to a later milestone, not Phase 49.
- Using offer maturity or readiness as direct decision levers belongs to Phase 50, not Phase 49.
- Cleaning the pandas concat `FutureWarning` in batch artifact collection is useful but not part of this phase’s policy-evaluation boundary.

</deferred>

---

*Phase: 49-threshold-policy-evaluation-provenance*
*Context gathered: 2026-04-02*
