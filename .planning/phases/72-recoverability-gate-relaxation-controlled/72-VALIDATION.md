---
phase: 72
slug: 72-recoverability-gate-relaxation-controlled
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 72 — Validation Strategy

> Validation contract for a controlled policy unlock (`assisted_full`) that must preserve trust counters at zero and remain W2a-comparable.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + artifact checks |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q` |
| **Full suite command** | `cd credit-coach && PYTHONPATH=src python3 -m pytest -q` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Run Quick run command
- **After every plan wave:** Run Full suite command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 72-01-01 | 01 | 1 | GATE-01,GATE-03 | compile | `cd credit-coach && PYTHONPATH=src python3 -m compileall -q src` | ✅ | ⬜ pending |
| 72-01-02 | 01 | 1 | GATE-01,GATE-02 | smoke | `cd credit-coach && PYTHONPATH=src python3 -m compileall -q src && PYTHONPATH=src python3 -c "from credit_coach.cli.run_recourse import _apply_recourse_gate_to_roadmap; r={'summary':{'recourse_mode':'limited','recommendation_mode':'informational','recoverable_flag':False,'assisted_full_flag':1,'selected_path_type':'customer_only','best_plan_id':'p1','selection_outcome':'ok','decision_status':'REJECTED','threshold_reach_probability':0.3,'approval_gap':0.2,'best_possible_pd_improvement':0.05,'gap_closure_rate':0.25},'narrative':{'steps':[{'action_key':'adjust_requested_loan_amount','requires_institutional_approval':False,'requires_acceptance':False,'primary_recommendation':{'en':'Lower requested amount','tr':'Lower requested amount'}}]},'phases':[{'phase_id':'phase_1','steps':[{'action_key':'adjust_requested_loan_amount','requires_institutional_approval':False,'requires_acceptance':False}]}]}; out=_apply_recourse_gate_to_roadmap(r); s=out.get('summary',{}); assert s.get('recourse_mode') in {'assisted_full','limited'}, s; print('ok', s.get('recourse_mode'))"` | ✅ | ⬜ pending |
| 72-01-03 | 01 | 1 | GATE-03 | regression | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 72-01-04 | 01 | 1 | GATE-02,GATE-03 | unit | `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q` | ❌ W0 | ⬜ pending |
| 72-02-01 | 02 | 2 | GATE-01 | compile | `cd credit-coach && PYTHONPATH=src python3 -m compileall -q src` | ❌ W0 | ⬜ pending |
| 72-02-02 | 02 | 2 | TRUST-01..03 | integration | `cd credit-coach && ls artifacts/evaluations/v27_w2a_control_eval_*_full_processed_n3000_seed42/cohort_metrics.json >/dev/null && ls artifacts/evaluations/v27_w2a_assisted_full_eval_*_full_processed_n3000_seed42/cohort_metrics.json >/dev/null && python3 -c \"import glob,json; p=glob.glob('artifacts/evaluations/v27_w2a_assisted_full_eval_*_full_processed_n3000_seed42/cohort_metrics.json'); assert p, 'missing intervention cohort_metrics.json'; d=json.load(open(p[0],'r',encoding='utf-8')); m=d.get('population_metrics',{}).get('global_denied',{}); assert int(m.get('selected_invalid_winner_count',-1))==0, m; assert int(m.get('selected_surface_drift_count',-1))==0, m; assert int(m.get('operator_packet_contradiction_count',-1))==0, m\"` | ❌ W0 | ⬜ pending |
| 72-02-03 | 02 | 2 | GATE-03 | report-check | `test -f .planning/phases/72-recoverability-gate-relaxation-controlled/72-REPORT.md && rg -n \"Rollback\" .planning/phases/72-recoverability-gate-relaxation-controlled/72-REPORT.md >/dev/null` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers Phase 72 foundations:
- `credit-coach/tests/test_cohort_evaluation.py` — end-to-end cohort eval contract

Wave 1 introduces:
- `credit-coach/tests/test_recourse_gate_relaxation.py` — assisted_full routing + pruning tests

---

## Manual-Only Verifications

After Wave 2, do one quick audit scan:
- confirm only one policy intervention was applied (assisted_full tier), and that ranking/selection logic was unchanged (no changes outside gate/surface seam).

---

## Validation Sign-Off

- [ ] All tasks have automated verify or bounded manual checks
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all dependencies
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter when complete

**Approval:** pending
