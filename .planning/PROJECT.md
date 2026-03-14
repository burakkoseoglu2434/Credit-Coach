# Credit Coach

## What This Is

Credit Coach is a credit-risk and recourse platform that moves beyond binary approve/deny decisions. It predicts probability of default, explains model behavior, and generates feasible action plans that can help denied customers reach approval while staying within fairness, reliability, latency, and governance gates.

The project serves two connected goals: an academically credible research core and a production-oriented fintech productization path. The current milestone is focused on turning an already capable brownfield baseline into a fairness-stable, KPI-hardened release system that can survive repeated seeded evaluation.

## Core Value

Generate credit recourse plans that are actionable, safe, and measurably effective enough to improve denied-customer outcomes without breaking governance constraints.

## Current Milestone: v1.1 Fairness Stability & KPI Hardening

**Goal:** Make release decisions stable across repeated seeded runs by hardening fairness diagnostics, KPI contract alignment, trajectory realism, and production evidence.

**Target features:**
- Seed-stable fairness and recourse diagnostics
- Unified KPI contract across smoke, suite, and challenger workflows
- Candidate diversity and short-term trajectory tuning with explainable provenance
- Telemetry-required release evidence and outcome-feedback reporting

## Requirements

### Validated

- ✓ Core PD modeling, calibration, and deterministic backend controls exist in the codebase - v1.0
- ✓ Gate-aligned recourse generation, feasibility controls, and high-risk/trajectory flows exist in the codebase - v1.0
- ✓ Fairness, stress, benchmark, challenger, telemetry, and release-gate workflows exist in the codebase - v1.0
- ✓ Operational runbooks, security controls, and audit-friendly persistence exist in the codebase - v1.0

### Active

- [ ] Stabilize fairness and equalized-odds behavior across repeated seeded evaluations
- [ ] Align smoke, phase-suite, and challenger workflows behind one KPI contract
- [ ] Improve short-term and candidate-diversity signals without breaking governance gates
- [ ] Require telemetry-backed release evidence for production-like decisions
- [ ] Extend release evidence toward outcome-feedback and policy-delta reporting

### Out of Scope

- Mobile-first product expansion - current documentation and code are focused on core decisioning and recourse reliability
- New domain pivots outside credit recourse - existing research, code, and reports are tightly centered on credit approval improvement
- Legal/compliance opinion automation - documents explicitly frame these as engineering and governance patterns, not legal advice
- Major end-user product surfaces - this milestone is focused on stability and governance of the existing brownfield platform

## Context

- The repository already contains a substantial brownfield implementation under `credit-coach/`.
- Legacy documentation describes a 12-week thesis-oriented plan, multiple hardening sprints, recourse redesign work, KPI recovery iterations, and production runbooks.
- The imported `v1.0` baseline was reconstructed from historical planning and execution docs so the project can continue with milestone-style GSD planning.
- The recurring product tension is clear across the imported documents: increase lift and business value while preserving fairness, reliability, latency, and audit gates.
- Several documents indicate release readiness is judged by batch KPI reports, smoke reports, challenger matrices, telemetry exports, and operational runbooks.
- The latest imported reports shift the primary blocker from basic capability coverage to fairness stability, trajectory realism, and KPI contract consistency under repeated seeded runs.
- The documentation set mixes planning, research, implementation reports, onboarding material, and production operations guidance. This migration reorganizes that material into a GSD-compatible planning structure.

## Constraints

- **Governance**: Fairness, reliability, and release gates must remain explicit - product success is not defined by lift alone
- **Performance**: Batch and smoke workflows must stay within p95/p99 latency targets - several imported reports identify tail latency as a key blocker
- **Reproducibility**: KPI decisions must be based on deterministic or well-controlled experiment flows - repeated run comparisons appear throughout the legacy reports
- **Operational Safety**: Telemetry, runbooks, and gate documentation must stay aligned with the codebase - productionization is a first-class goal
- **Brownfield**: Existing implementation patterns and artifacts must be respected - this is not a greenfield reset
- **Milestone Continuity**: Phase numbering continues from imported v1.0 history - current milestone work starts at Phase 8

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GSD `.planning` as the single planning home for this repo | Legacy docs were scattered across repo root and `credit-coach/docs`, making continuity and phase tracking difficult | ✓ Good |
| Preserve legacy source documents under `.planning/` instead of discarding them | The old files contain historical context, evidence, and implementation detail needed for audits and future planning | ✓ Good |
| Treat the repository as a brownfield GSD project | Existing code and reports prove the project is already in active development | ✓ Good |
| Frame current roadmap around KPI stability plus governance compliance | Nearly every imported plan/report evaluates success through both lift and safety gates | ✓ Good |
| Reconstruct phases 1-7 as historical `v1.0` baseline work | This preserves continuity while allowing milestone-based planning to start cleanly at Phase 8 | ✓ Good |
| Open `v1.1 Fairness Stability & KPI Hardening` as the active milestone | Latest imported reports show fairness stability and KPI contract consistency are the main remaining blockers | — Pending |

---
*Last updated: 2026-03-14 after starting milestone v1.1*
