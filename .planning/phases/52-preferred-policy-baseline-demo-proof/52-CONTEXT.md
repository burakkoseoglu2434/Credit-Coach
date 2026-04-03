# Phase 52: Preferred Policy Baseline & Demo Proof - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 52 closes `v2.3` by selecting the honest demo/pilot baseline from the already-evaluated Phase `49-51` evidence, packaging that baseline into the standard artifact and pilot-refresh flows, and documenting why the bounded threshold and outcome-rule candidates were not adopted.

This phase does **not**:

- add new threshold families
- add new outcome-rule families
- expand action semantics
- reopen trust-repair work from Phases `40` through `48`
- pretend that a promotable uplift profile exists when the evidence says otherwise

Phase 52 owns:

- one preferred baseline contract for demos and pilot refreshes
- one fallback demo profile contract for first customer conversations
- one explicit non-adoption record for every bounded candidate already evaluated in Phases `49` and `50`
- one demo-proof package that turns the `no_safe_uplift` and `structural_cohort_limited` findings into honest, reusable pilot-facing evidence
- one clean handoff note that frames what the next milestone must solve without widening scope inside `v2.3`

</domain>

<decisions>
## Implementation Decisions

### Exact scope of Phase 52

- Phase 52 should treat Phase `49`, Phase `50`, and Phase `51` outputs as the full candidate universe for `v2.3`.
- The phase should select and package a baseline from those already-locked results; it should not run a new search or create a new promotion lane.
- Preferred and fallback profiles must both preserve the shipped live decision owner:
  - `decision_policy_version = v2.1_phase_40_5`
  - selected truth, operator packets, and explanation packs remain driven by the shipped baseline only
- The phase should make the negative result first-class:
  - threshold family conclusion = `no_safe_uplift`
  - outcome-rule family conclusion = `no_safe_uplift`
  - dominant bottleneck on the standard cohorts = `structural_cohort_limited`
- The standard artifact bundle and pilot refresh outputs should expose the chosen demo profile, fallback profile, non-adoption reasons, and next-step limitation without inventing new decision semantics.

### Problem statement

- `v2.3` was opened to find safe funnel movement using only existing signals, existing outputs, and existing action space.
- Phase `49` proved bounded threshold-only relaxation does not safely improve `APPROVED + CONDITIONAL` share on the standard cohorts.
- Phase `50` proved bounded offer/readiness-only outcome rules also do not safely improve funnel movement on the same cohorts.
- Phase `51` proved the dominant explanation is not hidden trust regression and not merely a blocked promotion candidate; it is `structural_cohort_limited` under the current bounded signal and action baseline.
- That means the remaining Phase 52 problem is not “which candidate should we promote?” It is:
  - which baseline should demos and pilots carry forward now
  - how should the system prove that choice honestly
  - how should the milestone hand off to the next milestone without overclaiming uplift

### Preferred policy baseline contract

- The preferred demo/pilot baseline should be a new packaging profile, not a new runtime decision family:
  - `preferred_demo_profile = preferred_demo_baseline_v2_3`
- This preferred profile must pin all selected outputs to the shipped live baseline:
  - `decision_policy_version = v2.1_phase_40_5`
  - `policy_version_evaluated = v2.1_phase_40_5`
- The preferred profile must explicitly carry the Phase `49-51` conclusions:
  - `recommended_candidate_status = no_safe_uplift`
  - `recommended_outcome_rule_status = no_safe_uplift`
  - `dominant_movement_bottleneck = structural_cohort_limited` on the standard cohorts unless the current run proves another locked Phase `51` diagnosis without any regression
- The preferred profile should include the full evidence appendix:
  - candidate threshold profiles compared
  - candidate outcome-rule profiles compared
  - movement guardrail summary
  - promotion blocker summary
  - direct comparison against the shipped `v2.2` baseline refresh
- Allowed claims for the preferred profile:
  - the shipped trust baseline remains clean
  - bounded threshold and outcome-rule candidates were evaluated explicitly
  - no bounded candidate safely beat the shipped baseline
  - current standard cohorts are structurally too far from near-term movement under the present bounded signal/action baseline
- Forbidden claims for the preferred profile:
  - any promoted uplift profile exists today
  - approval or conditional yield improved under a newly adopted bounded policy
  - the system solved movement without needing future capability expansion or new cohort strategy

### Fallback policy profile contract

- The fallback profile should also be a packaging profile over the same shipped runtime baseline, not an alternate decision policy:
  - `fallback_demo_profile = trust_first_baseline_v2_3`
- The fallback profile exists for trust-first, risk-first, or comparison-light demo situations where the full candidate appendix would distract from the pilot story.
- The fallback profile must still pin:
  - `decision_policy_version = v2.1_phase_40_5`
  - selected outputs remain unchanged from the shipped live baseline
- Minimum required content for the fallback profile:
  - clean trust posture from the shipped `v2.2` baseline
  - one concise statement that bounded `v2.3` candidates remained `no_safe_uplift`
  - one concise statement that the dominant current limitation is structural cohort composition under the current action/signal envelope
  - current pilot refresh QA and smoke status
- The fallback profile should intentionally suppress deep candidate-by-candidate storytelling while still remaining honest about the absence of promotion.
- The fallback profile must never be presented as a stricter or looser promoted policy; it is a narrower communication mode over the same live baseline.

### Demo-proof package requirements

- Demo proof should explain both selection and non-selection.
- The package must answer four questions directly:
  1. what baseline is currently preferred for demos and pilots?
  2. why were the bounded threshold candidates not adopted?
  3. why were the bounded offer/readiness candidates not adopted?
  4. what is the real next bottleneck after `v2.3`?
- The package should be assembled entirely from existing Phase `49-51` evidence seams rather than freeform narrative:
  - policy recommendation summary
  - outcome-rule recommendation summary
  - movement guardrail summary
  - promotion blocker matrix
  - bottleneck and ceiling breakdowns
  - pilot refresh comparison and artifact QA outputs
- The demo-proof package should separate:
  - operational truth: shipped live baseline
  - analysis truth: evaluated bounded candidates and their non-adoption reasons
  - forward-looking truth: next milestone must address structural movement limits rather than re-running the same bounded candidate families
- Demo proof should include explicit claim discipline:
  - what we can say in demos
  - what we cannot say yet
  - what evidence is comparative versus merely descriptive

### Required outputs and artifacts

- Phase 52 should reuse existing artifacts from Phases `49-51` as required inputs:
  - `calibration/policy_profile_catalog.json`
  - `calibration/policy_recommendation_summary.json`
  - `calibration/outcome_rule_profile_catalog.json`
  - `calibration/outcome_rule_recommendation_summary.json`
  - `calibration/movement_guardrail_summary.json`
  - `calibration/movement_promotion_blockers.csv`
  - `calibration/movement_bottleneck_breakdown.csv`
  - `calibration/movement_ceiling_breakdown.csv`
  - `calibration/movement_guardrail_review.md`
  - `tables/policy_version_comparison.md`
  - `tables/pilot_refresh_summary.md`
  - `tables/artifact_qa_summary.json`
- Phase 52 should add one canonical structured selection artifact to the collection outputs:
  - `calibration/policy_baseline_selection.json`
    - preferred demo profile
    - fallback demo profile
    - runtime policy version
    - baseline selection reason
    - non-promotion truth for threshold and outcome-rule families
    - dominant bottleneck summary
- Phase 52 should add one explicit candidate disposition table:
  - `calibration/policy_candidate_disposition.csv`
    - one row per bounded threshold and outcome-rule profile
    - family
    - profile version
    - recommendation status
    - non-adoption reason
    - movement created flag
    - guardrail-blocked flag
- Phase 52 should add one demo-facing proof document to the pilot refresh outputs:
  - `tables/demo_policy_proof.md`
    - preferred profile
    - fallback profile
    - why the bounded candidates were not adopted
    - current allowed claims
    - current disallowed claims
- Phase 52 should add one milestone handoff note to the pilot refresh outputs:
  - `tables/next_milestone_handoff.md`
    - bottleneck summary
    - why repeating the same bounded families is not the next step
    - what future milestone should investigate instead
- Additive manifest / summary fields should be carried through collection and pilot refresh outputs:
  - `preferred_demo_profile`
  - `fallback_demo_profile`
  - `policy_baseline_selection_reason`
  - `threshold_family_promotion_status`
  - `outcome_rule_family_promotion_status`
  - `next_milestone_focus`

### Acceptance criteria

- The standard collection bundle can regenerate under the preferred demo profile and fallback demo profile labels while keeping selected truth pinned to the shipped live baseline.
- Every bounded threshold and outcome-rule candidate from Phases `49` and `50` has an explicit disposition row explaining why it was not adopted.
- Pilot/demo proof states, without ambiguity:
  - the shipped baseline is still the preferred runtime policy
  - bounded threshold candidates remained `no_safe_uplift`
  - bounded offer/readiness candidates remained `no_safe_uplift`
  - the dominant current limitation is `structural_cohort_limited` on the standard cohorts unless rerun evidence says otherwise
- Pilot refresh summaries and manifests surface the preferred profile, fallback profile, and selection reason.
- Artifact QA fails or degrades when the new Phase 52 proof artifacts or manifest fields are missing or inconsistent.
- Phase 52 closes `POL-01` and `POL-02` honestly even if the preferred and fallback profiles share one runtime policy owner, because the contract difference is packaging posture and claim depth, not hidden decision-rule drift.

### Recommended implementation order

1. Extend [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) with one canonical Phase 52 baseline-selection helper that consumes the locked Phase `49-51` summaries and emits:
   - `policy_baseline_selection.json` payload
   - candidate disposition rows
   - preferred/fallback demo profile labels
2. Extend [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) to write the new selection and disposition artifacts, add the new manifest fields, and include a short baseline-selection section in the collection summary.
3. Extend [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) to render:
   - `demo_policy_proof.md`
   - `next_milestone_handoff.md`
   - preferred/fallback profile fields in the refresh manifest and summary
4. Extend [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) so the new Phase 52 artifacts and fields are QA-checked alongside the existing policy/outcome/guardrail metadata.
5. Add regression coverage in:
   - [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
   - [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py)
   - [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py)
   so Phase 52 selection stays deterministic and honest.

### Claude's Discretion

- Exact wording, markdown layout, and section ordering inside the new demo-proof and handoff documents.
- Exact JSON and CSV field ordering as long as the preferred/fallback contracts, non-adoption reasons, and bottleneck story remain deterministic.
- Whether the collection summary and pilot refresh summary expose the new baseline-selection story as dedicated sections or additive bullet summaries, as long as the core Phase 52 truth is not diluted.

</decisions>

<specifics>
## Specific Ideas

- Treat this phase as “honest packaging of a negative optimization result” rather than “find a face-saving pseudo-winner.”
- The preferred profile should feel strong because the trust baseline is clean and the analysis is explicit, not because the milestone manufactures uplift it did not find.
- The fallback profile should be narrower, not different: same live baseline, fewer candidate details, same honesty.
- The next milestone handoff should say clearly that repeating the same bounded threshold and outcome-rule families is unlikely to change the answer without a broader movement lever.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py): already owns the baseline policy mirror, candidate policy catalog, outcome-rule catalog, recommendation summaries, movement guardrail summary, bottleneck selection, and markdown review generation. This is the natural owner for Phase 52 baseline selection and candidate disposition logic.
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already writes all Phase `49-51` calibration artifacts plus collection manifest and summary sections. It is the right place to emit the new Phase 52 structured selection artifacts.
- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py): already writes `policy_version_comparison.*`, `pilot_refresh_summary.md`, `artifact_qa_summary.json`, and `pilot_refresh_manifest.json`. It is the natural seam for the new demo-proof and next-step handoff documents.
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py): already checks policy/outcome/guardrail metadata consistency and should become the Phase 52 gatekeeper for the new proof artifacts.
- [pilot/contracts.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/pilot/contracts.py): typed refresh manifest contract already exists and can be extended if the new preferred/fallback profile fields need first-class manifest typing.

### Established Patterns

- Collection manifests are the canonical place for summary truth that downstream pilot refresh and QA consume.
- Pilot refresh outputs already compare the current refresh to a reference baseline and already carry recommendation and bottleneck summaries, so Phase 52 should extend that path rather than create a second demo packaging runner.
- The repo consistently treats analysis-only candidate truth and live decision truth as separate layers; Phase 52 should keep that separation intact.
- Earlier phases already proved that explicit `no_safe_uplift` is preferable to silent fallback or ambiguous promotion language; Phase 52 should preserve that honesty.

### Integration Points

- Build the Phase 52 baseline-selection payload from the existing Phase `49-51` outputs rather than recomputing candidate movement from raw customer rows.
- Thread the preferred/fallback demo profile fields from collection manifest into pilot refresh manifest and QA summary so every demo-facing artifact agrees on the chosen posture.
- Keep the website and explanation-pack consumers passive; they should read the new package truth from artifacts, not derive Phase 52 policy stories themselves.

</code_context>

<deferred>
## Deferred Ideas

- Expanding action semantics or recommendation families belongs to the next milestone, not Phase `52`.
- Re-opening threshold ladders or outcome-rule ladders with new candidate families belongs to a future milestone only if new leverage exists.
- Any attempt to claim real movement on materially different cohorts or new institution-specific populations belongs after the next milestone defines that scope explicitly.

</deferred>

---

*Phase: 52-preferred-policy-baseline-demo-proof*
*Context gathered: 2026-04-03*
