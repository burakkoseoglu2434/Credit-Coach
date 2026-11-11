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

## İddia etmediklerimiz
- Bir planın uygulanmasının gerçekte onay ya da daha düşük risk getireceğini. Nedensel etki doğrulanmadı; model bir ilişki ölçer.
- Gerçek bir kurumun onay oranını, fiyatlamasını ya da kârlılığını. Kredi veren kurgusaldır ve tek fiyatlıdır.
- Güncel (2015 sonrası) başvurular için kalibrasyonu.
- Bir kişinin planı yapabileceğini ya da yapma olasılığını (yürütme olasılığı ölçülmedi).
- Alt gruplar arası adillik analizini ya da kredi mevzuatına uygunluğu. Bu sürümde yapılmadı.

## Bilinen sınırlar
- **Veri kapsamı.** Yalnızca LendingClub, 36 aylık krediler, 2012-01..2015-12 ABD. Reddedilenlerin sonucu gözlenmediği için seçilim yanlılığı vardır.
- **Zaman kayması.** Kalibrasyon ve gözlenen oranlar dönemden döneme kayar; sonuçlar bu aylar için ölçüldü.
- **Destek kontrolü.** Eğitim diliminin en küçük/en büyük değeri (kategorikte görülen değer kümesi) kullanılır; eğitimdeki uç değerler aralığı genişletir (ör. `revol_util` 892). Çok boyutlu destek denetlenmez.
- **Plan oranı düşüktür.** Katalog iki eylemden oluşur; reddedilenlerin çoğunda plan çıkmaz (`docs/demo_portfolio_report.md`). Eylem eklenmedi.
- **Model sınırı.** `loan_amnt` modelde kısıtsızdır; etkisinin yönü bilinmez ve yalnızca yeniden skorlamayla kabul edilir. `dti` güncellemesi kapalıdır; FICO değişmez kabul edilir.
- **Denetim izi bu sürümde yok.** `/score` ve `/batch` kayıt yazmaz; karar logu kapalıdır ve açılması reddedilir. Hafta 3'teki replay yalnızca karar katmanını kapsar, skor katmanını kapsamaz.
- **Demo sınırları.** Kimlik doğrulama yok, veritabanı yok, tek süreç. Toplu mod en çok 10.000 satır kabul eder.
