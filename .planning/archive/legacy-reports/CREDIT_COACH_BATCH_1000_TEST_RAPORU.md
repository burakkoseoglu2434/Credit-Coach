# CREDIT COACH - 1000 MUSTERI BATCH TEST RAPORU

## 0) Kapsam
Bu rapor, 1000 musteri uzerinde otomatik toplu degerlendirme kosusunun sonucunu 3 baslikta sunar:
1. Batch recourse + DiCE basari orani
2. Fairness/stress degisimi
3. Operasyonel sure ve hata analizi

Tarih: `2026-03-07`

---

## 1) Calistirilan Komut

```bash
cd credit-coach && TQDM_DISABLE=1 python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000 --log_every 100
```

Run ID: `20260307_013513_4f12f1_9cba96`  
Toplam sure: `418.60 sn`

---

## 2) Batch Recourse + DiCE Sonuclari

### 2.1 Ozet KPI
1. Islenen musteri: `1000`
2. Hata sayisi: `0` (`error_rate=0.0`)
3. Best plan `APPROVED` orani: `0.752` (752/1000)
4. DiCE basari orani: `1.0` (1000/1000, backend=`dice`)
5. DiCE fallback: `none` (fallback yok)
6. Ortalama PD iyilesmesi (`base_pd - best_pd`): `0.001096`

### 2.2 Approval etkisi
1. Oncesi approval rate: `0.763`
2. Sonrasi approval rate: `0.763`
3. Net lift: `0.0`

Yorum:
1. Bu kosuda DiCE entegrasyonu teknik olarak basarili calisti (fallback yok).
2. Ancak risk kapisi altinda (CI/reliability gate), reddedilen musterilerde approval'a donusen bir segment olusmadi.

---

## 3) Fairness + Stress Degisimi

### 3.1 Fairness (before/after)
1. `approval_gap`: `0.100306 -> 0.100306` (`delta=0.0`)
2. `equalized_odds_gap`: `0.117733 -> 0.117733` (`delta=0.0`)
3. `high_stress_approval_gap`: `0.100306 -> 0.100306` (`delta=0.0`)

### 3.2 Senaryo bazli stress matrix
1. `base`, `interest_rate_plus_2`, `interest_rate_plus_5`, `unemployment_plus_3`, `combined_stress` senaryolarinin tamaminda:
   - `approval_gap_delta = 0.0`
   - `equalized_odds_gap_delta = 0.0`

Yorum:
1. Bu batch kosusunda recourse uygulamasinin fairness/stress metriklerinde olculebilir degisiklik üretmedigi goruldu.

---

## 4) Operasyonel Sure ve Hata Analizi

### 4.1 Latency
1. Ortalama satir suresi: `418.56 ms`
2. `p50`: `225.55 ms`
3. `p95`: `332.90 ms`
4. `p99`: `8949.75 ms`
5. Maksimum: `17366.88 ms`

### 4.2 Outlier incelemesi
1. `>1 sn` satir sayisi: `21`
2. `>5 sn` satir sayisi: `18`
3. En yavas satirlar hata uretmedi; hepsi `dice` backend ile tamamlandi.

Yorum:
1. Ortalama/p95 saglikli olmasina ragmen ust kuyrukta ciddi latency outlier'lari var.
2. Bu outlier'lar icin sonraki adimda satir-bazli profiler/tracing ile darbogaz analizi onerilir (DiCE runtime, model call, GC, native lib overhead).

---

## 5) Uretilen Ciktilar

Artifact klasoru:
`credit-coach/artifacts/runs/20260307_013513_4f12f1_9cba96/`

Ana dosyalar:
1. `metrics.json`
2. `tables/batch_summary.json`
3. `tables/batch_recourse_results.csv`
4. `tables/dice_backend_distribution.csv`
5. `tables/dice_fallback_distribution.csv`
6. `tables/batch_fairness_change.csv`
7. `tables/batch_fairness_stress_compare.csv`
8. `tables/batch_error_breakdown.csv`

---

## 6) Sonuc
1. 1000 musteri batch kosusu teknik olarak stabil tamamlandi (error yok).
2. DiCE entegrasyonu bu kosuda tam basari verdi (`dice_success_rate=1.0`).
3. Buna karsin approval/fairness/stress metriklerinde anlamli bir iyilesme gorulmedi.
4. Ust kuyruk latency outlier'lari urun seviyesinde optimize edilmesi gereken bir alan olarak tespit edildi.
