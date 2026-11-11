# Demo v0: δ = 0,02 (eski varsayılan) ve δ = 0,012 (varsayılan) yan yana

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Varsayılan δ = 0,012 (`configs/catalog/demo_v0.yaml`, `delta.deger`, varsayım, ADR-007). δ = 0,02 önceki varsayılandır ve yalnızca karşılaştırma içindir; API ve arayüz onu kullanmaz.

Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı. Etiket = kaydın planı olan yolları içinde en güçlü olanı. Hücre: kayıt sayısı (oran).

## kalibrasyon

| kova (p_point − eşik) | reddedilen | PLAN_YOK δ = 0,02 (eski varsayılan) | PLAN_YOK δ = 0,012 (varsayılan) | GUCLU δ = 0,02 (eski varsayılan) | GUCLU δ = 0,012 (varsayılan) | KOSULLU δ = 0,02 (eski varsayılan) | KOSULLU δ = 0,012 (varsayılan) | ZAYIF δ = 0,02 (eski varsayılan) | ZAYIF δ = 0,012 (varsayılan) |
|---|---|---|---|---|---|---|---|---|---|
| < 0 | 0 | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) |
| [0, 0,01) | 3943 | 932 (23.6%) | 932 (23.6%) | 57 (1.4%) | 528 (13.4%) | 511 (13.0%) | 2483 (63.0%) | 2443 (62.0%) | 0 (0.0%) |
| [0,01, 0,02) | 3855 | 1617 (41.9%) | 1617 (41.9%) | 0 (0.0%) | 38 (1.0%) | 142 (3.7%) | 2200 (57.1%) | 2096 (54.4%) | 0 (0.0%) |
| [0,02, 0,03) | 3529 | 2076 (58.8%) | 2076 (58.8%) | 0 (0.0%) | 0 (0.0%) | 88 (2.5%) | 257 (7.3%) | 1365 (38.7%) | 1196 (33.9%) |
| [0,03, 0,05) | 9757 | 7571 (77.6%) | 7571 (77.6%) | 0 (0.0%) | 0 (0.0%) | 57 (0.6%) | 296 (3.0%) | 2129 (21.8%) | 1890 (19.4%) |
| [0,05, 0,10) | 11171 | 10273 (92.0%) | 10273 (92.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 13 (0.1%) | 898 (8.0%) | 885 (7.9%) |
| [0,10, 0,20) | 14143 | 13953 (98.7%) | 13953 (98.7%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 190 (1.3%) | 190 (1.3%) |
| >= 0,20 | 5831 | 5827 (99.9%) | 5827 (99.9%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 4 (0.1%) | 4 (0.1%) |
| tümü | 52229 | 42249 (80.9%) | 42249 (80.9%) | 57 (0.1%) | 566 (1.1%) | 798 (1.5%) | 5249 (10.0%) | 9125 (17.5%) | 4165 (8.0%) |

> **Bu tablo ne demek:** Aynı reddedilen kayıtlar için iki δ'da, planı olmayanların (PLAN_YOK) ve planı olanlarda en güçlü yolun etiketinin sayısı; 'tümü' satırı tüm reddedilenleri verir.

> **Ne DEMEK DEĞİL:** Hangi δ'nın doğru olduğunu ya da etiketlerin gerçekte işe yarayacağını göstermez; δ bir varsayımdır (ADR-007), gerçek etki payı bilinmiyor.

## boşluk

| kova (p_point − eşik) | reddedilen | PLAN_YOK δ = 0,02 (eski varsayılan) | PLAN_YOK δ = 0,012 (varsayılan) | GUCLU δ = 0,02 (eski varsayılan) | GUCLU δ = 0,012 (varsayılan) | KOSULLU δ = 0,02 (eski varsayılan) | KOSULLU δ = 0,012 (varsayılan) | ZAYIF δ = 0,02 (eski varsayılan) | ZAYIF δ = 0,012 (varsayılan) |
|---|---|---|---|---|---|---|---|---|---|
| < 0 | 0 | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) | 0 (-) |
| [0, 0,01) | 4714 | 1104 (23.4%) | 1104 (23.4%) | 73 (1.5%) | 644 (13.7%) | 633 (13.4%) | 2964 (62.9%) | 2904 (61.6%) | 2 (0.0%) |
| [0,01, 0,02) | 4526 | 1936 (42.8%) | 1936 (42.8%) | 1 (0.0%) | 50 (1.1%) | 201 (4.4%) | 2540 (56.1%) | 2388 (52.8%) | 0 (0.0%) |
| [0,02, 0,03) | 4047 | 2384 (58.9%) | 2383 (58.9%) | 0 (0.0%) | 0 (0.0%) | 113 (2.8%) | 307 (7.6%) | 1550 (38.3%) | 1357 (33.5%) |
| [0,03, 0,05) | 11067 | 8569 (77.4%) | 8568 (77.4%) | 0 (0.0%) | 0 (0.0%) | 81 (0.7%) | 357 (3.2%) | 2417 (21.8%) | 2142 (19.4%) |
| [0,05, 0,10) | 12809 | 11854 (92.5%) | 11854 (92.5%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 23 (0.2%) | 955 (7.5%) | 932 (7.3%) |
| [0,10, 0,20) | 15908 | 15664 (98.5%) | 15664 (98.5%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 244 (1.5%) | 244 (1.5%) |
| >= 0,20 | 6458 | 6453 (99.9%) | 6453 (99.9%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 5 (0.1%) | 5 (0.1%) |
| tümü | 59529 | 47964 (80.6%) | 47962 (80.6%) | 74 (0.1%) | 694 (1.2%) | 1028 (1.7%) | 6191 (10.4%) | 10463 (17.6%) | 4682 (7.9%) |

> **Bu tablo ne demek:** Aynı reddedilen kayıtlar için iki δ'da, planı olmayanların (PLAN_YOK) ve planı olanlarda en güçlü yolun etiketinin sayısı; 'tümü' satırı tüm reddedilenleri verir.

> **Ne DEMEK DEĞİL:** Hangi δ'nın doğru olduğunu ya da etiketlerin gerçekte işe yarayacağını göstermez; δ bir varsayımdır (ADR-007), gerçek etki payı bilinmiyor.

