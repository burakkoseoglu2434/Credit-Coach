# Phase 17: Full Portfolio Evaluation & Coverage Audit - Context

**Gathered:** 2026-03-18
**Status:** Ready for replanning

<domain>
## Phase Boundary

Run the engine across the full evaluation population and establish one canonical full-cohort proof layer that answers not only whether plans are generated, but whether they are realistic, governance-safe, execution-aware, offer-capable, and product-ready. This phase also quantifies the gap between curated demo stories and full-cohort truth. It does not reopen typed actions, behavior-aware ranking, trajectories, offers, or learning-loop mechanics from `v1.2`; it audits and packages them as portfolio proof.

</domain>

<decisions>
## Implementation Decisions

### Coverage Contract
- Canonical headline coverage set is:
  - `raw_plan_coverage`
  - `valid_plan_coverage`
  - `governance_safe_plan_coverage`
  - `product_ready_plan_coverage`
- A strongly preferred companion metric is:
  - `no_plan_rate`
- `valid_plan_coverage` counts a customer only if there is at least one plan that is:
  - non-rejected
  - feasible or repaired-if-safe
  - rankable
  - not provisional-only
  - a real contender rather than a placeholder or degenerate plan
- `product_ready_plan_coverage` counts a plan only if it:
  - has at least one meaningful action
  - is translated into action semantics rather than raw feature output in default view
  - is not provisional-only
  - has no unrealistic-plan flag
  - is not empty or trivial
  - has a coherent checkpoint narrative, at minimum 4w plus 12w
  - carries an explicit offer state:
    - no offer
    - offer
    - requires approval
    - requires acceptance
  - can be shown in business language without raw internal jargon
  - can be placed in the product UI without manual cleanup
- Coverage should be presented as a funnel in this order:
  - raw
  - valid
  - governance-safe
  - product-ready
- Each funnel transition must carry drop-reason breakdowns:
  - raw to valid:
    - infeasible
    - rejected
    - degenerate
  - valid to governance-safe:
    - fairness
    - reliability
    - trajectory instability
  - governance-safe to product-ready:
    - action not interpretable
    - narrative missing
    - offer unclear
    - reality-gap flags

### Reality-Gap Audit
- Reality-gap is canonical in Phase 17 as:
  - audit-first
  - non-blocking
  - explicitly visible in coverage and review
  - indirectly connected to `product_ready`
- Reality-gap is not:
  - a gate
  - a ranking override
  - an automatic reject rule
- Canonical minimal reality-gap flag family is:
  - `unrealistic_pd_drop_flag`
  - `engine_native_action_flag`
  - `trivial_or_degenerate_plan_flag`
  - `narrative_gap_flag`
  - `offer_state_ambiguity_flag`
  - `checkpoint_consistency_flag`
  - `execution_mismatch_flag`
- `unrealistic_pd_drop_flag` should fire only when:
  - PD drop is large
  - action burden is low or trivial
  - checkpoint trajectory does not support the jump
  - and/or the improvement is feature-local but outcome-global
- Large improvement alone must not trigger the flag; only unexplained improvement should.
- Reality-gap review must include:
  - `reality_gap_flag_rate`
  - `dominant_reality_gap_reason`
  - `product_ready_drop_due_to_reality_gap`
  - flag distribution by reason
  - multi-flag exposure
  - severity split:
    - mild
    - moderate
    - severe
  - highest reality-gap segment
  - highest product-ready drop segment
- Product-readiness and reality-gap are explicitly linked:
  - `product_ready = governance_safe AND no critical reality-gap`

### Segment And Trajectory Classes
- Canonical segment axis set is:
  - `risk_band`
  - `income_band`
  - `stress_band`
  - `recoverability_segment`
  - `offer_needed_segment`
- `recoverability_segment` and `offer_needed_segment` are explicitly derived layers, not raw underwriting labels.
- Segment axes should remain orthogonal where possible:
  - risk is not recoverability
  - stress is not offer-needed
- Canonical `recoverability_segment` set is:
  - `approved_like`
  - `recoverable`
  - `hard_to_recover`
- Recoverability must be derived from engine behavior, using signals such as:
  - plan existence
  - execution probability
  - checkpoint success
  - offer necessity
- Segment meanings are:
  - `approved_like`: low intervention needed, strong early checkpoint, near-approval behavior
  - `recoverable`: meaningful actions and sometimes offers can plausibly improve the outcome
  - `hard_to_recover`: low feasibility, high stress, weak plan availability, or only long-horizon low-execution stories
- Canonical trajectory class set is:
  - `early_healthy`
  - `delayed_only`
  - `unstable`
  - `long_horizon_heavy`
  - `replan_prone`
- Each plan must have exactly one primary trajectory class.
- Trajectory meanings are:
  - `early_healthy`: 4w checkpoint is healthy and sustainable
  - `delayed_only`: 4w is weak but 12w and/or 24w become good
  - `unstable`: checkpoint pattern is inconsistent or zig-zag
  - `long_horizon_heavy`: meaningful improvement arrives too late for a strong early story
  - `replan_prone`: plan appears fragile and likely to need replan
- Review output must include:
  - strongest 2 segments
  - weakest 2 segments
  - highest `offer_needed` segment
  - lowest `product_ready` segment
  - `early_healthy` vs `delayed_only` distribution
  - highest `replan_prone` slice
  - long-horizon exposure
  - clear insight lines:
    - where engine works
    - where engine struggles
    - where offer is required
    - where narrative breaks

### Demo Representativeness
- Canonical demo representativeness verdict set is:
  - `representative`
  - `optimistic`
  - `narrow`
  - `misleading`
- Verdict must be rule-based rather than loosely heuristic.
- Canonical decision signals are:
  - `demo_case_segment_share`
  - `cohort_vs_demo_delta`
  - `product_ready_alignment`
- `product_ready_alignment` is the strongest signal in the verdict logic.
- Verdict intent is:
  - `representative`: segment share is meaningful, cohort delta is low, and product-ready behavior aligns
  - `optimistic`: demo is directionally aligned but materially better than cohort reality
  - `narrow`: story may be valid but belongs to a small segment
  - `misleading`: product-ready alignment breaks, direction diverges, or the demo pattern does not exist in the cohort
- Demo should remain a single-customer story, but it must always carry a canonical segment anchor.
- Required demo-fit companion fields are:
  - `demo_case_segment`
  - `segment_size`
  - `segment_product_ready_rate`
  - `segment_offer_dependency`
- Demo fit review block must include:
  - `demo_representativeness_verdict`
  - `demo_case_segment_share`
  - `cohort_vs_demo_delta`
  - `product_ready_alignment`
  - `segment_product_ready_rate`
  - confidence label:
    - strong
    - moderate
    - weak
- Demo-fit narrative should explicitly state one of:
  - demo aligns with cohort
  - demo overstates portfolio reality
  - demo reflects a narrow segment
  - demo is not representative of portfolio behavior

### Claude's Discretion
- Exact threshold values for:
  - product-ready pass/fail
  - critical reality-gap severity
  - representativeness verdict cutoffs
  - segment-share and cohort-delta boundaries
- Exact JSON nesting and CSV layouts as long as the locked canonical fields remain explicit and testable
- Exact wording of executive review copy as long as it remains explanation-first and business-safe

</decisions>

<specifics>
## Specific Ideas

- The user explicitly wants Phase 17 to be more than a “run many cases” phase; it must become a combined coverage, realism, governance, and demo-vs-reality proof phase.
- The user wants one especially strong Phase 17 outcome sentence to become possible:
  - “Model %X müşteriye plan üretiyor ama yalnız %Y’si üründe gösterilebilir.”
- The user wants segment reporting to produce product strategy, not only slice tables.
- The user wants demo representativeness to be measurable enough that a strong-looking website story can be called representative, narrow, optimistic, or misleading.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - current population-scale seam
  - already emits candidate-quality, behavior-aware, trajectory, offer, fairness, and segment-adjacent metrics
  - already carries fields such as `risk_band`, `income_band`, and several checkpoint and offer outputs
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already mirrors seeded summaries and several segment breakdowns
  - is the natural downstream seam for portfolio-proof mirroring
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already renders explanation-first review summaries
  - can later consume Phase 17 executive proof without changing source-of-truth contracts
- `credit-coach-website/server/services/demo-data.ts`
  - already exposes curated and live demo seams
  - is the later consumer for demo representativeness outputs

### Established Patterns
- Canonical truth lives in machine-readable artifacts first; markdown is derived explanation
- Existing portfolio-adjacent metrics are fragmented across:
  - denied uplift
  - execution probability
  - offer coverage
  - trajectory checkpoint health
- Existing segment vocabulary already includes:
  - `risk_band`
  - `income_band`
  - `stress_band`
- Existing trajectory semantics already emphasize:
  - 4w primary checkpoint
  - 12w confirmation
  - 24w stability/upside

### Integration Points
- Phase 17 should likely centralize proof logic in a dedicated evaluation helper, then feed:
  - `run_batch_recourse_eval.py` for full-cohort artifact emission
  - `run_phase_experiment_suite.py` for seeded mirrors
  - later website proof sync through curated demo-data contracts
- Demo representativeness should be computed engine-side, then referenced by the website rather than inferred in frontend code

</code_context>

<deferred>
## Deferred Ideas

- Turning reality-gap from audit-only into a hard gate belongs to a future phase, not Phase 17
- Replacing the single-customer demo with a multi-demo case selector belongs to later website productization, not this phase
- Any new underwriting or model-family expansion remains outside the Phase 17 boundary

</deferred>

---
*Phase: 17-full-portfolio-evaluation-coverage-audit*
*Context gathered: 2026-03-18*
