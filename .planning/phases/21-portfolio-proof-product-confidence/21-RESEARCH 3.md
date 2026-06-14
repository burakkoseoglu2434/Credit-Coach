# Phase 21: Portfolio Proof & Product Confidence - Research

**Researched:** 2026-03-19
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so the post-hardening proof layer can answer, with product-safe honesty, whether the engine is actually working across the full portfolio and not only inside curated demo stories?

## Planning Basis

Phase 21 now has a locked `21-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/17-full-portfolio-evaluation-coverage-audit/17-CONTEXT.md`
- `.planning/phases/18-decision-narrative-product-output-translation/18-CONTEXT.md`
- `.planning/phases/19-behavior-aware-recourse/19-CONTEXT.md`
- `.planning/phases/20-trajectory-hardening/20-CONTEXT.md`
- `.planning/phases/21-portfolio-proof-product-confidence/21-CONTEXT.md`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
- `credit-coach-website/server/services/demo-data.ts`
- `credit-coach-website/shared/demo-schema.ts`
- `credit-coach-website/client/src/pages/ProofPage.tsx`
- `credit-coach/tests/test_portfolio_validation.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_kpi_contract.py`

This is sufficient because the proof stack already exists. The remaining gap is not “how to prove something at all,” but how to refresh that proof after Phase 19 and Phase 20 hardening and expose it in one executive-first contract that product surfaces can consume without reinterpreting engine truth.

## Executive Summary

The repo already has nearly all of the structural seams Phase 21 needs:

- `portfolio_validation.py` already computes the canonical full-cohort proof bundle
- `run_batch_recourse_eval.py` already writes refreshed portfolio proof tables
- `run_phase_experiment_suite.py` already aggregates seed-level proof and milestone evidence
- `kpi_contract.py` already owns release-facing acceptance language
- the website already consumes typed engine artifacts through `demo-data.ts` and `demo-schema.ts`

What is still missing is the proof answer itself:

1. there is no product-facing proof verdict distinct from internal release decision language
2. there is no canonical baseline-aware comparison against the original Phase 17 proof snapshot
3. there is no engine-owned curated proof snapshot that the website can consume as a single proof contract
4. the current proof page still stitches together multiple raw artifacts instead of rendering one executive-first confidence view

Phase 21 should therefore be planned as a focused refresh pass with one clear deliverable:

`portfolio truth -> verdict + confidence + delta + proof page contract`

## Existing Assets We Can Reuse

### Portfolio proof engine seam already exists

- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already emits:
    - coverage funnel
    - reality-gap summary
    - segment story
    - demo representativeness
  - already produces review markdown and machine-readable summary artifacts

This is the correct seam for:

- product-facing proof verdict
- proof confidence label
- headline metric hierarchy
- comparison against Phase 17 baseline proof

### Batch proof regeneration seam already exists

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already re-runs the portfolio and writes `portfolio_validation_summary.json`
  - already emits portfolio-facing tables and review artifacts

This is the right seam for:

- refreshed proof after Phase 19 and 20 hardening
- persisted proof comparison artifacts
- writing a website-facing curated proof snapshot into the run output

### Suite and milestone packaging seams already exist

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates seed-level proof
  - already writes milestone acceptance and release review outputs

This is the right seam for:

- seed-stable proof refresh
- carrying product-facing proof separately from release decision
- emitting the final curated confidence snapshot into the suite run tables

### Release decision seam already exists and should not be overloaded

- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already owns governance-facing acceptance semantics
  - already uses internal language such as:
    - `ACCEPTED`
    - `PILOT_ONLY`
    - `REJECTED`

Phase 21 should preserve this seam and keep product-proof verdicts separate.

### Website artifact-consumer seam already exists

- `credit-coach-website/server/services/demo-data.ts`
  - currently serves multiple proof artifacts separately
- `credit-coach-website/shared/demo-schema.ts`
  - already holds typed contracts for engine-owned demo payloads
- `credit-coach-website/client/src/pages/ProofPage.tsx`
  - already renders a proof surface, but still synthesizes its story from several low-level artifacts

Phase 21 should keep the website as a consumer and move proof synthesis fully back into engine-owned artifacts.

## What Phase 21 Must Deliver

### 1. Product-facing proof verdict contract

Phase 21 must introduce a proof-facing verdict that is separate from internal release decision language.

Locked posture:

- verdict set:
  - `working`
  - `promising`
  - `mixed`
  - `not_proven`
- confidence set:
  - `strong`
  - `moderate`
  - `weak`
- verdict and confidence remain separate

This should live in engine-owned proof artifacts, not website logic.

### 2. Baseline-aware proof comparison

Phase 21 is not a snapshot-only pass. It must compare refreshed proof against the canonical Phase 17 baseline.

The central comparison question is:

- did product credibility improve after behavior-aware and trajectory hardening?

The key delta lenses are:

- `product_ready_plan_coverage`
- weak `4w` exposure
- execution-aware value
- reality-gap pressure

The system must permit honest outcomes such as:

- more honest but narrower

### 3. One curated engine-owned proof snapshot

The website should stop stitching together a proof story from multiple raw artifacts.

Phase 21 should produce one curated, executive-first artifact, recommended as:

- `product_confidence_snapshot.json`

This snapshot should include:

- proof verdict
- proof confidence
- headline metric hierarchy
- delta vs Phase 17
- demo-fit annotation
- supporting trust layer

### 4. Proof-page sync, not website redesign

This phase should only align:

- proof-facing data contract
- proof page consumption

It should not spill into:

- broader product-surface redesign
- investor-page redesign
- analyst workflow redesign

## Recommended Plan Split

### Plan 21-01 — Proof verdict and baseline-aware portfolio refresh

Focus on:

- adding product-facing proof verdict + confidence to canonical proof artifacts
- computing and serializing delta vs Phase 17 baseline
- keeping release semantics separate from product proof semantics

### Plan 21-02 — Suite packaging and curated confidence snapshot

Focus on:

- refreshing suite-level proof outputs after Phase 19 and 20 hardening
- carrying proof verdict and confidence through milestone-facing artifacts
- emitting one curated engine-owned proof snapshot for downstream consumers

### Plan 21-03 — Website proof sync and proof-page consumption

Focus on:

- extending the typed website proof contract
- wiring `demo-data.ts` to the curated proof snapshot
- making `ProofPage.tsx` consume one proof artifact instead of synthesizing from many raw artifacts

## Main Risks

### Risk 1: Proof verdict accidentally drifts into release semantics

If Phase 21 reuses only `ACCEPTED / PILOT_ONLY / REJECTED`, the proof page will speak governance language instead of product language.

Mitigation:

- keep product proof verdict separate
- preserve release decision as an internal governance seam

### Risk 2: Delta comparison becomes too flattering or too noisy

If the comparison posture is underspecified, the phase can either:

- overstate hardening wins
- or fail to explain why a narrower story is actually more credible

Mitigation:

- anchor all comparison to the canonical Phase 17 proof snapshot
- center the delta story on credibility, not only on uplift

### Risk 3: Website keeps inventing proof meaning

If the proof page continues to merge many low-level artifacts itself, engine truth and product truth will drift again.

Mitigation:

- one engine-owned curated proof snapshot
- typed website consumer contract

### Risk 4: Supporting trust layer buries the core verdict

If learning or OPE evidence dominates the proof page, Phase 21 will lose its central answer.

Mitigation:

- keep headline on coverage + safety + execution-aware value
- keep learning confidence as secondary trust support

## Validation Architecture

Phase 21 can be covered with the existing proof and website seams:

- engine proof logic:
  - `credit-coach/tests/test_portfolio_validation.py`
- suite and milestone packaging:
  - `credit-coach/tests/test_phase_experiment_suite.py`
  - `credit-coach/tests/test_kpi_contract.py`
- website proof contract:
  - `cd credit-coach-website && npm run check`
  - `cd credit-coach-website && npm run build`

This is enough to create a Nyquist-compliant validation file because:

- proof verdict and comparison logic are concentrated in a few stable artifacts
- suite aggregation already has regression seams
- the website proof surface is TypeScript-checked and build-verified

## Planner Notes

- Treat Phase 21 as a proof refresh and packaging phase, not a new modeling phase.
- Keep verdict logic and confidence logic engine-side.
- Prefer one curated proof artifact over many page-local joins.
- Keep release acceptance and product proof explicitly separate.
- Use the Phase 17 snapshot as the only canonical comparison baseline for this phase.

