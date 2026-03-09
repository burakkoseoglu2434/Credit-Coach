# High-Risk Objective Phase Report (2026-03-08)

## Goal
High-risk denied segment için ayrı objective/policy katmanı eklemek ve KPI ölçümlerini genişletmek.

## Implemented

### 1) Planner: high-risk specific objective (code)
- File: `src/credit_coach/coaching/planner.py`
- `choose_best_plan(...)` artık şu parametreleri destekliyor:
  - `base_pd`
  - `segment_context`
- Yeni high-risk objective yolu eklendi:
  - `denied_objective.high_risk_objective.enabled=true`
  - Sadece `risk_band=high` ve `base_pd>tau` için devreye giriyor.
- High-risk objective içinde eksik gate alanları (`ci/reliability/worst`) konservatif fallback ile cezalandırılıyor.

### 2) Batch KPI genişletmesi
- File: `src/credit_coach/cli/run_batch_recourse_eval.py`
- Yeni row alanları:
  - `best_candidate_pd`
  - `candidate_pd_delta`
  - `high_risk_bridge_hit`
- Yeni summary metrikleri:
  - `denied_high_risk_bridge_count`
  - `denied_high_risk_bridge_rate`
  - `denied_high_risk_any_pd_reduction_count`
  - `denied_high_risk_any_pd_reduction_rate`
  - `denied_high_risk_avg_candidate_pd_reduction`
  - `denied_high_risk_p95_candidate_pd_reduction`
- Yeni tablo:
  - `tables/high_risk_bridge_diagnostics.csv`

### 3) Config updates
- `configs/recourse.yaml`
  - `robust.denied_objective.high_risk_objective` bloğu eklendi (varsayılan: `enabled: false`)
  - `high_risk_bridge_kpi` bloğu eklendi
- `configs/experiments/recourse_phaseb_hybrid_v2.yaml`
  - Aynı bloklar eklendi (stabil baseline için `high_risk_objective.enabled: false` bırakıldı)

### 4) Tests
- `tests/test_planner_denied_objective.py`
  - High-risk objective için 3 ek senaryo:
    - PD improvement tercih testi
    - `denied_mode=False` iken high-risk objective aktivasyonu
    - eksik gate alanları için ceza testi

## Validation Runs

### A) Stabil baseline (GO korunarak)
- Batch (1000): `20260308_150211_fc2b51_99cb87`
  - `denied_to_approved_lift = 0.1097`
  - `denied_high_risk_lift = 0.0`
  - `denied_high_risk_any_pd_reduction_rate = 0.0`
  - `latency_p95 = 200.73 ms`
  - `latency_p99 = 1526.53 ms`
  - `denied_reliability_violation_rate = 0.0284`
- Monitoring: `20260308_150239_6db8cf_387f7b`
- Smoke: `20260308_150246_92147a_54de36` => `GO`

### B) High-risk objective ON denemesi (ara run)
- Batch (1000): `20260308_150119_00ee45_4afd69`
  - `denied_high_risk_lift = 0.0` (değişmedi)
  - `denied_high_risk_any_pd_reduction_rate = 0.0169`
  - Ancak `denied_reliability_violation_rate` ciddi yükseldi (`0.8626`)
- Karar: Bu mod prod baseline'da varsayılan açık bırakılmadı.

## Outcome
- Sistem artık high-risk segmentteki ilerlemeyi sadece "approved'a döndü mü" ile değil, "PD düşüşü var mı" perspektifiyle ölçebiliyor.
- High-risk objective/policy altyapısı kodlandı ancak mevcut veri/model koşullarında prod için güvenli varsayılan olarak kapalı tutuldu.
- GO baseline korunarak faz tamamlandı.
