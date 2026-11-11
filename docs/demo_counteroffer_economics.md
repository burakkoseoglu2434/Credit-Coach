# Demo v0: kurum yolu karşı teklifinin beklenen fazla kârı (tanım; sayılar henüz hesaplanmadı)

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Bu bölüm sonuçlardan ÖNCE yazıldı ve commit'lendi; hesap bu tanıma göre yapılır, sonuç görüldükten sonra değiştirilmez.

## Tanım

**Kapsam.** Yalnızca kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi yüklenmez. Motor, politika (v1) ve katalog değişmez; plan arama ve etiket kuralı mevcut kuraldır.

**Aday.** v1 REJECTED (destek içi) kayıtlardan, kurum yolunun (yalnızca `loan_amount_reduction`) en ucuz planı geçerli olanlar. Geçerlilik ve dayanıklılık etiketi mevcut `p_high` kuralıyla belirlenir (`p_high_sonra < eşik − δ`, `min_phi` ve etiket eşikleri). Segmentler, kurum yolu planının kendi etiketine göre:

- (i) etiket GUCLU,
- (ii) etiket GUCLU veya KOSULLU,
- (iii) kurum yolu planı geçerli olan hepsi (GUCLU, KOSULLU, ZAYIF).

**İki ayrı tahmin, karıştırılmaz.**

- *Geçerlilik ve etiket* `p_high` ile belirlenir (üst sınır tahmini); bu raporda değiştirilmez.
- *Ekonomik değer* nokta tahminiyle (`p_point`) hesaplanır. Aşağıdaki formüldeki p, `p_high` değildir.

**Beklenen fazla kâr (USD), kayıt başına.**

`değer = L' × [ (1 − p) · getiri − p · temerrüt_kaybı − hurdle ]`

- L' = planın yeni kredi tutarı (USD).
- getiri = `configs/cost.yaml` `saglam_kredi_getirisi.mean`; temerrüt_kaybı = `temerrut_kaybi.mean`; hurdle = `asgari_marj + fon_maliyeti + isletme_gideri` toplamı (`decision.total_hurdle`). Üçü de yapılandırmadaki varsayımlardır ve değiştirilmez; birim funded_amnt oranıdır, kredi ömrü boyunca toplam.
- p = `p_point_önce − φ · Δ_point`, Δ_point = `p_point_önce − p_point_sonra` (planın nokta tahminindeki düşüş). φ = 0: p = p_point_önce; φ = 1: p = p_point_sonra. Formül olduğu gibi uygulanır; p kırpılmaz. Δ_point ≤ 0 olan kayıt sayısı ayrıca bildirilir.
- Reddetmenin değeri 0 alınır; değer, reddetmeye göre fazladır.

**Izgara.** φ ∈ {0; 0,25; 0,50; 0,75; 1,00} ve δ ∈ {0,012 (varsayılan), 0,03}. Aday kümesi ve etiketler δ'ya bağlıdır; her δ için ayrı hesaplanır.

**Kabul oranı.** Müşterinin teklifi kabul oranı 1 varsayılır. Tüm toplamlar kabul oranıyla doğrusal ölçeklenir (kabul oranı a ise toplam ve kayıt başına değer a ile çarpılır; kayıt sayısı ve ortalama L' bu varsayımda tanıma göre değişmez).

**Çıktı.** Her segment × φ × δ için: kayıt sayısı, ortalama L' (USD), toplam beklenen fazla kâr, kayıt başına değer. Segment × δ başına başa-baş φ: toplamın sıfır olduğu φ, ızgara noktaları arasında doğrusal enterpolasyonla; toplam φ'de doğrusaldır. Aralıkta işaret değişmiyorsa "yok" yazılır.

**Çapraz kontrol (yalnızca φ = 0).** Aynı hesap, p yerine kaydın GÖZLENEN sonucuyla (`target`: 1 = temerrüt, 0 = değil): `L' × [ (1 − y) · getiri − y · temerrüt_kaybı − hurdle ]`. Etiketler (gözlenen sonuç) yalnızca bu değerlendirme için kullanılır; plan seçimine, geçerliliğe ve etikete girmez. Bu, kaydın özgün tutarındaki gözlenen sonucunun L' tutarına uygulanmasıdır.
