# Phase 17: Full Portfolio Evaluation & Coverage Audit - Research

**Researched:** 2026-03-18
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can be run across the full evaluation population and answer not only whether plans are generated, but whether they are realistic, governance-safe, execution-aware, offer-capable, product-ready, and representative of what the website demo currently claims?

## Planning Basis

Phase 17 does not yet have a locked `17-CONTEXT.md`. For this planning pass, the authoritative sources are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/milestones/v1.2-ROADMAP.md`
- `.planning/milestones/v1.2-REQUIREMENTS.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/CONCERNS.md`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
- `credit-coach/tests/test_recourse_funnel_kpis.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach-website/server/services/demo-data.ts`

This is sufficient because Phase 17 is not a new modeling phase. The `v1.2` engine is already the inherited baseline. The remaining question is how to validate that baseline across the whole portfolio and quantify the gap between curated product stories and full-cohort truth.

## Phase 17 Must Answer Four Questions

Phase 17 should be framed around four hard questions rather than a generic “coverage audit”:

1. **Coverage**
   - Across the full evaluation population, how many customers receive any meaningful plan at all?

2. **Reality and governance**
   - Of the plans that exist, how many are realistic, feasible, execution-aware, and governance-safe rather than merely mathematically convenient?

3. **Demo versus full-cohort truth**
   - Does the success shown in curated demo stories hold across the portfolio, or is the website telling a narrow best-case story?

4. **Product usability**
   - Are outputs clean enough to be shown to analysts and buyers, or are they still too engine-native to count as product-ready?

That framing makes Phase 17 a combined:

- full-population evaluation phase
- coverage taxonomy phase
- reality-gap audit phase
- demo-representativeness phase

## Executive Summary

The repository already has most of the mechanics needed for Phase 17:

- `run_batch_recourse_eval.py` already evaluates many customers and emits candidate-quality, behavior-aware, trajectory, and offer summaries
- row-level context such as `risk_band`, `income_band`, and `stress_band` already exists
- `run_phase_experiment_suite.py` already mirrors many seeded artifacts and segment rollups
- the website already consumes curated snapshots and live-demo fallbacks

But the current proof surface is still too fragmented and too easy to overread.

Today the repo can show:

- denied uplift
- trajectory checkpoint metrics
- offer metrics
- behavior-aware metrics

But it cannot yet answer the Phase 17 questions in one coherent way because it lacks:

1. **A full-cohort proof contract**
   - there is no single canonical artifact that says what happened across the entire evaluation population

2. **A useful coverage taxonomy**
   - “plan exists” is not enough; Phase 17 must distinguish raw coverage from usable coverage

3. **A reality-gap audit**
   - the system can still emit plans that look mathematically strong but are too technical, too idealized, or too weakly grounded for product use

4. **A demo representativeness check**
   - the website can tell a clean story, but the engine does not yet quantify whether that story is typical, optimistic, or narrow

5. **A product-ready output lens**
   - the engine can produce a plan without producing something clean enough for analyst or enterprise-buyer consumption

## The Key Phase 17 Insight

Phase 17 should treat full-dataset execution as a **proof standard**, not a convenience.

The center of gravity is:

- not “did we get many runs?”
- but “when we run all customers through the engine, what fraction of outputs are actually meaningful, realistic, safe, and presentable?”

This means full evaluation of the complete available population is mandatory for the phase narrative.

Curated demo cases become supporting stories only after full-cohort behavior is measured.

## Coverage Must Be Split Into Four Layers

Phase 17 should not let coverage collapse into one number.

The phase must distinguish:

### 1. Raw coverage

- how many customers got at least one candidate plan

### 2. Valid coverage

- how many customers got at least one feasible, rankable, non-placeholder plan

### 3. Governance-safe coverage

- how many customers got a plan that remains acceptable under fairness, reliability, trajectory, and related inherited controls

### 4. Product-ready coverage

- how many customers got a plan clean enough to surface in the product without exposing engine-native awkwardness

Without this split, the phase would risk overstating usefulness by counting weak, unrealistic, provisional, or narratively unusable plans as success.

## Reality Gap Must Be Explicit

The single most important new research axis is the **reality gap audit**.

This should explicitly ask:

- can plans be translated into real borrower actions?
- are the recommended changes financially plausible?
- are early checkpoint outcomes consistent with long-horizon promises?
- are some plans producing suspiciously large PD drops from very small technical edits?
- are no-offer plans being idealized relative to how real institutions would intervene?

That means Phase 17 needs explicit signals such as:

- unrealistic PD-drop flags
- repaired or provisional exposure
- reality-gap flag rate
- product-ready output rate

## Segment Analysis Must Produce Product Strategy

Segment analysis should not be treated as a passive slice report.

It should explain:

- where the engine works well
- where it does not
- where offer logic matters
- where behavior-aware logic changes the story
- where demo cases might overstate performance

Canonical segment dimensions should include:

- `risk_band`
- `income_band` or `income_quantile`
- `stress_band`
- recoverability slice such as `denied`, `approved_like`, or `recoverable`
- `offer_needed` vs `no_offer_needed`
- short-term healthy vs long-horizon-only trajectory classes

The final two dimensions are especially important because they move the phase from pure diagnostics into product and strategy insight.

## Offer Diagnostics Must Be First-Class

Offer logic already exists from Phase 15, but Phase 17 must prove whether it matters at portfolio scale.

That means separate offer diagnostics are required:

- `offer_plan_rate`
- `rankable_offer_rate`
- offer acceptance distribution
- combined realization distribution
- governance-safe offer rate
- dominant offer type by segment

Otherwise overall plan coverage can look strong while the offer layer is quietly weak or underused.

## Behavior-Aware Must Be Compared Against Nominal

Phase 17 should not merely carry forward behavior-aware metrics. It must show whether behavior-aware ranking materially changes portfolio quality.

That means explicit comparison between:

- nominal expected improvement
- execution-weighted expected improvement

The phase should also quantify:

- where behavior-aware ranking demotes nominally strong but weakly executable plans
- whether behavior-aware logic lowers superficial lift but improves realism and usability

## Trajectory Health Needs Cohort-Level Classes

The existing 4w / 12w / 24w checkpoints are useful, but Phase 17 should summarize them into stable cohort-level classes.

Recommended trajectory classes:

- `early_healthy`
- `delayed_only`
- `unstable`
- `long_horizon_heavy`
- `replan_prone`

These classes will make later product and narrative phases much easier.

## Demo Cases Must Be Audited For Representativeness

One of the most important outputs of Phase 17 should be a concrete answer to:

**Is the current demo customer representative or unusually favorable?**

That implies specific proof questions:

- which segment does the demo case belong to?
- how large is that segment in the total population?
- how far are demo metrics from cohort averages?
- is the demo a representative story, an optimistic story, or a narrow edge case?

This should become an explicit audit output rather than an informal judgment.

## Recommended Metric Families

Phase 17 should organize its proof around these metric families.

### Coverage

- `raw_plan_coverage`
- `valid_plan_coverage`
- `governance_safe_plan_coverage`
- `product_ready_plan_coverage`

### Feasibility and realism

- `infeasible_plan_rate`
- `repaired_plan_rate`
- `provisional_plan_rate`
- `unrealistic_pd_drop_rate`
- `reality_gap_flag_rate`

### Behavior-aware

- `mean_plan_execution_probability`
- `execution_weighted_expected_improvement`
- `mixed_execution_exposure`
- `failed_execution_exposure`

### Offer

- `offer_plan_rate`
- `rankable_offer_rate`
- `governance_safe_offer_rate`
- `combined_realization_rate`

### Trajectory

- `early_checkpoint_health_rate`
- `delayed_only_rate`
- `long_horizon_heavy_rate`
- `replan_risk_rate`

### Segment proof

- by risk
- by income
- by stress
- by offer-needed segment
- by recoverability segment

### Demo/proof fit

- `representative_demo_gap`
- `demo_case_segment_share`
- `cohort_vs_demo_delta`

## Recommended Artifact Contract

The likely Phase 17 artifact family should look like:

- `portfolio_validation_summary.json`
- `portfolio_coverage_breakdown.csv`
- `portfolio_reality_gap_breakdown.csv`
- `portfolio_segment_breakdown.csv`
- `portfolio_offer_breakdown.csv`
- `portfolio_trajectory_class_breakdown.csv`
- `demo_representativeness_breakdown.csv`
- `portfolio_validation_review.md`

The exact filenames can be refined during execution, but the contract should preserve the distinction between:

- machine-readable canonical truth
- supporting breakdown tables
- executive proof review

## Brownfield Seams To Reuse

### 1. `run_batch_recourse_eval.py` remains the population runner

Phase 17 should not create a second orchestration path. It should extract full-cohort validation on top of the existing batch runner.

### 2. Existing segment fields should remain canonical

The code already carries `risk_band`, `income_band`, `stress_band`, and canonical segment keys. Phase 17 should reuse these rather than minting a parallel taxonomy.

### 3. `run_phase_experiment_suite.py` should mirror, not redefine

Seeded suite outputs should reflect the new portfolio-proof contract, not independently reinvent it.

### 4. Website proof remains downstream

The website is a consumer of curated snapshots and proof artifacts. Phase 17 should produce the evidence layer that later website phases can safely sync.

## Recommended Plan Structure

### Plan 17-01

Create the canonical full-population runner outputs:

- full-dataset evaluation
- coverage taxonomy
- reality-gap and product-ready base diagnostics

### Plan 17-02

Add strategic slice diagnostics:

- segment rollups
- offer diagnostics
- behavior-aware vs nominal comparison
- trajectory class summaries

### Plan 17-03

Publish the executive proof layer:

- full-cohort review
- demo representativeness audit
- explicit separation of curated story and portfolio truth

## Final Research Conclusion

Phase 17 should be planned as:

> Run the engine across the full evaluation population and determine not only whether plans can be generated, but whether they are realistic, governance-safe, execution-aware, offer-capable, and product-ready across representative segments. The phase must also quantify the gap between curated demo stories and full-cohort behavior.

That framing is stronger than a simple coverage audit and better matches the real gap between the current engine and the current product surface.
