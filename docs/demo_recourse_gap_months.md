# Demo v0: recourse, boşluk ayları ve kalibrasyon yan yana

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Boşluk ayları: 2015-01, 02, 07, 08 (etiket kullanılmadı, test dilimi yüklenmedi). Maliyet ve süre varsayımdır.

## Küme

| Büyüklük | kalibrasyon | boşluk |
|---|---|---|
| Kayıt | 81136 | 94456 |
| Destek dışı | 6 | 6 |
| v1 APPROVED | 28801 | 34812 |
| v1 CONDITIONAL | 100 | 109 |
| v1 REJECTED (destek içi) | 52229 | 59529 |

## Geçerli planı olan reddedilen oranı

| δ | dti | dilim | en az bir yol | customer | hybrid | institution | PLAN_YOK |
|---|---|---|---|---|---|---|---|
| 0 | kapalı | kalibrasyon | 29.7% | 8.7% | 23.7% | 16.8% | 70.3% |
| 0 | kapalı | boşluk | 30.0% | 9.1% | 23.9% | 17.2% | 70.0% |
| 0 | açık | kalibrasyon | 34.1% | 12.2% | 28.4% | 16.8% | 65.9% |
| 0 | açık | boşluk | 34.3% | 12.4% | 28.5% | 17.2% | 65.7% |
| 0.01 | kapalı | kalibrasyon | 19.1% | 4.2% | 15.9% | 8.3% | 80.9% |
| 0.01 | kapalı | boşluk | 19.4% | 4.3% | 16.1% | 8.7% | 80.6% |
| 0.01 | açık | kalibrasyon | 23.2% | 6.6% | 20.1% | 8.3% | 76.8% |
| 0.01 | açık | boşluk | 23.5% | 6.8% | 20.3% | 8.7% | 76.5% |
| 0.02 | kapalı | kalibrasyon | 19.1% | 4.2% | 15.9% | 8.3% | 80.9% |
| 0.02 | kapalı | boşluk | 19.4% | 4.3% | 16.1% | 8.7% | 80.6% |
| 0.02 | açık | kalibrasyon | 23.2% | 6.6% | 20.1% | 8.3% | 76.8% |
| 0.02 | açık | boşluk | 23.5% | 6.8% | 20.3% | 8.7% | 76.5% |
| 0.03 | kapalı | kalibrasyon | 8.6% | 1.4% | 7.6% | 2.5% | 91.4% |
| 0.03 | kapalı | boşluk | 8.9% | 1.5% | 7.8% | 2.7% | 91.1% |
| 0.03 | açık | kalibrasyon | 11.6% | 2.8% | 10.6% | 2.5% | 88.4% |
| 0.03 | açık | boşluk | 12.0% | 3.0% | 10.9% | 2.7% | 88.0% |

## Eylem seviyesi başına durum (kayıt payı, reddedilenler içinde)

| δ | dti | dilim | eylem | seviye | UYGULANAMAZ | SEVIYE_GECERSIZ | DESTEK_DISI | ETKI_YETERSIZ | GECERLI |
|---|---|---|---|---|---|---|---|---|---|
| 0 | kapalı | kalibrasyon | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 26.2% | 2.7% |
| 0 | kapalı | kalibrasyon | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 48.2% | 5.6% |
| 0 | kapalı | kalibrasyon | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 50.8% | 7.0% |
| 0 | kapalı | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 80.2% | 3.2% |
| 0 | kapalı | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 79.0% | 8.1% |
| 0 | kapalı | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 69.6% | 15.4% |
| 0 | kapalı | boşluk | revolving_paydown | util_70 | 69.9% | 1.1% | 0.0% | 26.2% | 2.8% |
| 0 | kapalı | boşluk | revolving_paydown | util_50 | 39.8% | 6.7% | 0.0% | 47.8% | 5.8% |
| 0 | kapalı | boşluk | revolving_paydown | util_30 | 13.9% | 28.8% | 0.0% | 50.1% | 7.2% |
| 0 | kapalı | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 79.9% | 3.3% |
| 0 | kapalı | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 78.5% | 8.4% |
| 0 | kapalı | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 69.1% | 15.9% |
| 0 | açık | kalibrasyon | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 25.9% | 3.2% |
| 0 | açık | kalibrasyon | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 47.9% | 7.3% |
| 0 | açık | kalibrasyon | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 54.2% | 10.6% |
| 0 | açık | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 80.2% | 3.2% |
| 0 | açık | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 79.0% | 8.1% |
| 0 | açık | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 69.6% | 15.4% |
| 0 | açık | boşluk | revolving_paydown | util_70 | 69.9% | 0.9% | 0.0% | 25.9% | 3.3% |
| 0 | açık | boşluk | revolving_paydown | util_50 | 39.8% | 5.0% | 0.0% | 47.7% | 7.5% |
| 0 | açık | boşluk | revolving_paydown | util_30 | 13.9% | 21.5% | 0.0% | 53.9% | 10.7% |
| 0 | açık | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 79.9% | 3.3% |
| 0 | açık | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 78.5% | 8.4% |
| 0 | açık | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 69.1% | 15.9% |
| 0.01 | kapalı | kalibrasyon | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 27.8% | 1.1% |
| 0.01 | kapalı | kalibrasyon | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 51.3% | 2.4% |
| 0.01 | kapalı | kalibrasyon | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 54.3% | 3.5% |
| 0.01 | kapalı | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.01 | kapalı | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.01 | kapalı | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.01 | kapalı | boşluk | revolving_paydown | util_70 | 69.9% | 1.1% | 0.0% | 27.8% | 1.2% |
| 0.01 | kapalı | boşluk | revolving_paydown | util_50 | 39.8% | 6.7% | 0.0% | 51.0% | 2.6% |
| 0.01 | kapalı | boşluk | revolving_paydown | util_30 | 13.9% | 28.8% | 0.0% | 53.7% | 3.6% |
| 0.01 | kapalı | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 82.8% | 0.4% |
| 0.01 | kapalı | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 84.2% | 2.7% |
| 0.01 | kapalı | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.6% | 8.3% |
| 0.01 | açık | kalibrasyon | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 27.7% | 1.4% |
| 0.01 | açık | kalibrasyon | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 51.6% | 3.6% |
| 0.01 | açık | kalibrasyon | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 58.8% | 5.9% |
| 0.01 | açık | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.01 | açık | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.01 | açık | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.01 | açık | boşluk | revolving_paydown | util_70 | 69.9% | 0.9% | 0.0% | 27.7% | 1.5% |
| 0.01 | açık | boşluk | revolving_paydown | util_50 | 39.8% | 5.0% | 0.0% | 51.3% | 3.9% |
| 0.01 | açık | boşluk | revolving_paydown | util_30 | 13.9% | 21.5% | 0.0% | 58.5% | 6.1% |
| 0.01 | açık | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 82.8% | 0.4% |
| 0.01 | açık | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 84.2% | 2.7% |
| 0.01 | açık | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.6% | 8.3% |
| 0.02 | kapalı | kalibrasyon | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 27.8% | 1.1% |
| 0.02 | kapalı | kalibrasyon | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 51.3% | 2.4% |
| 0.02 | kapalı | kalibrasyon | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 54.3% | 3.5% |
| 0.02 | kapalı | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.02 | kapalı | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.02 | kapalı | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.02 | kapalı | boşluk | revolving_paydown | util_70 | 69.9% | 1.1% | 0.0% | 27.8% | 1.2% |
| 0.02 | kapalı | boşluk | revolving_paydown | util_50 | 39.8% | 6.7% | 0.0% | 51.0% | 2.6% |
| 0.02 | kapalı | boşluk | revolving_paydown | util_30 | 13.9% | 28.8% | 0.0% | 53.7% | 3.6% |
| 0.02 | kapalı | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 82.8% | 0.4% |
| 0.02 | kapalı | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 84.2% | 2.7% |
| 0.02 | kapalı | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.6% | 8.3% |
| 0.02 | açık | kalibrasyon | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 27.7% | 1.4% |
| 0.02 | açık | kalibrasyon | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 51.6% | 3.6% |
| 0.02 | açık | kalibrasyon | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 58.8% | 5.9% |
| 0.02 | açık | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.1% | 0.3% |
| 0.02 | açık | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 84.5% | 2.5% |
| 0.02 | açık | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.9% | 8.0% |
| 0.02 | açık | boşluk | revolving_paydown | util_70 | 69.9% | 0.9% | 0.0% | 27.7% | 1.5% |
| 0.02 | açık | boşluk | revolving_paydown | util_50 | 39.8% | 5.0% | 0.0% | 51.4% | 3.9% |
| 0.02 | açık | boşluk | revolving_paydown | util_30 | 13.9% | 21.5% | 0.0% | 58.5% | 6.1% |
| 0.02 | açık | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 82.8% | 0.4% |
| 0.02 | açık | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 84.2% | 2.7% |
| 0.02 | açık | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 76.6% | 8.3% |
| 0.03 | kapalı | kalibrasyon | revolving_paydown | util_70 | 70.0% | 1.1% | 0.0% | 28.6% | 0.3% |
| 0.03 | kapalı | kalibrasyon | revolving_paydown | util_50 | 40.1% | 6.2% | 0.0% | 53.0% | 0.7% |
| 0.03 | kapalı | kalibrasyon | revolving_paydown | util_30 | 14.0% | 28.2% | 0.0% | 56.6% | 1.2% |
| 0.03 | kapalı | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.4% | 0.0% |
| 0.03 | kapalı | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 86.7% | 0.3% |
| 0.03 | kapalı | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 82.5% | 2.5% |
| 0.03 | kapalı | boşluk | revolving_paydown | util_70 | 69.9% | 1.1% | 0.0% | 28.7% | 0.3% |
| 0.03 | kapalı | boşluk | revolving_paydown | util_50 | 39.8% | 6.7% | 0.0% | 52.8% | 0.8% |
| 0.03 | kapalı | boşluk | revolving_paydown | util_30 | 13.9% | 28.8% | 0.0% | 56.1% | 1.2% |
| 0.03 | kapalı | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 83.2% | 0.0% |
| 0.03 | kapalı | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 86.5% | 0.4% |
| 0.03 | kapalı | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 82.3% | 2.7% |
| 0.03 | açık | kalibrasyon | revolving_paydown | util_70 | 70.0% | 0.9% | 0.0% | 28.7% | 0.4% |
| 0.03 | açık | kalibrasyon | revolving_paydown | util_50 | 40.1% | 4.7% | 0.0% | 53.9% | 1.3% |
| 0.03 | açık | kalibrasyon | revolving_paydown | util_30 | 14.0% | 21.2% | 0.0% | 62.2% | 2.6% |
| 0.03 | açık | kalibrasyon | loan_amount_reduction | amnt_90 | 0.3% | 16.3% | 0.0% | 83.4% | 0.0% |
| 0.03 | açık | kalibrasyon | loan_amount_reduction | amnt_75 | 0.4% | 12.5% | 0.0% | 86.7% | 0.3% |
| 0.03 | açık | kalibrasyon | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 82.5% | 2.5% |
| 0.03 | açık | boşluk | revolving_paydown | util_70 | 69.9% | 0.9% | 0.0% | 28.8% | 0.5% |
| 0.03 | açık | boşluk | revolving_paydown | util_50 | 39.8% | 5.0% | 0.0% | 53.7% | 1.5% |
| 0.03 | açık | boşluk | revolving_paydown | util_30 | 13.9% | 21.5% | 0.0% | 61.9% | 2.7% |
| 0.03 | açık | boşluk | loan_amount_reduction | amnt_90 | 0.3% | 16.5% | 0.0% | 83.2% | 0.0% |
| 0.03 | açık | boşluk | loan_amount_reduction | amnt_75 | 0.5% | 12.7% | 0.0% | 86.5% | 0.4% |
| 0.03 | açık | boşluk | loan_amount_reduction | amnt_50 | 1.0% | 14.0% | 0.0% | 82.3% | 2.7% |

## Yol başına medyan USD maliyeti (varsayım)

| δ | dti | dilim | customer | hybrid | institution |
|---|---|---|---|---|---|
| 0 | kapalı | kalibrasyon | 5,708 (n=4558) | 7,214 (n=12389) | 3,000 (n=8779) |
| 0 | kapalı | boşluk | 5,613 (n=5401) | 7,135 (n=14211) | 3,000 (n=10264) |
| 0 | açık | kalibrasyon | 6,464 (n=6374) | 7,661 (n=14824) | 3,000 (n=8779) |
| 0 | açık | boşluk | 6,397 (n=7380) | 7,674 (n=16942) | 3,000 (n=10264) |
| 0.01 | kapalı | kalibrasyon | 8,379 (n=2174) | 8,704 (n=8316) | 5,050 (n=4355) |
| 0.01 | kapalı | boşluk | 8,385 (n=2567) | 8,807 (n=9605) | 5,038 (n=5154) |
| 0.01 | açık | kalibrasyon | 9,488 (n=3443) | 9,391 (n=10490) | 5,050 (n=4355) |
| 0.01 | açık | boşluk | 9,398 (n=4024) | 9,506 (n=12077) | 5,038 (n=5154) |
| 0.02 | kapalı | kalibrasyon | 8,379 (n=2173) | 8,699 (n=8313) | 5,050 (n=4355) |
| 0.02 | kapalı | boşluk | 8,402 (n=2567) | 8,808 (n=9600) | 5,000 (n=5150) |
| 0.02 | açık | kalibrasyon | 9,491 (n=3442) | 9,391 (n=10488) | 5,050 (n=4355) |
| 0.02 | açık | boşluk | 9,411 (n=4023) | 9,507 (n=12075) | 5,000 (n=5150) |
| 0.03 | kapalı | kalibrasyon | 11,119 (n=712) | 11,108 (n=3957) | 7,500 (n=1297) |
| 0.03 | kapalı | boşluk | 11,437 (n=876) | 11,185 (n=4631) | 7,500 (n=1607) |
| 0.03 | açık | kalibrasyon | 13,840 (n=1468) | 12,321 (n=5543) | 7,500 (n=1297) |
| 0.03 | açık | boşluk | 14,451 (n=1780) | 12,434 (n=6485) | 7,500 (n=1607) |
