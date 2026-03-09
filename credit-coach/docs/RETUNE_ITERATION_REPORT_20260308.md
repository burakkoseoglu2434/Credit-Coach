# Retune Iteration Report (2026-03-08)

## Amaç
`denied_to_approved_lift` ve özellikle `denied_high_risk_lift` değerlerini artırmak.

## Uygulanan Değişiklikler
Tuning dosyası:
- `configs/recourse.yaml`

Ana değişiklikler:
- Denied/high-risk için gate gevşetme (`min_reliability`, `min_worst_risk_margin`, penalty_scale).
- Denied arama alanı büyütme (`topk`, `max_actions`, horizon/weekly ayarları).
- DiCE kapasitesi artırma (`total_cfs`, `max_actions`, timeout ayarı).
- Search budget ve candidate pool büyütme.

## Çalıştırmalar

### Run A (post-refactor, ilk retune öncesi referans)
- Run ID: `20260308_063014_9ede50_c13432`
- denied_to_approved_lift: `0.0464`
- denied_high_risk_lift: `0.0000`
- dice_success_rate: `0.0260`
- latency_p95_ms: `861.78`
- latency_p99_ms: `8510.22`

### Run B (retune v1)
- Run ID: `20260308_063546_e9584d_540793`
- denied_to_approved_lift: `0.0253`
- denied_high_risk_lift: `0.0000`
- dice_success_rate: `0.0000`
- latency_p95_ms: `2207.72`
- latency_p99_ms: `2668.55`

Not: v1 lift'i düşürdü, bu yüzden ikinci iterasyona geçildi.

### Run C (retune v2 - final)
- Run ID: `20260308_063829_2d920a_c4c731`
- denied_to_approved_lift: `0.2321`
- denied_high_risk_lift: `0.1236`
- dice_success_rate: `0.2370`
- latency_p95_ms: `3362.98`
- latency_p99_ms: `40170.64`

## Delta (Run C vs Run A)
Kaynak dosya:
- `artifacts/runs/20260308_063829_2d920a_c4c731/tables/kpi_delta_vs_20260308_063014_9ede50_c13432.csv`

Önemli farklar:
- denied_to_approved_lift: `+0.1857`
- denied_high_risk_lift: `+0.1236`
- approval_rate_lift: `+0.0440`
- avg_pd_reduction: `+0.0186`
- dice_success_rate: `+0.2110`
- fairness_approval_gap_after: `+0.0067` (kötüleşme)
- fairness_equalized_odds_gap_after: `+0.0706` (kötüleşme)
- latency_p95_ms: `+2501.20 ms` (kötüleşme)
- latency_p99_ms: `+31660.42 ms` (kötüleşme)

## Sonuç
- İş KPI açısından retune başarılı: denied ve high-risk dönüşüm belirgin arttı.
- Operasyonel açıdan retune başarısız: tail latency çok yükseldi.
- Mevcut durum, "lift için agresif ama prod latency için uygunsuz" profildir.

## Sonraki teknik adım (önerilen)
- Bu profili `high_lift_experiment` olarak saklayıp prod profile'a doğrudan almamak.
- Latency'yi toparlamak için DiCE timeout ve quota'yi segment bazlı limitli yeniden ayarlamak (ör: sadece denied-high-risk dilimi).
