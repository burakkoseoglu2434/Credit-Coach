# Architecture Research

**Domain:** Brownfield credit recourse system fairness-stability and KPI-hardening milestone
**Researched:** 2026-03-14
**Confidence:** HIGH

## Standard Architecture

### System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                 CLI / Experiment Entry Points               │
├─────────────────────────────────────────────────────────────┤
│  run_batch_recourse_eval  run_phase_experiment_suite        │
│  run_model_challenger_matrix  run_production_smoke          │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│           Shared KPI Contract + Evaluation Layer            │
├─────────────────────────────────────────────────────────────┤
│ fairness metrics │ trajectory gates │ artifact aggregators  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│       Recourse / Planner / Candidate Provenance Layer       │
├─────────────────────────────────────────────────────────────┤
│ planner objective │ generator mix │ source diagnostics      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│          Storage + Artifacts + Telemetry Evidence           │
│   SQLite/audit chain │ artifacts/runs │ telemetry export    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| KPI contract layer | Define one source of truth for thresholds and pass/fail semantics | Shared helpers plus YAML contract file and common row builders |
| Experiment harness | Freeze model state, run seeded suites, and aggregate evidence | CLI orchestration with reusable helper functions and artifact manifests |
| Fairness diagnostics layer | Break regressions down by group, source, and stress context | Evaluation functions that return both summary and per-segment tables |
| Candidate provenance layer | Track which generator/policy path produced each candidate | Row-level source annotations inside batch and benchmark outputs |
| Evidence pack layer | Publish release-ready telemetry, summaries, and decision artifacts | Artifact directory conventions plus JSON/CSV summaries |

## Recommended Project Structure

```text
credit-coach/src/credit_coach/
├── cli/                 # Orchestration entry points
├── evaluation/          # Shared fairness, KPI, and summary builders
├── recourse/            # Candidate generation and source attribution
├── coaching/            # Planner objectives and short-term policy logic
├── ops/                 # Telemetry, KPI contract, release evidence
├── storage/             # Audit state and persistence
└── utils/               # Run context, hashing, shared helpers
```

### Structure Rationale

- **`evaluation/`:** milestone work should move more contract logic into reusable evaluation helpers instead of leaving it only in CLI modules.
- **`ops/`:** telemetry enforcement and release-evidence concerns belong here, not scattered across batch and smoke scripts.
- **`recourse/` and `coaching/`:** candidate diversity and short-term tuning should remain close to generation logic, but expose stable metrics outward.

## Architectural Patterns

### Pattern 1: Shared Contract, Multiple Consumers

**What:** One KPI contract is read by smoke, suite, and challenger workflows.
**When to use:** Any threshold or gate whose meaning must match across pipelines.
**Trade-offs:** Slightly more abstraction up front, much lower risk of contract drift later.

### Pattern 2: Deterministic Suite Wrapper

**What:** Train once, freeze the model snapshot, then run multiple seeded evaluations against the same state.
**When to use:** Comparative fairness or release acceptance testing.
**Trade-offs:** Additional orchestration complexity, but dramatically better interpretability.

### Pattern 3: Diagnostic Outputs Beside Aggregate Outputs

**What:** Every aggregate KPI report is paired with breakdown tables by segment, source, or phase.
**When to use:** Any time the project might pass average metrics while hiding failure concentration.
**Trade-offs:** More artifacts to manage, but far better debuggability.

## Data Flow

### Request Flow

```text
Experiment config
    ↓
CLI entry point
    ↓
Load model + freeze state
    ↓
Generate / score / validate candidates
    ↓
Aggregate KPI + fairness + trajectory tables
    ↓
Run shared gate checks
    ↓
Write release evidence + telemetry payload
```

### Key Data Flows

1. **Seeded evaluation flow:** config → frozen training state → repeated batch/challenger runs → aggregate seed summary.
2. **Release evidence flow:** batch + fairness + telemetry + trajectory summaries → smoke gate rows → GO/NO_GO package.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Local research / 1-5 seeded runs | Current monolithic CLI structure is acceptable |
| Regular 1000x5 milestone validation | Shared helper extraction becomes important to control runtime and debug drift |
| Larger benchmark matrices | Split orchestration from heavy candidate generation and cache intermediate artifacts |

### Scaling Priorities

1. **First bottleneck:** candidate generation breadth and DiCE fallback behavior — reduce hot-path work before adding more metrics.
2. **Second bottleneck:** artifact and contract drift across CLI modules — extract common gate and summary builders.

## Anti-Patterns

### Anti-Pattern 1: Reimplementing the KPI contract per command

**What people do:** Copy thresholds into smoke, suite, and challenger code separately.
**Why it's wrong:** The same run can look GO in one place and NO_GO in another.
**Do this instead:** Keep one contract and one interpretation layer.

### Anti-Pattern 2: Hiding root causes in aggregate summaries

**What people do:** Publish only final fairness or lift aggregates.
**Why it's wrong:** Segment-level or source-level failures stay invisible.
**Do this instead:** Always publish breakdown tables next to the aggregate.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Telemetry receiver | HTTP push or file output from `ops/telemetry.py` | Should become mandatory for production profile gates |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `cli/` ↔ `evaluation/` | Direct function calls | Contract logic should live in shared helpers, not only in CLI code |
| `coaching/` ↔ `recourse/` | Direct function calls and shared plan records | Short-term tuning must preserve provenance and metric compatibility |
| `evaluation/` ↔ `ops/` | Shared summaries and payload builders | Release evidence should be assembled from stable output schemas |

## Sources

- `.planning/research/legacy/THREE_PILLAR_RESEARCH_TO_IMPLEMENT_PLAN_20260309.md`
- `.planning/archive/legacy-reports/PHASE_TRAJECTORY_GATEFIX_EXECUTION_REPORT_20260310.md`
- `.planning/archive/legacy-reports/PHASE_REPLAN_EXECUTION_REPORT_20260309.md`
- `.planning/codebase/ARCHITECTURE.md`

---
*Architecture research for: fairness-stability and KPI-hardening milestone*
*Researched: 2026-03-14*
