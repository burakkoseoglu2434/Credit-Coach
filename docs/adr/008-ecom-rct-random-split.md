# ADR-008: E-ticaret uplift doğrulamasında rastgele bölme istisnası (RCT verisi)

Durum: **Kabul edildi (2026-11-11).** Veri açılmadan ve hiçbir sonuç görülmeden yazıldı.

## Bağlam
Depo kuralı (CLAUDE.md, ADR-002): bölme `issue_d` ile zamana göredir, rastgele bölme yasaktır.
Kural kredi verisi içindir: kredi başvuruları zamanla değişir ve model geleceğe uygulanır, bu yüzden
değerlendirme dönem kaymasını içermelidir.

E-ticaret uplift doğrulaması (`docs/ecom/PLAN.md`) Hillstrom ve Criteo Uplift setlerini kullanır.
İki sette de tedavi rastgele atanmıştır (RCT) ve **tarih alanı yoktur**; zamana göre bölme
uygulanamaz.

## Karar
1. Yalnızca rastgele atamalı deney verisinde (RCT) ve yalnızca `credit_coach.ecom` alt paketinde,
   **tabakalı rastgele bölme** kullanılır: eğitim / doğrulama / test = 0,6 / 0,2 / 0,2,
   tabaka = (tedavi × birincil sonuç), seed 20261111, atama satır kimliğinin sabit karmasıyla.

   *Sonradan (2026-11-13, düzeltme):* Gerçekte kullanılan yöntem tabakalı, seed'li
   permütasyondur: `e1_hillstrom.make_split` / `e2_criteo.make_split` →
   `uplift.stratified_split` (seed 20261111, `numpy.random.default_rng`; her tabakada satır
   kimlikleri karıştırılır, 0,6 / 0,2 / 0,2). Kayıtlı karmalar (Hillstrom `8bd4e53c…`, Criteo
   `c5fa21e7…`) bu yöntemle birebir yeniden üretildi (`docs/ecom/SPLIT_CHECK.md`). Yukarıdaki
   "satır kimliğinin sabit karmasıyla" ifadesi uygulamayı tarif etmiyordu. Test öncesi karma
   commit'i ve kilit bağları (`docs/ecom/test_run_*.lock`) değişmedi.
2. Test kümesi bir kez çalıştırılır; ayar yalnızca doğrulamada yapılır (PLAN bölüm 3.2).
3. Kredi verisi için zamana göre bölme kuralı **aynen geçerlidir**; bu ADR onu değiştirmez ve
   kredi koduna uygulanmaz.

## Sonuçlar
- **Zaman kayması ölçülmez.** Test kümesi eğitimle aynı dönemden gelir; bulunan uyum, modelin
  sonraki bir kampanyada ya da dönemde aynı kalacağını göstermez. Bu sınır her e-ticaret raporunda
  yazılır.
- Rastgele atama nedeniyle tedavi ve kontrol grupları her kümede karşılaştırılabilir kalır; bu,
  E0'da standartlaştırılmış ortalama farkıyla (SMD) denetlenir.
- Criteo birden çok testin birleşimidir ve test kimliği verilmez; rastgele bölme testleri
  kümelere karıştırır. Bu da kayma ölçülemeyeceğinin bir parçasıdır.

> **Bu ADR ne demek:** Tarih alanı olmayan iki RCT setinde, depodaki zaman bölmesi kuralına dar ve açık bir istisna.
>
> **Ne DEMEK DEĞİL:** Kredi verisinde rastgele bölmeye izin vermez; e-ticaret sonuçlarının zaman içinde sabit kalacağını göstermez.
