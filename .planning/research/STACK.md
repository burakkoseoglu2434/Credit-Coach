# Stack Research

**Domain:** Brownfield credit recourse system fairness-stability and KPI-hardening milestone
**Researched:** 2026-03-14
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Main application runtime | Already powers the full Credit Coach codebase and supports the scientific/CLI stack cleanly |
| pandas + NumPy | 2.1+ / 1.26+ | KPI aggregation, seeded experiment summaries, artifact tables | Existing reports and evaluation flows are tabular and metric-heavy |
| scikit-learn + XGBoost | 1.4+ / 2.x | Deterministic baseline and production model backends | Current code already supports both, and milestone work depends on reproducible backend behavior |
| SHAP + DiCE-ML | 0.45+ / 0.11+ | Explainability and counterfactual candidate generation | Existing recourse and explanation flows already use them; milestone work is about stability and measurement, not replacement |
| SQLAlchemy + SQLite | 2.x / current | State store and audit-chain persistence | Good fit for current brownfield scope and experiment-grade persistence needs |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Fairlearn | Validate compatible release against `scikit-learn>=1.4` | Multi-group fairness metrics, `MetricFrame`, and post-processing baselines | Use when milestone work formalizes intersecting fairness and contract-driven gate checks |
| pyarrow | 14.0+ | Artifact serialization and efficient table interchange | Use when phase-scale seeded reports need stable machine-readable outputs |
| Prometheus / OTLP-compatible endpoints | Receiver-dependent | Telemetry ingestion for release evidence | Use for enforced production-grade monitoring and telemetry-success gates |
| Benchmark harness such as CARLA or an equivalent controlled baseline wrapper | Validate in isolated benchmark environment | Candidate diversity and recourse benchmarking | Use for offline benchmark comparisons rather than hot-path serving |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest | Regression testing | Existing suite already covers smoke, fairness, recourse, telemetry, and auth flows |
| YAML experiment manifests | Config-first experimentation | Keep variants explicit, versioned, and reproducible |
| Seeded batch harnesses | Stability validation | Required for fairness-stability and KPI repeatability claims |

## Installation

```bash
# Core
pip install -e ".[dev]"

# Supporting research additions (validate compatibility before pinning)
pip install fairlearn
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Shared KPI contract in Python/YAML | Per-command hardcoded thresholds | Only acceptable for one-off prototypes, not release-governed evaluation |
| Fairlearn-style group evaluation | Hand-rolled fairness metrics only | Acceptable only when mirroring a specific published metric not covered by existing tooling |
| Controlled benchmark wrapper | Directly swapping production generator dependencies | Use direct integration only after the benchmark proves value and runtime cost is acceptable |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Single-run KPI decisions | Historical reports show seeded instability can hide fairness regressions | Use repeated seeded runs and aggregated acceptance gates |
| Hidden retraining inside every evaluation path | It contaminates comparison and makes root-cause analysis noisy | Use `train_once` / frozen-model evaluation flows |
| Lift-only optimization | It reintroduces fairness, latency, and reliability regressions | Keep lift inside a shared contract with governance gates |

## Stack Patterns by Variant

**If the work is evaluation-only:**
- Reuse the current Python CLI + artifact stack
- Because milestone scope is about measurement, alignment, and stability more than serving architecture change

**If the work adds benchmark frameworks or fairness toolkits:**
- Isolate them behind research or evaluation modules
- Because production hot paths should not take on new heavy dependencies without proven value

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `scikit-learn>=1.4` | current local model/evaluation code | Existing project baseline |
| `xgboost>=2.0` | deterministic backend policy in `model/train.py` | Keep fallback behavior explicit |
| `fairlearn` | validate against current scikit-learn pin before adoption | Add only after compatibility check in milestone work |

## Sources

- `.planning/research/legacy/THREE_PILLAR_RESEARCH_TO_IMPLEMENT_PLAN_20260309.md` — fairness stability, candidate diversity, outcome-loop recommendations
- `.planning/research/legacy/P0_P1_BACKLOG_DEEP_RESEARCH_IMPLEMENTATION_PLAN_20260308.md` — implementation-backed backlog and KPI gates
- `.planning/archive/legacy-reports/PHASE_TRAJECTORY_GATEFIX_EXECUTION_REPORT_20260310.md` — existing contract and trajectory alignment work
- `credit-coach/pyproject.toml` — current project dependency baseline

---
*Stack research for: fairness-stability and KPI-hardening milestone*
*Researched: 2026-03-14*
