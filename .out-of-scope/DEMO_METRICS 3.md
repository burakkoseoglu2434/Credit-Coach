# Credit Coach Demo Metrics

Bu dosya, bugun elde bulunan en somut ciktilari tek yerde toplar.

Amac:

- yatirimciya veya paydasa "sistem gercekte ne uretiyor?" sorusunu net gostermek
- teknik detayda bogulmadan, dogrudan gosterilecek artifact ve KPI setini sabitlemek
- demo sirasinda hangi dosyayi hangi hikaye ile anlatacagimizi netlestirmek

## 1. En Somut 4 Dosya

Eger yalnizca 4 dosya gostereceksek, varsayilan paket bu olmali:

1. `customer_roadmap.json`
2. `batch_summary.json`
3. `offer_optimization_summary.json`
4. `milestone_acceptance_review.md`

Bunlar birlikte su hikayeyi verir:

- sistem tek musteri icin ne oneriyor
- toplu olarak ne kadar iyilesme uretiyor
- kurumsal teklif optimizasyonu var mi
- tum bu is governance ve release kontrolunden geciyor mu

Not:

- Ciktilar tipik olarak `artifacts/runs/<RUN_ID>/tables/` altina yazilir.
- Seeded suite veya challenger ozetlerinde bircok metric `canonical_metrics` altinda tutulur.

## 2. En Guclu Demo Akisi

Demo sirasi su olmali:

1. Tek musteri yol haritasi
2. Toplu KPI etkisi
3. Oneri kalitesi ve uygulanabilirlik
4. Offer optimization
5. Learning loop
6. Governance / acceptance

Bu sira sunu anlatir:

- sistem once "ne oneriyor"
- sonra "bu oneri toplu olarak ise yariyor mu"
- sonra "gercekci mi"
- sonra "ticari degeri var mi"
- sonra "zamanla ogrenebilir mi"
- en sonda "kurumsal olarak guvenli mi"

## 3. Tek Musteri Demosu: Ne Uretiyoruz?

Ana artifact'ler:

- `customer_roadmap.json`
- `customer_roadmap_steps.csv`
- `weekly_coaching.csv`
- `decision_log_record.json`

One cikacak alanlar:

| Alan | Ne gosterir | Neden onemli |
| --- | --- | --- |
| `action_key` | Kullaniciya gorunen aksiyon | Oneri artik yalnizca feature edit degil |
| `action_class` | `behavioral`, `structural`, `institutional` | Gercek dunya aksiyon semantigi oldugunu gosterir |
| `offer_type` | Kurumsal teklif tipi | Fintech teklif katmani oldugunu gosterir |
| `offer_terms` | Teklifin acik term'leri | Sistem sembolik degil, hesaplanabilir teklif uretiyor |
| `phase_id` | `phase_1_stabilize`, `phase_2_build`, `phase_3_optimize` | Plan tek adimli degil, fazli trajectory |
| `target_pd` | Faz hedefi | Planin risk hedefi var |
| `plan_execution_probability` | Plani gercekte uygulama olasiligi | Davranis farkindaligi |
| `offer_acceptance_probability` | Teklifin kabul edilme olasiligi | Offer optimizer mantigi |
| `combined_plan_realization_probability` | Plan + teklif birlikte gerceklesme olasiligi | Gercek hayata yakinlasmis etki tahmini |
| `trajectory_status` | `on_track`, `needs_replan`, `degraded` | Yol haritasi adaptif mi, onu gosterir |

Tek cumlelik anlatim:

"Biz sadece red nedeni gostermiyoruz; musteri icin fazli bir yol haritasi, davranissal uygulanabilirlik ve gerekiyorsa kurum teklifini ayni plan icinde uretiyoruz."

## 4. Toplu KPI Etkisi: Cohort'ta Ne Oluyor?

Ana artifact:

- `batch_summary.json`

En guclu cohort KPI'lari:

| KPI | Ne anlatir | Demo cümlesi |
| --- | --- | --- |
| `denied_to_approved_lift` | Reddedilenlerin ne kadarinin onay bandina yaklastigi | "Motorun ana donusum KPI'i bu." |
| `before_approval_rate` | Baslangic onay orani | "Baslangic seviyesi buydu." |
| `after_approval_rate` | Oneri sonrasi onay orani | "Oneriler sonrasi olusan hedef durum bu." |
| `approval_rate_lift` | Onay oranindaki degisim | "Toplu etkide net artis burada goruluyor." |
| `avg_pd_reduction` | Ortalama PD dususu | "Sadece onay degil, risk kalitesini de iyilestiriyoruz." |
| `high_risk_reachability_rate` | Zor segmentte ulasilabilirlik | "En zor musterilerde bile yol acilabiliyor mu?" |
| `denied_high_risk_lift` | High-risk denied uplift | "Zor segmentteki asim kazanc burada." |
| `trajectory_gate_pass_rate_4w` | 4 haftada gate-pass tahmini | "Kisa vadede plan yasiyor mu?" |
| `trajectory_gate_pass_rate_12w` | 12 haftada guclenme | "Orta vade teyidi." |
| `trajectory_gate_pass_rate_24w` | 24 haftada kalicilik | "Uzun vadeli stabilizasyon." |

Yatirimciya gostermek icin varsayilan 3 KPI:

1. `denied_to_approved_lift`
2. `avg_pd_reduction`
3. `trajectory_gate_pass_rate_4w`

Tek cumlelik anlatim:

"Sistem yalnizca teori uretmiyor; reddedilen portfoyde onay potansiyelini artirirken riski de asagi cekiyor."

## 5. Oneri Kalitesi: Oneriler Gercekci mi?

Ana artifact'ler:

- `candidate_quality_summary.json`
- `action_realism_summary.json`
- `behavior_aware_summary.json`
- `trajectory_summary.json`

### 5.1 Candidate Quality

One cikacak alanlar:

- `candidate_pool_diversity_index`
- `candidate_source_entropy`
- `best_source_internal_rate`
- `best_source_dice_rate`
- `best_source_rule_rate`
- `best_source_fallback_rate`

Ne anlatir:

- motor hep ayni tur oneriyi vermiyor
- alternatif generator'lar arasinda secim yapabiliyor
- oneriler tek kaynaga bagli degil

### 5.2 Action Realism

One cikacak alanlar:

- `action_type_behavioral_rate`
- `action_type_structural_rate`
- `action_type_institutional_rate`
- `composite_action_rate`
- `clipped_action_rate`
- `rejected_action_rate`
- `repair_applied_rate`
- `approval_pending_action_rate`
- `invalid_combination_rate`
- `infeasible_plan_rate`
- `dominant_rejection_reason`

Ne anlatir:

- oneriler gercek dunya aksiyonlarina donusmus durumda
- feasibility ve conflict kurallari calisiyor
- sistem anlamsiz planlari sessizce kabul etmiyor

### 5.3 Behavior-Aware Quality

One cikacak alanlar:

- `mean_plan_execution_probability`
- `expected_pd_improvement`
- `partial_execution_rate`
- `mixed_execution_rate`
- `failed_execution_rate`
- `expected_partial_progress_rate`

Ne anlatir:

- sistem "yapilabilir" ile "yapilir" arasindaki farki modellemeye baslamis durumda
- sadece teorik etki degil, gerceklesme ihtimali de ranking'e giriyor

### 5.4 Sequential Trajectory Quality

One cikacak alanlar:

- `trajectory_gate_pass_rate_4w`
- `trajectory_gate_pass_rate_12w`
- `trajectory_gate_pass_rate_24w`
- `trajectory_partial_progress_rate`
- `trajectory_median_time_to_gate_pass_days`
- `trajectory_soft_regression_penalty_mean`
- `trajectory_on_track_rate`
- `trajectory_needs_replan_rate`
- `trajectory_degraded_rate`
- `dominant_transition_reason`

Ne anlatir:

- plan tek adimli degil, zaman icinde izlenebilir
- erken checkpoint sagligi onceliklidir
- sistem gerekirse replan ihtiyacini da acikca isaretler

Tek cumlelik anlatim:

"Onerilerimiz sadece akilli degil; cesitli, gercekci, davranis farkindalikli ve zaman icinde izlenebilir."

## 6. Offer Optimization: Ticari Katman

Ana artifact:

- `offer_optimization_summary.json`

Companion breakdown'lar:

- `offer_type_breakdown.csv`
- `offer_policy_arm_breakdown.csv`
- `offer_acceptance_breakdown.csv`
- `offer_proxy_impact_breakdown.csv`

One cikacak alanlar:

| KPI | Ne anlatir |
| --- | --- |
| `offer_plan_rate` | Planlarin ne kadarinda institution-side teklif var |
| `rankable_offer_rate` | Gercekten hesaplanabilir ve winner ranking'e girebilen teklif orani |
| `offer_acceptance_probability_mean` | Teklif kabul olasiliginin ortalamasi |
| `combined_plan_realization_probability_mean` | Plan + teklif birlikte gerceklesme olasiligi |
| `expected_recovery_proxy` | Recovery odakli ticari etki ozeti |
| `approval_rate_proxy_delta` | Approval proxy degisimi |
| `default_rate_90d_proxy_delta` | 90 gun default proxy degisimi |
| `avg_margin_90d_proxy_delta` | 90 gun margin proxy degisimi |
| `governance_safe_offer_rate` | Governance-safe kalan teklif orani |
| `dominant_offer_type` | En baskin teklif ailesi |

Tek cumlelik anlatim:

"Sistem sadece musteri aksiyonu onermiyor; kurum tarafli teklifleri de risk ve governance sinirlari icinde optimize edebiliyor."

## 7. Learning Loop: Sistem Ogrenmeye Hazir mi?

Ana artifact'ler:

- `decision_logging_summary.json`
- `outcome_ingestion_summary.json`
- `outcome_feedback_summary.json`
- `off_policy_evaluation.json`

One cikacak alanlar:

| KPI | Ne anlatir |
| --- | --- |
| `decision_log_completeness` | Kararlar ogrenmeye uygun sekilde log'laniyor mu |
| `policy_metadata_coverage` | Policy arm ve profil bilgisi ne kadar tam |
| `selection_propensity_coverage` | OPE icin gerekli propensity ne kadar mevcut |
| `reward_90d_coverage` | 90 gunluk reward penceresi ne kadar dolu |
| `default_90d_coverage` | Default outcome coverage |
| `margin_90d_coverage` | Margin outcome coverage |
| `learning_readiness_status_distribution` | `descriptive_only`, `partial_learning_ready`, `learning_ready` dagilimi |
| `comparison_status` | `treatment_vs_control` veya `baseline_missing` |
| `ope_confidence` | `strong`, `tentative`, `degraded` |
| `preferred_policy_signal` | Hangi arm'in sinyal verdigi |

Tek cumlelik anlatim:

"Bugun sistem sadece karar vermiyor; yarin hangi policy'nin daha iyi oldugunu ogrenebilecek veri omurgasini da kuruyor."

## 8. Governance ve Release Katmani

Ana artifact'ler:

- `kpi_contract_snapshot.json`
- `milestone_acceptance_summary.json`
- `release_evidence_pack.json`
- `milestone_acceptance_review.md`
- `telemetry_export.json`
- `production_smoke_report.json`

One cikacak alanlar:

| KPI / Alan | Ne anlatir |
| --- | --- |
| `release_decision` | Nihai release semantigi |
| `acceptance_status` | Milestone kabul durumu |
| `lift_pass` | Lift gate gecti mi |
| `reliability_pass` | Reliability gate gecti mi |
| `fairness_seed_pass_count` | Seed bazli fairness dayanikliligi |
| `worst_primary_fairness_gap` | En kotu fairness gap |
| `telemetry_gate_status` | Operasyonel telemetry sagligi |
| `broad_rollout_allowed` | Geniş rollout'a izin var mi |

Tek cumlelik anlatim:

"Bu motor yalnizca performans kovalamiyor; fairness, reliability, telemetry ve acceptance governance katmanlariyla birlikte calisiyor."

## 9. Yatirimciya Gosterilecek Varsayilan 10 KPI

Eger tek sayfada sadece 10 KPI gostereceksek, bu liste kullanilsin:

1. `denied_to_approved_lift`
2. `avg_pd_reduction`
3. `trajectory_gate_pass_rate_4w`
4. `mean_plan_execution_probability`
5. `candidate_pool_diversity_index`
6. `infeasible_plan_rate`
7. `offer_acceptance_probability_mean`
8. `expected_recovery_proxy`
9. `decision_log_completeness`
10. `reward_90d_coverage`

Bu 10 KPI birlikte su 5 soruyu cevaplar:

- Donusum uretiyor mu
- risk iyilesiyor mu
- oneriler uygulanabilir mi
- ticari katman var mi
- sistem ogrenmeye hazir mi

## 10. Yatirimciya Gosterilecek Varsayilan 6 Artifact

Eger "bana somut dosya goster" denirse, varsayilan paket bu olmali:

1. `customer_roadmap.json`
2. `batch_summary.json`
3. `action_realism_summary.json`
4. `behavior_aware_summary.json`
5. `offer_optimization_summary.json`
6. `milestone_acceptance_review.md`

## 11. 5 Dakikalik Demo Konusma Akisi

### Dakika 1

`customer_roadmap.json`

Soylenecek cumle:

"Burada tek bir musteri icin sistemin urettigi fazli yol haritasini goruyorsunuz. Aksiyonlar behavioral, structural ve institutional olarak ayriliyor; gerekiyorsa kurumsal offer da planda yer aliyor."

### Dakika 2

`batch_summary.json`

Soylenecek cumle:

"Tek musteri ornegi guzel ama asil soru cohort'ta ne oldugu. Bu ozet, recourse motorunun reddedilen musteri havuzunda ne kadar uplift ve risk iyilesmesi uretebildigini gosteriyor."

### Dakika 3

`action_realism_summary.json` + `behavior_aware_summary.json`

Soylenecek cumle:

"Burada sadece teorik iyilestirme degil, onerinin gercekci olup olmadigini da olcuyoruz. Oneriler feasibility, conflict ve execution-likelihood kontrollerinden geciyor."

### Dakika 4

`offer_optimization_summary.json`

Soylenecek cumle:

"Bu katman projeyi klasik recourse motorundan ayiriyor. Sistem, kurum tarafli teklifleri de hesaba katarak approval, default ve margin proxy'leri uzerinden optimizasyon yapabiliyor."

### Dakika 5

`milestone_acceptance_review.md`

Soylenecek cumle:

"Son adimda tum bunlarin governance tarafini goruyorsunuz. Performans kadar fairness, reliability, telemetry ve release readiness da machine-readable artifact'lerle kontrol altinda."

## 12. Hemen Calistirilabilecek Komutlar

Tek musteri demosu:

```bash
cd credit-coach
python -m credit_coach.cli.run_recourse --customer_id demo
```

Toplu KPI demosu:

```bash
cd credit-coach
python -m credit_coach.cli.run_batch_recourse_eval --n_customers 1000
```

Outcome / learning demosu:

```bash
cd credit-coach
python -m credit_coach.cli.run_outcome_feedback --window_days 90
```

## 13. Tek Cumlelik Son Ozet

Bugun elimizdeki en somut gosterim su:

"Credit Coach, reddedilen musteri icin fazli ve gercekci aksiyon/offer planlari uretebilen; bunu cohort KPI'lari, governance artifact'leri ve learning loop metrikleriyle kanitlayabilen bir karar-istihbarati motoru."
