# Hafta 3: kural kapsama raporu

Her kural ve gerekçe kodu en az bir senaryoyla tetiklenmelidir. "politika varyantı" işaretli senaryolar v1'in kendisiyle değil, ret eşiği veya zayıf destek aralığı değiştirilmiş bir politikayla çalışır (v1'de R1 pasif, R3 bu eşikte hiç tetiklenmez).

| Kural | Tetikleyen senaryolar |
|---|---|
| R1_HARD_REJECT | hard_reject (politika varyantı) |
| R2_THRESHOLD_BAND | straddles_threshold, above_but_within_band, below_but_within_band |
| R3_WEAK_SUPPORT_NEAR | weak_support_near (politika varyantı) |
| R4_APPROVE | approve_clear, weak_support_but_far (politika varyantı) |
| R5_NOT_APPROVED_PLAN | not_approved_plan_available |
| R6_NOT_APPROVED | not_approved_plan_unknown, not_approved_no_plan |
| R0_SUPPORT_CHECK | destek_disi_dti_999 (destek kontrolü) |

| Gerekçe kodu | Tetikleyen senaryolar |
|---|---|
| PD_BELOW_THRESHOLD | approve_clear, weak_support_but_far (politika varyantı) |
| PD_ABOVE_THRESHOLD | not_approved_plan_unknown, not_approved_no_plan, not_approved_plan_available |
| PLAN_AVAILABLE | not_approved_plan_available |
| NO_PLAN_AVAILABLE | not_approved_no_plan |
| REVIEW_REQUIRED | straddles_threshold, above_but_within_band, below_but_within_band, weak_support_near (politika varyantı), destek_disi_dti_999 (destek kontrolü) |
| HARD_REJECT_THRESHOLD | hard_reject (politika varyantı) |
| INTERVAL_STRADDLES_THRESHOLD | straddles_threshold |
| WITHIN_BAND_OF_THRESHOLD | above_but_within_band, below_but_within_band |
| WEAK_SUPPORT_NEAR_THRESHOLD | weak_support_near (politika varyantı) |
| OUT_OF_SUPPORT | destek_disi_dti_999 (destek kontrolü) |
