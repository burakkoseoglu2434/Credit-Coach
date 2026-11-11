# Demo v0: dayanıklılık etiketi dağılımı (demo varsayılan δ = 0,02)

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Demo varsayılan δ = 0,02 (`configs/catalog/demo_v0.yaml`, `delta.deger`, varsayım); API ve arayüz bu değerle plan arar. Rapor sütunları: δ = 0 (band içi: etkin kesim eşik − band), δ = 0,02 (demo varsayılanı), δ = 0,03.

Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi kullanılmadı. Reddedilen = v1 REJECTED (destek içi). dti güncellemesi kapalı. Eşik 0.1092, band 0.0027.

## 1. Kayıt başına en güçlü yolun etiketi (reddedilenler içinde)

| dilim | δ | reddedilen | PLAN_YOK | GUCLU | KOSULLU | ZAYIF |
|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 52229 | 36719 (70.3%) | 2497 (4.8%) | 4576 (8.8%) | 8437 (16.2%) |
| kalibrasyon | δ = 0,02 (demo varsayılanı) | 52229 | 42249 (80.9%) | 57 (0.1%) | 798 (1.5%) | 9125 (17.5%) |
| kalibrasyon | δ = 0,03 | 52229 | 47729 (91.4%) | 1 (0.0%) | 230 (0.4%) | 4269 (8.2%) |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 59529 | 41662 (70.0%) | 2985 (5.0%) | 5251 (8.8%) | 9631 (16.2%) |
| boşluk | δ = 0,02 (demo varsayılanı) | 59529 | 47964 (80.6%) | 74 (0.1%) | 1028 (1.7%) | 10463 (17.6%) |
| boşluk | δ = 0,03 | 59529 | 54230 (91.1%) | 0 (0.0%) | 327 (0.5%) | 4972 (8.4%) |

> **Bu tablo ne demek:** Her reddedilen kayıt için, planı olan yollar içinde en güçlü etiketin dağılımı; planı olmayanlar PLAN_YOK'ta sayılır.

> **Ne DEMEK DEĞİL:** GUCLU, planın gerçekte işe yarayacağı anlamına gelmez; yalnızca modelin öngördüğü etkinin yarısı ya da daha azının yeterli olduğunu söyler. Gerçek etki payı bilinmiyor.

## 2. Yol türüne göre etiket dağılımı

| dilim | δ | yol | planı olan kayıt | GUCLU | KOSULLU | ZAYIF |
|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | customer | 4558 | 799 (17.5%) | 1759 (38.6%) | 2000 (43.9%) |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | hybrid | 12389 | 1591 (12.8%) | 3274 (26.4%) | 7524 (60.7%) |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | institution | 8779 | 1198 (13.6%) | 3638 (41.4%) | 3943 (44.9%) |
| kalibrasyon | δ = 0,02 (demo varsayılanı) | customer | 2173 | 11 (0.5%) | 149 (6.9%) | 2013 (92.6%) |
| kalibrasyon | δ = 0,02 (demo varsayılanı) | hybrid | 8313 | 30 (0.4%) | 502 (6.0%) | 7781 (93.6%) |
| kalibrasyon | δ = 0,02 (demo varsayılanı) | institution | 4355 | 29 (0.7%) | 382 (8.8%) | 3944 (90.6%) |
| kalibrasyon | δ = 0,03 | customer | 712 | 0 (0.0%) | 35 (4.9%) | 677 (95.1%) |
| kalibrasyon | δ = 0,03 | hybrid | 3957 | 1 (0.0%) | 143 (3.6%) | 3813 (96.4%) |
| kalibrasyon | δ = 0,03 | institution | 1297 | 0 (0.0%) | 112 (8.6%) | 1185 (91.4%) |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | customer | 5401 | 953 (17.6%) | 2074 (38.4%) | 2374 (44.0%) |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | hybrid | 14211 | 1902 (13.4%) | 3763 (26.5%) | 8546 (60.1%) |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | institution | 10264 | 1454 (14.2%) | 4285 (41.7%) | 4525 (44.1%) |
| boşluk | δ = 0,02 (demo varsayılanı) | customer | 2567 | 12 (0.5%) | 214 (8.3%) | 2341 (91.2%) |
| boşluk | δ = 0,02 (demo varsayılanı) | hybrid | 9600 | 38 (0.4%) | 663 (6.9%) | 8899 (92.7%) |
| boşluk | δ = 0,02 (demo varsayılanı) | institution | 5150 | 40 (0.8%) | 512 (9.9%) | 4598 (89.3%) |
| boşluk | δ = 0,03 | customer | 876 | 0 (0.0%) | 41 (4.7%) | 835 (95.3%) |
| boşluk | δ = 0,03 | hybrid | 4631 | 0 (0.0%) | 193 (4.2%) | 4438 (95.8%) |
| boşluk | δ = 0,03 | institution | 1607 | 0 (0.0%) | 168 (10.5%) | 1439 (89.5%) |

> **Bu tablo ne demek:** Her yol türünün en ucuz geçerli planının etiketi; yalnızca o yolda planı olan kayıtlar sayılır.

> **Ne DEMEK DEĞİL:** Yollar birbiriyle sıralanmadı; bir yol türünde çok GUCLU etiketin olması o yolun diğerinden iyi olduğunu göstermez.

## 3. Etiket eşikleri

| etiket | koşul (min_phi) | durum |
|---|---|---|
| GUCLU | ≤ 0.50 | varsayım |
| KOSULLU | > 0.50 ve ≤ 0.75 | varsayım |
| ZAYIF | > 0.75 | varsayım |

> **Bu tablo ne demek:** Etiketin hangi minimum etki payı aralığına karşılık geldiği (yapılandırmadan okunur).

> **Ne DEMEK DEĞİL:** Eşikler ölçülmedi; insan kararıdır ve varsayımdır.

