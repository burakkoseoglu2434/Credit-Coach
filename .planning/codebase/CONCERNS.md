# Codebase Concerns

**Analysis Date:** 2026-03-14

## Tech Debt

**Oversized CLI orchestration in `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`:**
- Issue: one file contains more than 4,300 lines of orchestration, helper logic, KPI aggregation, and tuning behavior
- Why: experimentation and production hardening accumulated in a single command path
- Impact: high change risk, difficult onboarding, and weak isolation for future refactors
- Fix approach: split candidate generation, metric summarization, fairness accounting, and artifact writing into dedicated modules with focused tests

**Config sprawl in `credit-coach/configs/experiments/`:**
- Issue: dozens of experiment YAML files encode critical behavior differences
- Why: rapid tuning cycles favored cloning configs instead of introducing stronger composition or naming discipline
- Impact: hard to know which variants are authoritative, easy to compare the wrong baseline
- Fix approach: define canonical experiment families, archive obsolete variants, and add a manifest describing intended usage

**Schema and persistence drift risk:**
- Issue: Pydantic contracts in `credit-coach/src/credit_coach/data/schema.py` and ORM persistence in `credit-coach/src/credit_coach/storage/` evolve independently
- Why: there is no migration framework or explicit schema-version layer
- Impact: persisted rows can lag behind richer in-memory plan fields
- Fix approach: add migration/version tracking and tests that assert parity between persisted and domain-critical fields

## Known Bugs

**GSD helper tooling is partially broken in this repo:**
- Symptoms: `node ./.codex/get-shit-done/bin/gsd-tools.cjs init map-codebase` fails with `Cannot find module './lib/core.cjs'`
- Trigger: invoking GSD helper binaries from `.codex/get-shit-done/bin/`
- Workaround: run the workflow manually for now
- Root cause: local installed GSD bundle appears incomplete or has broken relative imports

## Security Considerations

**Optional insecure API mode in `credit-coach/src/credit_coach/api/auth.py`:**
- Risk: setting `CREDIT_COACH_ALLOW_INSECURE_API=1` bypasses configured token requirements
- Current mitigation: explicit opt-in flag plus config support
- Recommendations: guard this behind a development-only environment check or fail hard outside local/demo contexts

**Telemetry export has no built-in auth layer:**
- Risk: pushed metrics may leak to unintended endpoints or fail silently at insecure destinations
- Current mitigation: caller chooses endpoint and mode
- Recommendations: support auth headers or signed requests, and validate allowed destinations in config

## Performance Bottlenecks

**Batch recourse evaluation path:**
- Problem: `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py` combines expensive generation, fairness, and reporting in one pipeline
- Measurement: imported historical reports repeatedly mention p95/p99 latency as a release blocker
- Cause: large candidate search space, DiCE interaction, and heavy summary generation
- Improvement path: reduce hot-path work, isolate slow branches, and benchmark helper modules independently

**DiCE and candidate generation path:**
- Problem: `credit-coach/src/credit_coach/recourse/dice_baseline.py` and `credit-coach/src/credit_coach/recourse/generator.py` sit on the critical path for large batch runs
- Measurement: these modules are repeatedly referenced in imported latency-hardening reports
- Cause: fallback attempts, search breadth, and feasibility filtering
- Improvement path: strengthen early pruning and keep experiment-only branches out of default production paths

## Fragile Areas

**Smoke gate contract in `credit-coach/src/credit_coach/cli/run_production_smoke.py`:**
- Why fragile: GO/FAIL status depends on many artifact schemas lining up correctly
- Common failures: missing columns, stale artifact assumptions, threshold drift
- Safe modification: change gates only alongside tests such as `credit-coach/tests/test_production_smoke.py`
- Test coverage: present, but contract breadth keeps this area high-risk

**Persistence and audit chain in `credit-coach/src/credit_coach/storage/repository.py`:**
- Why fragile: writes append audit-chain hashes as a side effect of repository operations
- Common failures: partial field additions, mismatched payload assumptions, DB-specific behavior changes
- Safe modification: keep repository and audit tests in sync when adding persisted fields
- Test coverage: present for audit-related flows, but schema growth increases risk

## Scaling Limits

**Single-process batch execution:**
- Current capacity: suited for local or limited parallel execution via CLI flags such as `--n_workers`
- Limit: very large batch sizes or repeated challenger matrices will push CPU time and artifact volume sharply upward
- Symptoms at limit: high p95/p99 latency and long end-to-end run duration
- Scaling path: isolate workers, persist intermediate artifacts, and split evaluation/reporting from generation

## Dependencies at Risk

**XGBoost as optional backend:**
- Risk: execution is intentionally disabled by policy unless explicitly allowed
- Impact: behavior can silently fall back to logistic regression if environments are not prepared
- Migration plan: make backend choice explicit in reports and deployment checks, or standardize one supported production backend

**DiCE integration:**
- Risk: counterfactual generation libraries are often version-sensitive and runtime-heavy
- Impact: fallback frequency and latency can change after dependency upgrades
- Migration plan: pin validated versions and keep adapter behavior heavily tested

## Test Coverage Gaps

**Streamlit demo path:**
- What's not tested: `credit-coach/src/credit_coach/app/streamlit_app.py` and related UI helpers were not represented in the reviewed tests
- Risk: local demo regressions may go unnoticed
- Priority: Medium
- Difficulty to test: moderate; needs UI-level or smoke-style checks

**Migration/schema evolution path:**
- What's not tested: no formal migration workflow was detected for storage schema changes
- Risk: historical DB compatibility can break quietly
- Priority: High
- Difficulty to test: moderate; needs versioned fixture databases

---
*Concerns audit: 2026-03-14*
*Update as issues are fixed or new ones discovered*
