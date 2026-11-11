# Demo v0: recourse, kalibrasyon dilimi sayıları (ADR-006 adım 3)

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Yalnızca kalibrasyon dilimi; test dilimi yüklenmedi. Maliyet ve süre varsayımdır.
bundle.lock.json sha256: `22fc32a4711b234aced22ef67d43f957658e59fc78a284c7c83ab51a744c80b9`

## Küme

| Büyüklük | Sayı |
|---|---|
| Kalibrasyon kaydı | 81136 |
| Destek dışı (dışarıda bırakıldı) | 6 |
| v1 temel karar APPROVED | 28801 |
| v1 temel karar CONDITIONAL | 100 |
| v1 temel karar REJECTED | 52229 |

Reddedilen (v1 REJECTED, destek içi): **52229**

## Geçerli planı olan reddedilen oranı ve yol dağılımı

| δ | dti güncelleme | en az bir yolda plan | customer | hybrid | institution |
|---|---|---|---|---|---|
| 0 | kapalı | 29.7% | 8.7% | 23.7% | 16.8% |
| 0 | açık | 34.1% | 12.2% | 28.4% | 16.8% |
| 0.01 | kapalı | 19.1% | 4.2% | 15.9% | 8.3% |
| 0.01 | açık | 23.2% | 6.6% | 20.1% | 8.3% |
| 0.02 | kapalı | 19.1% | 4.2% | 15.9% | 8.3% |
| 0.02 | açık | 23.2% | 6.6% | 20.1% | 8.3% |
| 0.03 | kapalı | 8.6% | 1.4% | 7.6% | 2.5% |
| 0.03 | açık | 11.6% | 2.8% | 10.6% | 2.5% |

## Yol kümesi dağılımı (kayıt başına hangi yollarda plan var)

| δ | dti | PLAN_YOK | customer | customer+hybrid | customer+hybrid+institution | hybrid | hybrid+institution | institution |
|---|---|---|---|---|---|---|---|---|
| 0 | kapalı | 70.3% | 0.5% | 4.0% | 4.3% | 8.4% | 7.0% | 5.5% |
| 0 | açık | 65.9% | 0.7% | 6.4% | 5.2% | 10.2% | 6.6% | 5.0% |
| 0.01 | kapalı | 80.9% | 0.3% | 2.9% | 1.0% | 7.7% | 4.4% | 2.9% |
| 0.01 | açık | 76.8% | 0.4% | 4.8% | 1.4% | 9.7% | 4.3% | 2.7% |
| 0.02 | kapalı | 80.9% | 0.3% | 2.9% | 1.0% | 7.7% | 4.4% | 2.9% |
| 0.02 | açık | 76.8% | 0.4% | 4.8% | 1.4% | 9.7% | 4.3% | 2.7% |
| 0.03 | kapalı | 91.4% | 0.1% | 1.1% | 0.1% | 4.9% | 1.4% | 0.9% |
| 0.03 | açık | 88.4% | 0.2% | 2.4% | 0.2% | 6.6% | 1.4% | 0.9% |

## Eylem seviyesi başına durum (tek seviye, reddedilenler içinde, kayıt payı)

| δ | dti | eylem | seviye | UYGULANAMAZ | SEVIYE_GECERSIZ | DESTEK_DISI | ETKI_YETERSIZ | GECERLI |
|---|---|---|---|---|---|---|---|---|
| 0 | kapalı | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 26.2% | 2.7% |
| 0 | kapalı | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 48.2% | 5.6% |
| 0 | kapalı | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 50.8% | 7.0% |
| 0 | kapalı | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 80.2% | 3.2% |
| 0 | kapalı | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 79.0% | 8.1% |
| 0 | kapalı | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 69.6% | 15.4% |
| 0 | açık | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 25.9% | 3.2% |
| 0 | açık | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 47.9% | 7.3% |
| 0 | açık | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 54.2% | 10.6% |
| 0 | açık | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 80.2% | 3.2% |
| 0 | açık | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 79.0% | 8.1% |
| 0 | açık | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 69.6% | 15.4% |
| 0.01 | kapalı | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 27.8% | 1.1% |
| 0.01 | kapalı | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 51.3% | 2.4% |
| 0.01 | kapalı | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 54.3% | 3.5% |
| 0.01 | kapalı | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.01 | kapalı | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.01 | kapalı | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.01 | açık | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 27.7% | 1.4% |
| 0.01 | açık | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 51.6% | 3.6% |
| 0.01 | açık | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 58.8% | 5.9% |
| 0.01 | açık | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.01 | açık | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.01 | açık | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.02 | kapalı | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 27.8% | 1.1% |
| 0.02 | kapalı | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 51.3% | 2.4% |
| 0.02 | kapalı | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 54.3% | 3.5% |
| 0.02 | kapalı | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.02 | kapalı | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.02 | kapalı | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.02 | açık | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 27.7% | 1.4% |
| 0.02 | açık | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 51.6% | 3.6% |
| 0.02 | açık | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 58.8% | 5.9% |
| 0.02 | açık | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.02 | açık | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.02 | açık | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.03 | kapalı | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 28.6% | 0.3% |
| 0.03 | kapalı | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 53.0% | 0.7% |
| 0.03 | kapalı | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 56.6% | 1.2% |
| 0.03 | kapalı | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.4% | 0.0% |
| 0.03 | kapalı | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 86.7% | 0.3% |
| 0.03 | kapalı | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 82.5% | 2.5% |
| 0.03 | açık | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 28.7% | 0.4% |
| 0.03 | açık | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 53.9% | 1.3% |
| 0.03 | açık | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 62.2% | 2.6% |
| 0.03 | açık | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.4% | 0.0% |
| 0.03 | açık | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 86.7% | 0.3% |
| 0.03 | açık | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 82.5% | 2.5% |

## Yol başına medyan USD maliyeti (plan olan kayıtlar, yolun en ucuz planı)

| δ | dti | customer | hybrid | institution |
|---|---|---|---|---|
| 0 | kapalı | 5,708 (n=4558) | 7,214 (n=12389) | 3,000 (n=8779) |
| 0 | açık | 6,464 (n=6374) | 7,661 (n=14824) | 3,000 (n=8779) |
| 0.01 | kapalı | 8,379 (n=2174) | 8,704 (n=8316) | 5,050 (n=4355) |
| 0.01 | açık | 9,488 (n=3443) | 9,391 (n=10490) | 5,050 (n=4355) |
| 0.02 | kapalı | 8,379 (n=2173) | 8,699 (n=8313) | 5,050 (n=4355) |
| 0.02 | açık | 9,491 (n=3442) | 9,391 (n=10488) | 5,050 (n=4355) |
| 0.03 | kapalı | 11,119 (n=712) | 11,108 (n=3957) | 7,500 (n=1297) |
| 0.03 | açık | 13,840 (n=1468) | 12,321 (n=5543) | 7,500 (n=1297) |
