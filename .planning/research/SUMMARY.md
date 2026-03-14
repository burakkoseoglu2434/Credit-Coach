# Project Research Summary

**Project:** Credit Coach
**Domain:** Brownfield credit recourse system fairness-stability and KPI-hardening milestone
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

Credit Coach already has the ingredients of a production-minded recourse platform: deterministic model controls, gate-aligned recourse generation, trajectory metrics, telemetry export, and release smoke workflows. The imported legacy reports show that the remaining release blocker is no longer basic capability coverage; it is fairness stability and KPI consistency under repeated, production-like evaluation.

The recommended approach for v1.1 is therefore not a stack rewrite. It is a milestone focused on tightening the evidence model: unify the KPI contract across smoke/suite/challenger paths, make fairness failures localizable by segment and source, standardize deterministic experiment freezes, and require telemetry-backed release evidence. Candidate diversity and outcome feedback should be advanced, but only after the stability contract is trustworthy.

## Key Findings

### Recommended Stack

The current Python 3.11 + pandas/NumPy + scikit-learn/XGBoost + SHAP + DiCE-ML stack remains appropriate for this milestone. The likely additions are fairness/governance helpers rather than core runtime replacement. Fairlearn-style group analysis and a controlled benchmark wrapper are the main external patterns worth evaluating.

**Core technologies:**
- Python 3.11+ — main runtime and CLI orchestration foundation
- pandas/NumPy — seeded KPI tables and artifact aggregation
- scikit-learn/XGBoost — deterministic evaluation and production-model comparison
- SHAP/DiCE-ML — explanation and candidate-generation foundations

### Expected Features

The milestone table stakes are seeded fairness stability, unified KPI pass/fail semantics, intersecting fairness diagnostics, deterministic experiment freeze, and telemetry-required production evidence.

**Must have (table stakes):**
- Multi-seed fairness stability suite — users expect release evidence to be repeatable
- Unified KPI contract — prevents smoke/suite/challenger disagreement
- Segment x source diagnostics — makes fairness regressions actionable
- Telemetry-required production profile — prevents “pass without evidence”

**Should have (competitive):**
- Candidate diversity and source-entropy reporting — proves exploration quality
- Short-term fast-track tuning — improves near-term customer actionability
- Outcome-feedback reporting — links offline KPIs to business impact proxies

**Defer (v2+):**
- Operator dashboards and a broader product surface
- Deep regulatory explanation workbench beyond current milestone needs

### Architecture Approach

The milestone should reinforce a shared contract architecture instead of adding more special-case logic to individual CLI scripts. Gate thresholds, seeded aggregation rules, provenance metrics, and release evidence packaging need to become common building blocks that smoke, suite, and challenger workflows all consume consistently.

**Major components:**
1. Shared KPI contract layer — one interpretation of pass/fail semantics
2. Fairness diagnostics layer — segment/source/stress breakdowns beside aggregate KPIs
3. Candidate provenance and short-term tuning layer — explains how plans are produced and why they win
4. Release evidence layer — telemetry, seed summaries, and decision artifacts packaged consistently

### Critical Pitfalls

1. **Lift-first tuning without fairness stability** — always judge release candidates on repeated seeded fairness checks
2. **Contract drift across runners** — centralize thresholds and shared gate-row builders
3. **Invisible candidate diversity problems** — add source-entropy and generator contribution tables
4. **Optional telemetry in production-like decisions** — enforce fail-closed evidence rules

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 8: Fairness Stability Matrix
**Rationale:** Fairness instability is the clearest remaining release blocker.
**Delivers:** Multi-seed fairness summaries, intersecting segment diagnostics, and policy-safe fairness guards.
**Addresses:** FAIR-01, FAIR-02, FAIR-03
**Avoids:** seed-level fairness regressions staying hidden in aggregate reports

### Phase 9: KPI Contract Unification
**Rationale:** Stability work is not trustworthy until smoke, suite, and challenger flows share the same contract.
**Delivers:** Aligned KPI thresholds, deterministic train-once evaluation, and milestone acceptance semantics.
**Uses:** Existing CLI and YAML contract foundation
**Implements:** shared contract/evidence architecture

### Phase 10: Candidate Quality and Trajectory Tuning
**Rationale:** Once the measurement contract is stable, optimize how plans are generated and attributed.
**Delivers:** Candidate diversity metrics, short-term fast-track tuning, and generator/source diagnostics.

### Phase 11: Release Evidence and Outcome Feedback
**Rationale:** Final milestone value comes from reliable release evidence and a path toward business-impact validation.
**Delivers:** Telemetry-required prod profile, reproducible release packets, and outcome-feedback reporting.

### Phase Ordering Rationale

- Fairness stability comes first because it is the main blocker called out by the latest imported reports.
- Contract alignment comes before additional tuning so new optimization work can be measured honestly.
- Candidate and outcome enhancements come after the evidence model is stable enough to trust their impact.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 8:** fairness methodology and post-processing choices can affect actionability and should be checked carefully
- **Phase 10:** candidate diversity benchmarking may need external benchmark/framework validation
- **Phase 11:** outcome-feedback design may need additional domain research before implementation

Phases with standard patterns (skip research-phase if time-constrained):
- **Phase 9:** much of the work is brownfield refactoring and contract alignment inside the existing architecture

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Current stack and dependencies are explicit in the repo and imported docs |
| Features | HIGH | Latest imported reports converge on the same remaining blockers |
| Architecture | HIGH | Brownfield boundaries and hot paths are well understood from codebase map |
| Pitfalls | HIGH | Historical reports already document the failure patterns this milestone must prevent |

**Overall confidence:** HIGH

### Gaps to Address

- Exact fairness toolkit choice should be validated during phase planning if the milestone adopts new external libraries.
- Outcome-feedback requirements need careful scoping so they do not explode the milestone.

## Sources

### Primary (HIGH confidence)
- `.planning/research/legacy/THREE_PILLAR_RESEARCH_TO_IMPLEMENT_PLAN_20260309.md`
- `.planning/archive/legacy-reports/PHASE_TRAJECTORY_GATEFIX_EXECUTION_REPORT_20260310.md`
- `.planning/archive/legacy-reports/CONTINUE_P0_FASTTRACK_EXECUTION_REPORT_20260310.md`
- `.planning/codebase/ARCHITECTURE.md`

### Secondary (MEDIUM confidence)
- `.planning/research/legacy/P0_P1_BACKLOG_RESEARCH_20260308.md`
- `.planning/research/legacy/P0_SPRINT_FIX_PLAN_20260308.md`

### Tertiary (LOW confidence)
- Paper references embedded in the imported legacy reports for DiCE, FACE, LocalFACE, and Fairlearn usage patterns

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*
