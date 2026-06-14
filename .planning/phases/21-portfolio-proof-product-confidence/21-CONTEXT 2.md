# Phase 21: Portfolio Proof & Product Confidence - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Re-run the hardened engine across the full portfolio and convert the result into one refreshed proof layer that answers the product-facing question of whether the system is actually working beyond curated stories. This phase does not reopen recommendation mechanics, trajectory semantics, or website redesign. It refreshes proof after the Phase 19 and Phase 20 hardening passes, compares that refreshed proof against the canonical Phase 17 baseline, and produces one engine-owned proof snapshot that website proof surfaces can consume without inventing their own story.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 17-20
- Phase 17 remains authoritative for portfolio proof structure:
  - canonical coverage funnel
  - reality-gap audit
  - segment story
  - demo representativeness
- Phase 18 remains authoritative for translation and UI contract posture:
  - engine-owned truth
  - website as renderer or typed consumer
  - business-first default language
- Phase 19 remains authoritative for behavior-aware evidence:
  - nominal vs execution-aware value remains a first-class comparison
  - false optimism must be avoided
- Phase 20 remains authoritative for trajectory truth:
  - fixed `4 / 12 / 24` checkpoint horizon
  - weak `4w` health remains a dominant trust signal
  - product and proof horizon closes at `24w`
- Phase 21 is a proof refresh phase, not a new engine-capability phase.

### Proof Verdict Contract
- Product-facing proof verdict must remain separate from internal release decision semantics.
- Release decision continues to live in internal governance language such as:
  - `ACCEPTED`
  - `PILOT_ONLY`
  - `REJECTED`
- Product-facing proof must use a distinct verdict set:
  - `working`
  - `promising`
  - `mixed`
  - `not_proven`
- Proof verdict and proof confidence must remain separate concepts:
  - verdict = product-facing conclusion
  - confidence = how strongly the evidence supports that conclusion
- Canonical proof confidence labels are:
  - `strong`
  - `moderate`
  - `weak`
- `mixed` is the correct proof verdict when:
  - uplift and/or coverage is present
  - but meaningful fractures still remain in:
    - product-ready coverage
    - early-health truth
    - governance-safe proof
    - or reality-gap pressure

### Proof Metric Hierarchy
- The headline proof story should be carried by three first-class metric families:
  - `product_ready_plan_coverage`
  - `governance_safe_plan_coverage`
  - execution-aware value
- The Phase 21 proof surface should therefore center on:
  - coverage
  - safety
  - realistically executable value
- Early-health and trajectory truth must not be buried; they should appear immediately below the headline layer as first-class supporting proof.
- The most important trajectory-supporting signals are:
  - `weak_4w_health_rate`
  - delayed or long-horizon exposure
- Demo representativeness must stay visible on the proof surface, but as a trust annotation rather than a headline KPI.
- Learning and OPE confidence remain valuable, but should stay in a secondary supporting trust layer rather than in the core “is this working?” headline.

### Baseline And Comparison Posture
- Phase 21 must not be snapshot-only; it must explicitly carry delta versus prior proof.
- The canonical comparison baseline is:
  - `Phase 17` portfolio proof snapshot
- The primary review question for Phase 21 is:
  - did product credibility improve after behavior-aware and trajectory hardening?
- The most important comparison dimensions are:
  - product-ready coverage
  - weak-`4w` exposure
  - execution-aware value
  - reality-gap pressure
- Phase 21 must not hide non-improving or narrower outcomes.
- A result such as:
  - more honest but narrower
  is a valid and product-honest outcome for this phase.

### Website-Facing Proof Sync
- Website proof surfaces should not keep assembling many raw artifacts independently.
- Phase 21 should produce one separate curated proof snapshot for the website.
- That proof snapshot must be:
  - engine-side
  - derived from canonical proof artifacts
  - source-of-truth for website proof consumption
- Website remains a typed consumer and must not synthesize its own proof verdict or confidence story.
- The website proof snapshot should be executive-first and include:
  - headline proof verdict
  - headline confidence
  - metric hierarchy
  - delta versus Phase 17
  - demo-fit annotation
  - supporting trust layer
- Phase 21 website scope is intentionally limited to:
  - proof page
  - proof-facing data contract
- Full website redesign remains out of scope for this phase.

### Claude's Discretion
- Exact threshold cutoffs for:
  - `working`
  - `promising`
  - `mixed`
  - `not_proven`
- Exact evidence mapping from proof inputs to:
  - `strong`
  - `moderate`
  - `weak`
- Exact metric names for “execution-aware value” as long as the proof layer keeps nominal upside secondary to realistic execution-aware outcome
- Exact JSON nesting for the website-facing curated proof snapshot as long as:
  - verdict
  - confidence
  - headline metrics
  - Phase 17 delta
  - demo-fit annotation
  - supporting trust layer
  remain explicit and testable

</decisions>

<specifics>
## Specific Ideas

- The user wants Phase 21 to answer the business question:
  - “Bu sistem gerçekten çalışıyor mu?”
- The user explicitly wants proof language to stay separate from release-decision language:
  - internal release verdicts should not leak into product proof
- The user wants Phase 21 to make one especially important question visible:
  - credibility improved mi?
- The user explicitly prefers honest proof over flattering proof:
  - “more honest but narrower” is acceptable
- The user wants demo representativeness to remain visible so the system does not oversell curated stories.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [portfolio_validation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/portfolio_validation.py)
  - already owns canonical portfolio proof structure
  - already emits:
    - coverage funnel
    - reality-gap outputs
    - segment story
    - demo representativeness
  - is the natural seam for Phase 21 verdict and comparison logic
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
  - already performs batch reruns and writes portfolio proof tables
  - is the natural seam for refreshed proof artifact generation after Phase 19 and 20 hardening
- [run_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py)
  - already aggregates seed-level portfolio validation and milestone acceptance outputs
  - is the natural seam for Phase 17 baseline-vs-Phase 21 comparison and milestone-facing proof refresh
- [kpi_contract.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/kpi_contract.py)
  - already contains internal release and confidence semantics
  - should stay the home of governance-facing verdicts while product-proof verdict stays separate
- [demo-data.ts](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/server/services/demo-data.ts)
  - currently serves multiple proof artifacts individually
  - is the natural website seam for switching to one curated proof snapshot artifact
- [ProofPage.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/pages/ProofPage.tsx)
  - currently assembles proof from several raw artifacts
  - should become a consumer of the curated Phase 21 proof snapshot rather than synthesizing proof meaning itself

### Established Patterns
- Engine artifacts are the source of truth; website surfaces consume them through typed mirrors.
- Portfolio proof is already machine-readable first and markdown second.
- Release decision and product-facing story are allowed to diverge if both stay explicit and auditable.
- Hardening phases can narrow the story if they improve truthfulness; evidence does not need to become more flattering to be considered better.

### Integration Points
- Likely Phase 21 engine seams:
  - `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - `credit-coach/src/credit_coach/ops/kpi_contract.py`
- Likely website sync seams:
  - `credit-coach-website/server/services/demo-data.ts`
  - `credit-coach-website/shared/demo-schema.ts`
  - `credit-coach-website/client/src/pages/ProofPage.tsx`

</code_context>

<deferred>
## Deferred Ideas

- Full website redesign or broader buyer-surface rework remains outside this phase.
- Analyst UAT and pilot-readiness work remain outside this phase and belong to later milestone regrouping.
- Any new engine capability beyond proof refresh, proof comparison, and proof-page sync is out of scope here.

</deferred>

---
*Phase: 21-portfolio-proof-product-confidence*
*Context gathered: 2026-03-19*
