---
phase: 70
slug: 70-lendingclub-full-dataset-validation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-11
---

# Phase 70 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q` |
| **Full suite command** | `cd credit-coach && PYTHONPATH=src python -m pytest -q` |
| **Estimated runtime** | repo-dependent |

---

## Sampling Rate

- **After any code/config change:** Run `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q`
- **After each wave:** Run `cd credit-coach && PYTHONPATH=src python -m pytest -q`
- **Max feedback latency:** keep quick slice < ~180s when possible

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 70-01-01 | 01 | 1 | LCFULL-01 | compile | `cd credit-coach && PYTHONPATH=src python3 -m compileall -q src` | ✅ | ⬜ pending |
| 70-01-02 | 01 | 1 | LCFULL-02 | integration | `cd credit-coach && test -f data/splits_lendingclub_full/ingest_schema_report.json && python3 -c "import json; p='data/splits_lendingclub_full/ingest_schema_report.json'; d=json.load(open(p,'r',encoding='utf-8')); assert d.get('missing_required_columns', None)==[], d"` | ✅ | ⬜ pending |
| 70-01-03 | 01 | 1 | LCFULL-03 | integration | `cd credit-coach && ls artifacts/evaluations/v26_lendingclub_full_smoke_*/cohort_metrics.json >/dev/null && python3 -c "import glob,json; p=glob.glob('artifacts/evaluations/v26_lendingclub_full_smoke_*/cohort_metrics.json'); assert p; d=json.load(open(p[0],'r',encoding='utf-8')); m=d.get('population_metrics',{}).get('global_denied',{}); assert int(m.get('selected_invalid_winner_count',-1))==0; assert int(m.get('selected_surface_drift_count',-1))==0; assert int(m.get('operator_packet_contradiction_count',-1))==0"` | ✅ | ⬜ pending |
| 70-02-01 | 02 | 2 | LCFULL-03 | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_scale_sweep_summary.py -q` | ✅ | ⬜ pending |
| 70-02-02 | 02 | 2 | LCFULL-03 | integration | `cd credit-coach && ls artifacts/evaluations/v26_lendingclub_full_eval_*_full_processed_n1000_seed42/cohort_metrics.json >/dev/null && ls artifacts/evaluations/v26_lendingclub_full_eval_*_full_processed_n5000_seed42/cohort_metrics.json >/dev/null` | ✅ | ⬜ pending |
| 70-02-03 | 02 | 2 | LCFULL-03 | artifact-check | `cd credit-coach && ls artifacts/evaluations/v26_lendingclub_full_scale_sweep_*/scale_sweep_summary.csv >/dev/null && test -f ../.planning/phases/70-lendingclub-full-dataset-validation/70-02-SUMMARY.md` | ✅ | ⬜ pending |
| 70-03-01 | 03 | 3 | LCFULL-03 | integration | `cd credit-coach && (ls artifacts/evaluations/v26_lendingclub_full_eval_*_full_processed_n20000_seed42/cohort_metrics.json >/dev/null 2>&1 || ls artifacts/evaluations/v26_lendingclub_full_eval_*_full_processed_n50000_seed42/cohort_metrics.json >/dev/null)` | ✅ | ⬜ pending |
| 70-03-02 | 03 | 3 | LCFULL-04 | report-check | `cd credit-coach && test -f ../.planning/phases/70-lendingclub-full-dataset-validation/70-REPORT.md && rg -n '^## Comparison vs Phase 68/69 \\(descriptive\\)$' ../.planning/phases/70-lendingclub-full-dataset-validation/70-REPORT.md && python3 -c "import re, pathlib; report=pathlib.Path('../.planning/phases/70-lendingclub-full-dataset-validation/70-REPORT.md'); t=report.read_text(encoding='utf-8'); m68=re.search(r'^\\\\*\\\\*Phase 68 anchor dir\\\\*\\\\*:\\\\s*`([^`]+)`\\\\s*$', t, flags=re.M); assert m68, 'missing Phase 68 anchor dir'; p68=pathlib.Path(m68.group(1)); assert (p68/'cohort_metrics.json').is_file(), ('Phase 68 anchor dir', str(p68)); m69=re.search(r'^\\\\*\\\\*Phase 69 anchor dir\\\\*\\\\*:\\\\s*`([^`]+)`\\\\s*$', t, flags=re.M); assert m69, 'missing Phase 69 anchor dir'; p69=pathlib.Path(m69.group(1)); assert (p69/'cohort_metrics.json').is_file(), ('Phase 69 anchor dir', str(p69)); print('anchors_ok')"` | ✅ | ⬜ pending |
| 70-03-03 | 03 | 3 | LCFULL-04 | report-guard | `cd credit-coach && test -f ../.planning/phases/70-lendingclub-full-dataset-validation/70-REPORT.md && ! rg -ni 'uplift|proves|guarantee|increases approvals|increased approvals|caused' ../.planning/phases/70-lendingclub-full-dataset-validation/70-REPORT.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers Phase 70 (pytest present; cohort evaluation tests exist).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full dataset is not accidentally committed | n/a | data lives outside git | Confirm raw CSV path is outside repo OR is gitignored; ensure no large files staged |
| Reports contain no causal/uplift language | n/a | report writing is manual | Grep Phase 70 report(s) for banned words: `causal`, `uplift`, `proves`, `guarantee`, `increases approvals` |

---

## Validation Sign-Off

- [ ] All tasks have a `verify` command or are explicitly manual-only
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Feedback latency manageable
- [ ] `nyquist_compliant: true` set in frontmatter when complete

**Approval:** pending
