# External Integrations

**Analysis Date:** 2026-03-14

## APIs & External Services

**External APIs:**
- Not detected as a required third-party business API in the core runtime
  - Integration method: most pipelines are local/offline and read configs plus local artifacts
  - Auth: not applicable for the main modeling and recourse flows

**Telemetry Endpoints:**
- Generic Prometheus push-style HTTP endpoint or OTLP-like HTTP endpoint
  - Implementation: `credit-coach/src/credit_coach/ops/telemetry.py`
  - Auth: not built into the client helper; endpoint protection must be handled by the receiver or deployment environment
  - Rate limits: not enforced in code

## Data Storage

**Databases:**
- SQLite by default - product state database from `DB_URL` or fallback `sqlite:///./credit_coach_state.db`
  - Connection: `credit-coach/src/credit_coach/storage/db.py`
  - Client: SQLAlchemy ORM in `credit-coach/src/credit_coach/storage/models.py`
  - Migrations: not detected; tables are created with `Base.metadata.create_all(...)`

**File Storage:**
- Local filesystem - primary artifact store
  - Output root: `credit-coach/artifacts/runs/<run_id>/`
  - Writer: `credit-coach/src/credit_coach/utils/run_context.py`

**Caching:**
- Not detected

## Authentication & Identity

**Auth Provider:**
- Custom bearer-token validation
  - Implementation: `credit-coach/src/credit_coach/api/auth.py`
  - Token sources: `CREDIT_COACH_API_KEYS_JSON`, `CREDIT_COACH_API_TOKENS`, `CREDIT_COACH_API_TOKEN`, or `configs/security.yaml`
  - Session management: token-policy validation only; no OAuth or refresh-token framework

**OAuth Integrations:**
- Not detected

## Monitoring & Observability

**Error Tracking:**
- Not detected as a hosted service such as Sentry

**Analytics:**
- Not detected

**Logs:**
- Python `logging` to stdout/stderr across CLI modules such as `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- Run-specific text logs are written into each artifact directory via `credit-coach/src/credit_coach/utils/run_context.py`

## CI/CD & Deployment

**Hosting:**
- Not detected; repository is oriented around local execution and experiment pipelines

**CI Pipeline:**
- Not detected in the files reviewed

## Environment Configuration

**Development:**
- Required configs live in `credit-coach/configs/`
- Secrets location is environment-variable based plus optional `.env`
- Mock/stub data exists at `credit-coach/data/sample/lending_club_sample_2000.csv`

**Staging:**
- Environment-specific experiment overrides are modeled as YAML files in `credit-coach/configs/experiments/`

**Production:**
- Secrets management appears manual or platform-provided; no dedicated secrets manager client is present
- Release readiness depends on generated artifacts and smoke gates, not on an external control plane

## Webhooks & Callbacks

**Incoming:**
- Not detected

**Outgoing:**
- Telemetry POSTs from `credit-coach/src/credit_coach/ops/telemetry.py`
  - Trigger: monitoring/export workflows
  - Retry logic: not detected

---
*Integration audit: 2026-03-14*
*Update when adding/removing external services*
