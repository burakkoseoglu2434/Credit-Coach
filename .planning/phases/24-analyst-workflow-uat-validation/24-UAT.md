---
phase: 24-analyst-workflow-uat-validation
artifact: analyst-uat-matrix
created: 2026-03-20
status: active
requirements:
  - OPS-01
primary_surfaces:
  - /demo
  - /proof
---

# Phase 24 Analyst UAT Matrix

## Purpose

This matrix defines the milestone-local analyst workflow used to decide whether the current product surfaces are understandable, useful, and trustworthy in representative institution tasks.

The validation target is not general website feedback. The target is whether an analyst can use the shipped Demo Center and Proof surfaces to answer decision-relevant questions without depending on raw engine language.

## Validation Rules

- Start each task from the default business read.
- Use technical detail only when the default path does not fully support the analyst answer.
- Score every task on `understandable`, `useful`, and `trustworthy`.
- Record whether technical detail was required, helpful, or unnecessary.
- Close `OPS-01` only through the explicit gate in this document.

## Representative Tasks

| Task ID | Task | Analyst question | Expected decision output | Primary route | Primary section | Default evidence path | Technical detail expectation |
|---------|------|------------------|--------------------------|---------------|-----------------|-----------------------|------------------------------|
| 24-UAT-01 | Single-customer review | Can the analyst explain what is happening to one declined file and what happens next? | A short read covering status, expected outcome, and risk trend for one file | `/demo` | Customer | `Status`, `Expected outcome`, `Risk trend`, `Customer narrative`, `Next decision window` | Optional |
| 24-UAT-02 | Portfolio interpretation | Can the analyst explain whether the same customer story translates into broader portfolio movement? | A short read covering recovery lift, average risk improvement, and first-4-weeks health | `/demo` | Portfolio | `Recovery lift`, `Average risk improvement`, `First-4-weeks health`, `Portfolio narrative` | Optional |
| 24-UAT-03 | Offer assessment | Can the analyst explain whether the offer layer creates operationally credible institution-side value? | A short read covering offer acceptance, combined realization, and expected impact | `/demo` | Offer | `Offer acceptance`, `Combined realization`, `Expected impact`, `Offer narrative` | Optional |
| 24-UAT-04 | Learning-readiness interpretation | Can the analyst explain whether the same decision flow is ready to support future policy learning? | A short read covering decision log quality, outcome coverage, and learning-ready share | `/demo` | Learning | `Decision log completeness`, `Outcome coverage`, `Learning-ready records`, learning narrative panel | Optional |
| 24-UAT-05 | Proof-confidence review | Can the analyst explain whether the system looks safe enough to pilot and what still needs watching? | A short read covering proof verdict, trust posture, benchmark improvement, and watchlist pressure | `/proof` | Buyer verdict, decision read, watchlist | Buyer verdict, trust rail, benchmark panel, three headline proof metrics, three watchlist metrics | Optional but available |

## Dimension Definitions

### understandable

- `pass`: The analyst can restate the answer in business language after the default read.
- `caution`: The answer is available, but the analyst needs extra cross-checking, translation, or second-pass reading.
- `fail`: The analyst cannot confidently explain the answer without raw implementation language or guesswork.

### useful

- `pass`: The surface helps the analyst produce a decision-relevant next step or interpretation.
- `caution`: The surface gives context, but the next step still requires extra manual reconstruction.
- `fail`: The surface is descriptive only and does not support a practical institution task.

### trustworthy

- `pass`: The surface shows enough caveat structure, provenance, and context to support confidence in the read.
- `caution`: The answer is directionally believable, but the caveat layer or provenance is too thin on the default path.
- `fail`: The answer appears overstated, weakly grounded, or dependent on hidden assumptions.

## Task Rollup Rules

- Task result = `pass` when all three dimensions are `pass`.
- Task result = `caution` when exactly one dimension is `caution` and none are `fail`.
- Task result = `fail` when any dimension is `fail`, or when two or more dimensions are `caution`.

## Evidence Capture Standard

Every task result must capture:

- `Task ID`
- route and section reviewed
- observed analyst answer
- `understandable`
- `useful`
- `trustworthy`
- overall task result
- whether technical detail was required
- blocker or ambiguity note
- evidence reference to the current shipped surface

## OPS-01 Closure Gate

`OPS-01` closes only if all of the following are true:

- all five representative tasks are completed
- zero tasks are `fail`
- at most one task is `caution`
- no blocker remains unresolved at the end of the walkthrough
- the results packet states whether the default read was sufficient for each task

`OPS-01` remains open if any of the following are true:

- one or more core tasks are missing
- one or more tasks are `fail`
- two or more tasks are `caution`
- the analyst answer depends on technical detail across most tasks
- blockers are noted without an explicit follow-up path

## Execution Note

This matrix is intentionally narrow. It validates the current analyst workflow through `/demo` and `/proof`; it does not validate investor storytelling, lead capture, deployment readiness, or institution-specific demo operations. Those remain outside `OPS-01` scope.
