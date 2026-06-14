# Phase 24: Analyst Workflow & UAT Validation - Research

**Researched:** 2026-03-20
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must Phase 24 produce so `OPS-01` is closed with milestone-local analyst validation evidence, rather than another vague claim that the current product surfaces "seem understandable"?

## Planning Basis

Phase 24 now has a scoped `24-CONTEXT.md`. For this research pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/v1.3-MILESTONE-AUDIT.md`
- `.planning/phases/22-business-first-demo-center-refactor/22-VERIFICATION.md`
- `.planning/phases/23-proof-investor-narrative-hardening/23-VERIFICATION.md`
- `.planning/phases/24-analyst-workflow-uat-validation/24-CONTEXT.md`
- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
- `credit-coach-website/client/src/pages/ProofPage.tsx`
- `credit-coach-website/client/src/pages/InvestorPage.tsx`
- `credit-coach-website/client/src/data/site-content.ts`
- `credit-coach-website/server/services/demo-data.ts`

This is sufficient because the gap on `OPS-01` is not missing model logic or missing artifact sync. The gap is the absence of a milestone-local validation pack that proves an analyst can use the shipped surfaces to answer representative institution questions.

## Executive Summary

Phase 24 should be validation-first and artifact-first.

It does **not** need a new analyst product surface before planning can proceed. The repo already has the two surfaces an analyst workflow can be grounded in:

- `DemoCenterPage.tsx` for customer, portfolio, offer, and learning interpretation
- `ProofPage.tsx` for trust, benchmark, and pilot-readiness interpretation

The main missing pieces are procedural and evidentiary:

- no representative analyst task matrix
- no runbook telling a reviewer which page or section to use for each task
- no milestone-local scorecard for `understandable`, `useful`, and `trustworthy`
- no results artifact that says whether `OPS-01` actually passed or failed

Phase 24 should therefore stay mostly inside `.planning/` and produce a repeatable validation chain:

1. define the representative analyst tasks
2. define the walkthrough packet tied to shipped product surfaces
3. run and record the walkthrough in one explicit results artifact

## What Phase 24 Is Actually Validating

The requirement is:

- `OPS-01`: Analyst workflow and UAT can validate that outputs are understandable, useful, and trustworthy in representative institution tasks

That means the phase must prove three things together:

1. **Understandable**
   - an analyst can tell what the product is saying
   - the answer does not depend on raw engine vocabulary by default

2. **Useful**
   - the surface helps the analyst make a next-step interpretation
   - the page is not just descriptive; it supports a real institution task

3. **Trustworthy**
   - the analyst can see enough evidence and caveat structure to trust the read
   - technical detail exists when needed, but does not dominate the default path

If the phase only captures impressions such as "looks good" or "reads clearly," it will not close `OPS-01`.

## Core Analyst Surfaces Available Today

### Demo Center is the primary analyst workflow surface

Phase 22 already created the right section structure for analyst tasks:

- customer story
- portfolio impact
- offer layer
- learning readiness

Those four sections map directly to the representative institution tasks already hinted by the roadmap and audit gap.

### Proof is the trust and benchmark companion surface

Phase 23 turned the Proof page into the decision-support layer an analyst would use to answer:

- is this safe enough to pilot?
- what is improving relative to the previous benchmark?
- what still needs watching?

That makes Proof part of the analyst workflow, even though it is not the operational task surface itself.

### Investor should remain secondary for Phase 24

The Investor page is now disciplined and useful, but it is not the core analyst task surface for `OPS-01`.

Research conclusion:

- Demo Center and Proof should be the primary validation targets
- Investor can remain a secondary reference, but Phase 24 should not dilute itself into another narrative review

## Representative Task Set Needed For Closure

The analyst workflow should be defined around five representative tasks:

1. **Single-customer review**
   - Can the analyst explain the customer status, expected outcome, and next decision-relevant step?

2. **Portfolio interpretation**
   - Can the analyst tell whether the customer story translates into broader portfolio movement?

3. **Offer assessment**
   - Can the analyst explain whether the offer layer is commercially meaningful and operationally credible?

4. **Learning-readiness interpretation**
   - Can the analyst tell whether the current trace is strong enough to support future policy learning?

5. **Proof-confidence review**
   - Can the analyst explain why the system is or is not ready for a controlled pilot, including benchmark caveats?

If any of these tasks is missing from the validation pack, `OPS-01` stays under-scoped.

## Recommended Scoring Contract

Phase 24 needs one explicit scoring model so the results artifact can close or fail the requirement cleanly.

Recommended contract:

- Each task is scored on:
  - `understandable`
  - `useful`
  - `trustworthy`
- Each dimension uses:
  - `pass`
  - `caution`
  - `fail`
- Each task also records:
  - evidence reference
  - blocker note
  - whether technical detail was required

Recommended task-level rule:

- `pass` if all three dimensions pass
- `caution` if exactly one dimension is caution and none fail
- `fail` if any dimension fails, or if two or more dimensions are caution

Recommended phase-level rule:

- `OPS-01` passes only if:
  - all five core tasks are completed
  - there are zero failed tasks
  - there is at most one cautioned task
- otherwise:
  - `OPS-01` remains open
  - the results artifact must state the blocking task(s) and next follow-up path

This makes the phase audit-ready rather than narrative-only.

## What Good Phase 24 Artifacts Should Look Like

### 1. One analyst UAT matrix

Needed file:

- `24-UAT.md`

This file should define:

- the five representative tasks
- the scoring rules
- the pass/fail thresholds
- the evidence fields captured per task

### 2. One analyst walkthrough packet

Needed file:

- `24-UAT-RUNBOOK.md`

This file should map each task to:

- current route (`/demo` or `/proof`)
- section or metric area
- expected analyst question
- expected evidence source
- when technical details should or should not be needed

### 3. One analyst results artifact

Needed file:

- `24-UAT-RESULTS.md`

This file should record:

- task-by-task ratings
- blockers
- whether default reading was sufficient
- overall `OPS-01` recommendation

This results doc is the real missing artifact from the audit perspective.

## Recommended Plan Split

### Plan 24-01 - Define the representative analyst task matrix

Focus on:

- creating `24-UAT.md`
- locking task families
- locking the scoring contract
- defining the explicit phase pass/fail gate

This is the phase foundation and should run first.

### Plan 24-02 - Build the milestone-local walkthrough packet

Focus on:

- creating `24-UAT-RUNBOOK.md`
- mapping each analyst task to current shipped product surfaces
- tying the walkthrough to Demo Center and Proof sections plus demo-data artifacts

This keeps execution from drifting into abstract feedback gathering.

### Plan 24-03 - Capture analyst walkthrough results and closure recommendation

Focus on:

- creating `24-UAT-RESULTS.md`
- recording task-by-task outcomes
- explicitly recommending pass or fail for `OPS-01`
- documenting blockers if the requirement still cannot close

This is the artifact that converts validation into milestone evidence.

## Main Risks

### Risk 1: The phase gathers feedback, but not closure evidence

If the work results only in notes or impressions, the milestone audit will still fail.

Mitigation:

- require one results artifact with an explicit `OPS-01` recommendation
- use a fixed score contract

### Risk 2: The task set drifts into buyer or investor storytelling

If Phase 24 spends too much time validating the Investor page, it will blur the analyst workflow objective.

Mitigation:

- treat Demo Center and Proof as the primary analyst workflow
- keep Investor as optional secondary context only

### Risk 3: No explicit pass/fail threshold exists

Without a closure rule, the phase can always be described as "mixed" and never actually close the requirement.

Mitigation:

- define task-level and phase-level thresholds up front in `24-UAT.md`

### Risk 4: Technical detail is either overused or ignored

If the walkthrough allows every answer to depend on technical reveals, the default product surface is not actually validated. If it forbids technical reveals entirely, trust may be under-measured.

Mitigation:

- record whether technical detail was required
- treat "default read insufficient" as a valid caution signal

## Validation Architecture

Phase 24 is best validated through a hybrid contract:

- docs integrity checks for the new analyst artifacts
- website `check` and `build` guards to confirm the current reviewed surfaces still render cleanly
- manual milestone-local walkthrough checks for task completion quality

This means Phase 24 does not need new automated product tests to be Nyquist-compliant. It needs a strong artifact chain plus explicit manual-review gates.
