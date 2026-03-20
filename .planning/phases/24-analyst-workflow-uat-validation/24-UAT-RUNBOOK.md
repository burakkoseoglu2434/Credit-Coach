---
phase: 24-analyst-workflow-uat-validation
artifact: analyst-uat-runbook
created: 2026-03-20
status: active
requirements:
  - OPS-01
routes:
  - /demo
  - /proof
---

# Phase 24 Analyst Walkthrough Runbook

## Purpose

This runbook explains how to execute the analyst walkthrough against the shipped Demo Center and Proof page.

Use it together with `24-UAT.md`. The matrix defines what must be answered; this runbook defines where to look, what the analyst should say, and what evidence should be captured.

## Run Discipline

- Start in one locale and stay there for the entire run.
- `EN` run: keep the entire walkthrough in English.
- `TR` run: keep the entire walkthrough in Turkish.
- Do not mix `EN` and `TR` strings inside a single recorded session.
- Begin each task from the default page state before opening `Show technical details`.
- Open `Show technical details` only if the analyst cannot complete the task from the default read or wants to confirm caveats.

## Surface Map

| Route | Surface | Primary use |
|-------|---------|-------------|
| `/demo` | Demo Center | Single-customer review, portfolio interpretation, offer assessment, and learning-readiness interpretation |
| `/proof` | Proof page | Proof-confidence review, benchmark framing, and pilot-readiness caveats |

## Task Runbook

### 24-UAT-01 - Single-customer review

- Route: `/demo`
- Surface: Demo Center
- Start section: Customer
- Default read path:
  - `Status`
  - `Expected outcome`
  - `Risk trend`
  - `Customer narrative`
  - `Next decision window`
- Expected analyst answer:
  - the file is in controlled recovery
  - expected outcome is credit-ready in 12 weeks
  - risk trend is decreasing
  - the next decision point is checkpoint-based rather than immediate re-application
- Evidence source:
  - `single-customer-roadmap`
- Technical detail:
  - `Show technical details` should stay optional
  - open only to confirm checkpoint labels, decision status, or generated trace metadata
- Facilitator note prompts:
  - Was the answer produced from the first business view?
  - Did the analyst use business language instead of PD or phase jargon?
  - Was any blocker caused by unclear customer context?

### 24-UAT-02 - Portfolio interpretation

- Route: `/demo`
- Surface: Demo Center
- Start section: Portfolio
- Default read path:
  - `Recovery lift`
  - `Average risk improvement`
  - `First-4-weeks health`
  - `Portfolio narrative`
  - `What this shows`
- Expected analyst answer:
  - the single-customer pattern appears to translate into portfolio movement
  - the current read shows meaningful lift with visible early-checkpoint pressure
  - the story is broader than one good-looking file
- Evidence source:
  - `portfolio-batch-summary`
  - supporting detail from `action-realism`, `behavior-aware`, and `trajectory`
- Technical detail:
  - `Show technical details` should stay optional
  - open only to confirm 12-week or 24-week checkpoint health or supporting signal mix
- Facilitator note prompts:
  - Could the analyst answer from the three headline portfolio metrics?
  - Did context labels make the simulation nature clear?
  - Was the portfolio story credible without reading the technical grid?

### 24-UAT-03 - Offer assessment

- Route: `/demo`
- Surface: Demo Center
- Start section: Offer
- Default read path:
  - `Offer acceptance`
  - `Combined realization`
  - `Expected impact`
  - `Offer narrative`
  - `What this shows`
- Expected analyst answer:
  - institution-side offers are measured inside the same decision surface
  - the offer layer has credible acceptance and realization logic
  - expected impact is positive but still framed as a representative simulation
- Evidence source:
  - `offer-optimization`
  - supporting context from `single-customer-roadmap` when offer timing is referenced
- Technical detail:
  - `Show technical details` should stay optional
  - open only to confirm dominant offer type, safe-offer rate, or impact proxies
- Facilitator note prompts:
  - Did the analyst understand the offer layer as part of the same workflow rather than a separate tool?
  - Was the commercial value legible from the default read?
  - Did any trust concern require technical proxy confirmation?

### 24-UAT-04 - Learning-readiness interpretation

- Route: `/demo`
- Surface: Demo Center
- Start section: Learning
- Default read path:
  - `Decision log completeness`
  - `Outcome coverage`
  - `Learning-ready records`
  - learning narrative panel
  - `What this shows`
- Expected analyst answer:
  - the product captures enough decision and outcome data to support future policy learning
  - learning readiness is real but not universal across the portfolio
  - the learning layer improves trust because the system can compare future policy choices
- Evidence source:
  - `outcome-ingestion`
  - supporting context from `off-policy-evaluation`
- Technical detail:
  - `Show technical details` should stay optional
  - open only to confirm coverage mix, OPE confidence, or preferred policy arm
- Facilitator note prompts:
  - Did the analyst understand why learning matters for future policy improvement?
  - Was the learning story legible without raw OPE language?
  - Did the analyst need technical detail to trust the claim?

### 24-UAT-05 - Proof-confidence review

- Route: `/proof`
- Surface: Proof page
- Start section:
  - Buyer verdict
  - compact trust rail
  - decision read
  - watchlist
- Default read path:
  - buyer verdict label
  - `Safe to pilot`
  - `Controlled rollout`
  - `Institution-ready safeguards`
  - benchmark panel
  - three proof metrics
  - three watchlist metrics
- Expected analyst answer:
  - the system looks safe to pilot, not ready for broad rollout
  - confidence improved relative to the previous benchmark
  - weak first-4-week exposure and representativeness still need watching
- Evidence source:
  - `product-confidence-snapshot`
- Technical detail:
  - `Show technical details` should stay optional
  - open only to confirm demo confidence, long-horizon load, or OPE support detail
- Facilitator note prompts:
  - Did the analyst reach the verdict before opening any technical evidence?
  - Was the watchlist visible enough to support trust?
  - Did the benchmark translation clarify the previous benchmark without exposing internal phase language?

## Evidence Recording Standard

Capture these notes for every task:

- the first sentence the analyst used to answer the task
- whether the answer came from the default read or after `Show technical details`
- which route and section were enough to answer the question
- which artifact slug anchored the answer
- whether the analyst trusted the answer and why
- whether any blocker or ambiguity remained

## Completion Standard

The walkthrough is complete only when:

- all five task IDs from `24-UAT.md` are run
- every task has a default-read observation
- every task records whether `Show technical details` was needed
- every task is tied to at least one current evidence source
- the session ends with one explicit `OPS-01` recommendation
