# E-ticaret uplift doğrulaması — özet (2026-11-12)

Kaynaklar: [PLAN.md](PLAN.md), [E0_data_check.md](E0_data_check.md), [E1_hillstrom.md](E1_hillstrom.md), [E2_criteo.md](E2_criteo.md). Bu özet için yeni analiz, model eğitimi ya da test çalıştırması yapılmadı; tüm sayılar bu raporlardan alındı.

## 1. Amaç ve kapsam

Kredi hattında "önerilen hamlenin tahmin edilen etkisi" fikri doğrulanamadı: rastgele deney verisi yoktu ve sonuç 36 ay sonra gözlenir. Bu çalışma aynı fikri, tedavinin rastgele atandığı iki halka açık e-ticaret setinde sınadı: Hillstrom (e-posta, 64.000 müşteri) ve Criteo (reklam, 13.979.592 satır). Kapsam tek adımlı hamledir (bir kez gönder ya da gönderme). Eşikler sonuçlar görülmeden donduruldu; test kümeleri birer kez çalıştı ve kilitlendi.

> **Bu bölüm ne demek:** Neyin, hangi veriyle ve hangi disiplinle sınandığı.
>
> **Ne DEMEK DEĞİL:** Bu bir doğrulama çalışmasıdır, ürün iddiası değildir; kredi önerileri hakkında bir sonuç vermez.

## 2. Kapı sonuçları

| Kapı | Ölçüt | Ölçülen | Sonuç |
|---|---|---|---|
| E0 veri | 1–4: satır, tedavi payı, Pandera, denge | Hillstrom 64.000 satır; Criteo 13.979.592 satır, tedavi oranı 0,85000; Pandera kalan satır 0; en büyük \|SMD\| Hillstrom 0,0153, Criteo 0,0488 (`f3`) | geçti |
| E0 lisans | 5 | kullanıcı onayladı (ticari olmayan iç doğrulama) | geçti |
| E1 Hillstrom | 1 Qini alt sınırı > 0 | 0,002661 [0,000151; 0,004961] | geçti |
| | 2 Eğim ∈ [0,5; 1,5], alt sınır > 0 | 0,353 [−0,005; 0,688] | **kaldı** |
| | 3 Genel düzey farkı aralığı 0'ı içerir | −0,00148 [−0,01274; 0,01047] | geçti |
| E2 Criteo | 1 Qini alt sınırı > 0 | 0,003246 [0,003026; 0,003476] | geçti |
| | 2 Eğim ∈ [0,7; 1,3] | 0,648 [0,600; 0,699] | **kaldı** |
| | 3 En az 8/10 desil uyumlu | 8/10 | geçti |
| E3 değer | — | yapılmadı | — |

E3 neden yapılmadı: E2 testinden önce yazılan ön kayıt (PLAN bölüm 11), E2'de ölçüt 1 ya da 2'den biri kalırsa E3'ün yapılmayacağını söylüyordu. Ölçüt 2 kaldı; sonuç "hedefleme değeri bu veriyle gösterilemedi" olarak kaydedildi.

> **Bu tablo ne demek:** Her kapının dondurulmuş eşiklere göre sonucu ve ölçülen değerler (köşeli parantez: bootstrap %95 aralığı).
>
> **Ne DEMEK DEĞİL:** "Kaldı" modelin bilgi taşımadığını, "geçti" hamlenin başka bir yerde aynı farkı vereceğini göstermez.

## 3. Ne öğrendik / ne öğrenmedik

- **Sıralama bir miktar bilgi taşıyor:** iki sette de Qini alanının alt sınırı sıfırın üstünde. Hillstrom'da sınır sıfıra çok yakın (0,000151).
- **Kişi düzeyinde etki büyüklüğü iyimser tahmin ediliyor:** iki sette de kapı modelinin kalibrasyon eğimi 1'in altında (0,353 ve 0,648). Tahminler ölçülen farktan geniş yayılıyor; en üst desilde tahmin ölçülenden yüksek (Hillstrom 0,1308 / 0,0777; Criteo 0,09441 / 0,06213).
- **Sonuç model ailesine duyarlı:** Criteo'da kapıya girmeyen T ailesinin eğimi 0,910 [0,842; 0,979], ama genel düzeyi ölçülenden düşük (−0,00301 [−0,00366; −0,00241]). Seçim doğrulamada yapıldı ve değiştirilmedi.
- **Özellik dengesizliğine duyarlılık (ikincil, kapıya girmez):** Criteo'da $\hat p(x)$ ağırlığıyla kapı modelinin Qini alanı 0,003246'dan 0,001506'ya, genel `visit` farkı 0,01034'ten 0,00745'e iniyor. Ağırlıklı Qini için aralık **raporlanmadı** (nokta tahmini).
- **Öğrenmediğimiz:** hedeflemenin herkese göndermeye göre değer kattığı (E3 yapılmadı); bu farkların kâra dönüştüğü; kredi önerilerinin gerçek etkisi.

> **Bu bölüm ne demek:** Ölçülen farklar ile tahminlerin hangi yönlerde uyuştuğu ve uyuşmadığı.
>
> **Ne DEMEK DEĞİL:** Hamlenin bir müşteride şu etkiyi yaratacağı söylenemez; eğimin 1'in altında olması yalnızca bu iki test kümesinde tahminlerin ölçülen farka göre geniş yayıldığını gösterir.

## 4. Sınırlar

- Yalnızca iki halka açık set; tek adımlı etki; Hillstrom'da iki haftalık pencere.
- Criteo özellikleri anonim, birden çok testin birleşimi ve eşit olmayan alt örnekleme içeriyor; mutlak oranlar gerçek bir kampanyayı temsil etmez.
- Lisans: ticari olmayan iç doğrulama (Criteo CC BY-NC-SA 4.0 HF etiketi; Hillstrom lisansı doğrulanamadı).
- Criteo kapı modelinde test satırlarının %40'ı aynı tahmini paylaşıyor (6–10. desiller); bu desillerde sıralama bilgi taşımıyor.
- Hillstrom örneklemi küçük (test 12.802 satır, desil başına yaklaşık 430 kontrol); aralıklar geniş.
- E1 eski eşitlik kuralıyla (satır kimliği), E2 sabit anahtarla üretildi (PLAN 2.1 sonradan notu); Hillstrom dosyası tedaviye göre sıralı olmadığı için E1 etkilenmedi.
- ADR-008'de bölme yöntemi yanlış tarif edilmişti (satır kimliği karması; gerçekte seed'li tabakalı permütasyon); düzeltme 2026-11-13 sonradan notunda, kayıtlı karma koddan birebir yeniden üretildi (`SPLIT_CHECK.md`).
- Sonuçlar kredi kararlarına aktarılamaz; sıralı zincir (reklam → indirim → …) test edilmedi.

> **Bu bölüm ne demek:** Sonuçların hangi koşullarda geçerli olduğu.
>
> **Ne DEMEK DEĞİL:** Listelenmeyen bir sınırın olmadığını söylemez.

## 5. Sonraki adım adayları (karar yok)

Her biri yeni, ön kayıtlı bir plan gerektirir; bu belgede seçilmedi.

- Tahminleri ölçülen farka göre yeniden ölçekleme (kalibrasyon) yöntemini önceden tanımlayıp ayrı bir veri kümesinde sınamak.
- E3'ü (değer ve başa-baş etki payı) yalnızca Hillstrom'da, "E1 ölçüt 2 kalan model" etiketiyle ayrı bir ön kayıtla değerlendirmek.
- Lenta, X5 RetailHero gibi aday setlerde yeniden üretim.
- Eşit tahmin bloklarını azaltacak model ayarlarını önceden tanımlayıp doğrulamada sınamak.

> **Bu bölüm ne demek:** Çalışmanın açık bıraktığı sorulara olası devam yolları.
>
> **Ne DEMEK DEĞİL:** Bu adımların yapılacağı ya da sonuç vereceği anlamına gelmez.
