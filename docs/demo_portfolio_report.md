# Demo v0: portföy raporu (demo varsayılan δ = 0,012)

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Demo varsayılan δ = 0,012 (`configs/catalog/demo_v0.yaml`, `delta.deger`, varsayım); API ve arayüz bu değerle plan arar. Rapor sütunları: δ = 0 (band içi: etkin kesim eşik − band), δ = 0,012 (demo varsayılanı), δ = 0,03.

Kapsam: kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08). Onay eşiği (PD) 0.1092, band 0.0027. dti güncellemesi kapalı. Etiketler (gözlenen temerrüt) yalnızca değerlendirme içindir, karar yoluna girmez.

**Test dilimi (2015-09..12) bu raporda yeniden çalıştırılmadı.** Tek seferlik test sonuçları `docs/week2_report.md` içindedir (ham model AUC 0,6906; onay oranı 0,3860; onaylananlarda gözlenen temerrüt 0,0677). Test dilimi bir kez kullanıldı ve ayar için kullanılamaz.

Plan = en az bir yol türü için geçerli plan (ADR-006). δ = 0'da etkin kesim eşik − band'dır (yakınlık bandı karar kuralı R2 tarafından zaten uygulanır).

## 1. Karar dağılımı (politika v1)

| dilim | kayıt | destek dışı | onay | koşullu | ret | ret payı (destek içi) |
|---|---|---|---|---|---|---|
| kalibrasyon | 81136 | 6 | 28801 | 100 | 52229 | 64.4% |
| boşluk | 94456 | 6 | 34812 | 109 | 59529 | 63.0% |

> **Bu tablo ne demek:** v1 politikasının bu aylardaki başvuruları nasıl ayırdığı; sayılar karar sayısıdır.

> **Ne DEMEK DEĞİL:** Bu, bir kurumun gerçek onay oranı ya da güncel başvurular için bir tahmin değildir; model 2012-15 ABD verisiyle eğitildi ve eşik kurgusal tek fiyatlı kredi vereni temsil eder.

## 2. Geçerli plan oranı (reddedilenler içinde)

| dilim | δ | reddedilen | en az bir yolda plan | müşteri | karma | kurum | PLAN_YOK |
|---|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 52229 | 29.7% | 8.7% | 23.7% | 16.8% | 70.3% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | 52229 | 19.1% | 4.2% | 15.9% | 8.3% | 80.9% |
| kalibrasyon | δ = 0,03 | 52229 | 8.6% | 1.4% | 7.6% | 2.5% | 91.4% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 59529 | 30.0% | 9.1% | 23.9% | 17.2% | 70.0% |
| boşluk | δ = 0,012 (demo varsayılanı) | 59529 | 19.4% | 4.3% | 16.1% | 8.7% | 80.6% |
| boşluk | δ = 0,03 | 59529 | 8.9% | 1.5% | 7.8% | 2.7% | 91.1% |

> **Bu tablo ne demek:** Reddedilen kayıtların, katalogdaki iki eylemle modele göre eşiğin güvenli payla altına inen bir plana sahip olan payı.

> **Ne DEMEK DEĞİL:** Plan bulunması, kişinin bu değişikliği yapabileceği, yapacağı ya da sonucun gerçekleşeceği anlamına gelmez; etki doğrulanmadı ve model bir ilişki ölçer.

## 3. Yol dağılımı (kayıt başına hangi yol türlerinde plan var)

| dilim | δ | PLAN_YOK | customer | customer+hybrid | customer+hybrid+institution | hybrid | hybrid+institution | institution |
|---|---|---|---|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 70.3% | 0.5% | 4.0% | 4.3% | 8.4% | 7.0% | 5.5% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | 80.9% | 0.3% | 2.9% | 1.0% | 7.7% | 4.4% | 2.9% |
| kalibrasyon | δ = 0,03 | 91.4% | 0.1% | 1.1% | 0.1% | 4.9% | 1.4% | 0.9% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 70.0% | 0.5% | 3.9% | 4.6% | 8.3% | 7.0% | 5.6% |
| boşluk | δ = 0,012 (demo varsayılanı) | 80.6% | 0.3% | 2.8% | 1.2% | 7.7% | 4.4% | 3.0% |
| boşluk | δ = 0,03 | 91.1% | 0.1% | 1.2% | 0.2% | 4.9% | 1.5% | 1.0% |

> **Bu tablo ne demek:** Aynı kaydın birden çok yol türünde planı olabilir; sütunlar yol türü kümeleridir.

> **Ne DEMEK DEĞİL:** Yollar birbiriyle sıralanmadı; bir yolun diğerinden iyi olduğu anlamına gelmez.

## 4. Yol başına medyan USD maliyeti (varsayım)

| dilim | δ | müşteri | karma | kurum |
|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | 5,708 USD (n=4558) | 7,214 USD (n=12389) | 3,000 USD (n=8779) |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | 8,379 USD (n=2173) | 8,699 USD (n=8313) | 5,050 USD (n=4355) |
| kalibrasyon | δ = 0,03 | 11,119 USD (n=712) | 11,108 USD (n=3957) | 7,500 USD (n=1297) |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | 5,613 USD (n=5401) | 7,135 USD (n=14211) | 3,000 USD (n=10264) |
| boşluk | δ = 0,012 (demo varsayılanı) | 8,398 USD (n=2567) | 8,808 USD (n=9602) | 5,000 USD (n=5151) |
| boşluk | δ = 0,03 | 11,437 USD (n=876) | 11,185 USD (n=4631) | 7,500 USD (n=1607) |

> **Bu tablo ne demek:** Yolun en ucuz geçerli planının USD tutarının medyanı; tutar nakit çıkışı ya da karşılanmayan talep olarak varsayıldı.

> **Ne DEMEK DEĞİL:** Maliyet ölçülmedi; iki maliyet türü 1 USD = 1 USD varsayımıyla aynı birimde gösterildi. Gerçek bir başvuranın maliyetini göstermez.

## 5. Geçerli plan oranı, p_point − eşik kovalarına göre

| dilim | δ | kova (p_point − eşik) | reddedilen | geçerli plan oranı |
|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 3943 | 94.5% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 3855 | 85.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 3529 | 67.7% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 9757 | 40.1% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 11171 | 15.9% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 14143 | 3.0% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 5831 | 0.2% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0, 0,01) | 3943 | 76.4% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,01, 0,02) | 3855 | 58.1% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,02, 0,03) | 3529 | 41.2% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,03, 0,05) | 9757 | 22.4% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,05, 0,10) | 11171 | 8.0% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,10, 0,20) | 14143 | 1.3% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | >= 0,20 | 5831 | 0.1% |
| kalibrasyon | δ = 0,03 | [0, 0,01) | 3943 | 39.2% |
| kalibrasyon | δ = 0,03 | [0,01, 0,02) | 3855 | 25.9% |
| kalibrasyon | δ = 0,03 | [0,02, 0,03) | 3529 | 18.7% |
| kalibrasyon | δ = 0,03 | [0,03, 0,05) | 9757 | 9.1% |
| kalibrasyon | δ = 0,03 | [0,05, 0,10) | 11171 | 3.1% |
| kalibrasyon | δ = 0,03 | [0,10, 0,20) | 14143 | 0.5% |
| kalibrasyon | δ = 0,03 | >= 0,20 | 5831 | 0.0% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 4714 | 95.0% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 4526 | 84.0% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 4047 | 66.9% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 11067 | 40.1% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 12809 | 14.9% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 15908 | 3.3% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 6458 | 0.2% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0, 0,01) | 4714 | 76.6% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,01, 0,02) | 4526 | 57.2% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,02, 0,03) | 4047 | 41.1% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,03, 0,05) | 11067 | 22.6% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,05, 0,10) | 12809 | 7.5% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,10, 0,20) | 15908 | 1.5% |
| boşluk | δ = 0,012 (demo varsayılanı) | >= 0,20 | 6458 | 0.1% |
| boşluk | δ = 0,03 | [0, 0,01) | 4714 | 40.6% |
| boşluk | δ = 0,03 | [0,01, 0,02) | 4526 | 26.5% |
| boşluk | δ = 0,03 | [0,02, 0,03) | 4047 | 17.8% |
| boşluk | δ = 0,03 | [0,03, 0,05) | 11067 | 9.2% |
| boşluk | δ = 0,03 | [0,05, 0,10) | 12809 | 2.8% |
| boşluk | δ = 0,03 | [0,10, 0,20) | 15908 | 0.5% |
| boşluk | δ = 0,03 | >= 0,20 | 6458 | 0.0% |

> **Bu tablo ne demek:** Eşiğe uzaklık arttıkça planı olan kayıt payının nasıl değiştiği.

> **Ne DEMEK DEĞİL:** Kova, kişinin ne kadar çaba göstermesi gerektiğini ölçmez; yalnızca modelin bugünkü risk tahmininin eşiğe uzaklığıdır.

## 6. En kötü durum: planı olan reddedilenlerin ORİJİNAL gözlenen temerrüt oranı

| dilim | δ | kova | plan'lı reddedilen | gözlenen temerrüt |
|---|---|---|---|---|
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 3726 | 11.54% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 3278 | 12.69% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 2388 | 13.82% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 3911 | 14.70% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 1772 | 17.21% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 425 | 23.29% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 10 | 30.00% |
| kalibrasyon | δ = 0 (band içi: etkin kesim eşik − band) | tümü | 15510 | 13.91% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0, 0,01) | 3011 | 11.76% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,01, 0,02) | 2238 | 12.96% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,02, 0,03) | 1453 | 13.83% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,03, 0,05) | 2186 | 14.96% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,05, 0,10) | 898 | 15.92% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | [0,10, 0,20) | 190 | 25.79% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | >= 0,20 | 4 | 50.00% |
| kalibrasyon | δ = 0,012 (demo varsayılanı) | tümü | 9980 | 13.69% |
| kalibrasyon | δ = 0,03 | [0, 0,01) | 1545 | 11.65% |
| kalibrasyon | δ = 0,03 | [0,01, 0,02) | 1000 | 12.90% |
| kalibrasyon | δ = 0,03 | [0,02, 0,03) | 661 | 14.07% |
| kalibrasyon | δ = 0,03 | [0,03, 0,05) | 888 | 15.99% |
| kalibrasyon | δ = 0,03 | [0,05, 0,10) | 342 | 15.20% |
| kalibrasyon | δ = 0,03 | [0,10, 0,20) | 64 | 28.12% |
| kalibrasyon | δ = 0,03 | tümü | 4500 | 13.64% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0, 0,01) | 4477 | 11.46% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,01, 0,02) | 3803 | 11.36% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,02, 0,03) | 2708 | 13.74% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,03, 0,05) | 4433 | 14.73% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,05, 0,10) | 1904 | 17.07% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | [0,10, 0,20) | 530 | 19.06% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | >= 0,20 | 12 | 16.67% |
| boşluk | δ = 0 (band içi: etkin kesim eşik − band) | tümü | 17867 | 13.42% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0, 0,01) | 3610 | 11.02% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,01, 0,02) | 2590 | 11.24% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,02, 0,03) | 1664 | 14.42% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,03, 0,05) | 2499 | 14.85% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,05, 0,10) | 955 | 16.86% |
| boşluk | δ = 0,012 (demo varsayılanı) | [0,10, 0,20) | 244 | 16.39% |
| boşluk | δ = 0,012 (demo varsayılanı) | >= 0,20 | 5 | 0.00% |
| boşluk | δ = 0,012 (demo varsayılanı) | tümü | 11567 | 12.98% |
| boşluk | δ = 0,03 | [0, 0,01) | 1916 | 10.96% |
| boşluk | δ = 0,03 | [0,01, 0,02) | 1198 | 10.60% |
| boşluk | δ = 0,03 | [0,02, 0,03) | 720 | 14.17% |
| boşluk | δ = 0,03 | [0,03, 0,05) | 1020 | 13.73% |
| boşluk | δ = 0,03 | [0,05, 0,10) | 363 | 16.80% |
| boşluk | δ = 0,03 | [0,10, 0,20) | 79 | 16.46% |
| boşluk | δ = 0,03 | >= 0,20 | 3 | 0.00% |
| boşluk | δ = 0,03 | tümü | 5299 | 12.32% |

Karşılaştırma: onaylananların gözlenen temerrüt oranı.

| dilim | onaylanan | gözlenen temerrüt |
|---|---|---|
| kalibrasyon | 28801 | 6.78% |
| boşluk | 34812 | 6.41% |

> **Bu tablo ne demek:** Plan bulunan kayıtlar, plan uygulanmadan bugünkü hâlleriyle gözlenen temerrüt oranına sahiptir; plan bulunması, kayıtların güvenli olduğunu değil, modelin eşiğin altına inen bir değişiklik bulduğunu söyler.

> **Ne DEMEK DEĞİL:** Bu oran planın sonucu değildir: plan uygulanmış kişilerin sonuçları gözlenmedi. Orijinal oran, onaylananlarınkinden belirgin yüksek olduğu için planın etkisi doğrulanmış sayılmaz.

