# Credit Coach demo v0: ne iddia ediyoruz, ne iddia etmiyoruz

> Kredi veren: tek fiyatlı kurgusal kredi veren. Demo; kimlik doğrulama, veritabanı ve denetim izi yok.

## İddia ettiklerimiz
- **Deterministik karar.** Aynı başvuru, aynı politika ve aynı model paketiyle aynı karar çıkar. Karar yolunda rastgelelik, LLM ya da açıklama yaklaşımı (LIME, SHAP, DiCE) yoktur. Karar katmanında eski bir karar bayt düzeyinde yeniden üretilebilir (hafta 3, golden set ve replay).
- **Yalnızca başvuru anında bilinen özellikler.** Fiyatlama alanları ve kredi sonrası alanlar manifestoda yasaktır ve sızıntı testleriyle denetlenir.
- **Zamana göre bölme, tek seferlik test.** Eğitim 2012-01..2014-12, kalibrasyon 2015-03..06, test 2015-09..12. Test dilimi bir kez çalıştırıldı (ham model AUC 0,6906; kalibre ECE 0,0025; `docs/week2_report.md`).
- **Modelin kalibre risk tahmini.** Venn-Abers aralığıyla verilir; onay eşiği kurgusal kredi verenin sabit getiri, kayıp ve hurdle varsayımından türetilir.
- **Plan = modele göre bir değişiklik.** Her plan, tüm özellik vektörü yeniden skorlanarak ve karar kuralından (onay) geçirilerek doğrulanır; eşiğin güvenli payla altına inmeyen, derin seviyede riski artıran ya da eğitim aralığı dışına çıkan plan seçilmez.
- **Aralık dışı başvuru değerlendirilmez.** Eğitimde görülmeyen değerler "değerlendirilemez" sayfasına gider; skor ve plan üretilmez.
- **Maliyet ve süre varsayımdır** ve her yerde "varsayım" etiketiyle gösterilir.
- **Her plan için gereken minimum etki payı ve dayanıklılık etiketi.** `min_phi` = (p_önce − kesim) / Δ, motorda hesaplanır (arayüz hesaplamaz); etiket GUCLU, KOSULLU ya da ZAYIF'tır. Eylemlerin kanıt sınıfı gösterilir: bakiye ve kullanım değişimi muhasebe özdeşliğidir (K), risk etkisi model ilişkisidir (M); kurum eylemi "karşı teklif" olarak etiketlenir.

## İddia etmediklerimiz
- Bir planın uygulanmasının gerçekte onay ya da daha düşük risk getireceğini. Nedensel etki doğrulanmadı; model bir ilişki ölçer.
- Gerçek bir kurumun onay oranını, fiyatlamasını ya da kârlılığını. Kredi veren kurgusaldır ve tek fiyatlıdır.
- Güncel (2015 sonrası) başvurular için kalibrasyonu.
- Bir kişinin planı yapabileceğini ya da yapma olasılığını (yürütme olasılığı ölçülmedi).
- GUCLU etiketli bir planın gerçekte işe yarayacağını. Etiket, modelin öngördüğü etkinin ne kadarının gerekli olduğunu söyler; gerçek etki payı bilinmiyor (`docs/demo_effect_share.md`).
- Alt gruplar arası adillik analizini ya da kredi mevzuatına uygunluğu. Bu sürümde yapılmadı.

## Bilinen sınırlar
- **Veri kapsamı.** Yalnızca LendingClub, 36 aylık krediler, 2012-01..2015-12 ABD. Reddedilenlerin sonucu gözlenmediği için seçilim yanlılığı vardır.
- **Zaman kayması.** Kalibrasyon ve gözlenen oranlar dönemden döneme kayar; sonuçlar bu aylar için ölçüldü.
- **Destek kontrolü.** Eğitim diliminin en küçük/en büyük değeri (kategorikte görülen değer kümesi) kullanılır; eğitimdeki uç değerler aralığı genişletir (ör. `revol_util` 892). Çok boyutlu destek denetlenmez.
- **Reddedilen başvurulara uygulanabilirlik doğrulanmadı.** LendingClub'ın reddedilen başvurularında DTI bakımından eğitim aralığının dışında kalanların oranı 2012-13'te %16,7, 2014-15'te %27,4'tür (iki dosyadaki DTI tanımlarının uyumu doğrulanmadı); risk skoru ölçeği 2013-11'den itibaren tutarlı olmadığı için karşılaştırılamadı, bu nedenle reddedilen müşterilere uygulanabilirlik doğrulanmamıştır (`docs/rejected_overlap.md`).
- **Plan oranı düşüktür.** Katalog iki eylemden oluşur; reddedilenlerin çoğunda plan çıkmaz (`docs/demo_portfolio_report.md`). Eylem eklenmedi.
- **Örnek vakalar.** Varsayılan δ = 0,012'de (ADR-007) 198 örnek kayıttan 4'ü GUCLU, 27'si KOSULLU, 6'sı ZAYIF etiketlidir; GUCLU ve KOSULLU örnek vakaları arayüzde vardır. Etiket dağılımı δ'ya duyarlıdır.
- **Güvenlik payı δ bir varsayımdır.** δ = 0,012, kalibrasyon ve boşluk aylarındaki en büyük aylık |kalibre ortalama PD − gözlenen oran| değerinin 0,001'e yukarı yuvarlanmasıyla türetilir (ADR-007); ölçülmüş bir kapsama değildir.
- **Dayanıklılık etiketleri δ'ya duyarlıdır.** Etiketlerin dayandığı güvenlik payı δ bir varsayımdır (ADR-007) ve etiket dağılımı ona bağlıdır: kalibrasyon dilimindeki reddedilenlerde δ = 0,02'den 0,012'ye inildiğinde GUCLU %0,1'den %1,1'e, KOSULLU %1,5'ten %10,0'a, ZAYIF %17,5'ten %8,0'a kayar (`docs/demo_delta_comparison.md`).
- **Etiket eşikleri varsayımdır.** GUCLU için gereken etki payı en çok 0,50, KOSULLU için en çok 0,75'tir; eşikler ölçülmedi ve yapılandırmadadır.
- **Model sınırı.** `loan_amnt` modelde kısıtsızdır; etkisinin yönü bilinmez ve yalnızca yeniden skorlamayla kabul edilir. `dti` güncellemesi kapalıdır; FICO değişmez kabul edilir.
- **Denetim izi bu sürümde yok.** `/score` ve `/batch` kayıt yazmaz; karar logu kapalıdır ve açılması reddedilir. Hafta 3'teki replay yalnızca karar katmanını kapsar, skor katmanını kapsamaz.
- **Demo sınırları.** Kimlik doğrulama yok, veritabanı yok, tek süreç. Toplu mod en çok 10.000 satır kabul eder.
