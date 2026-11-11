# Demo v0: kurum yolu karşı teklifinin beklenen fazla kârı

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

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

## Sonuçlar

Test dilimi kullanılmadı. Müşteri kabul oranı 1 varsayılır; toplamlar ve kayıt başına değer kabul oranıyla doğrusal ölçeklenir. Kayıt sayıları tam sayıdır, USD değerleri yuvarlanmıştır.

## 1. Parametreler

| parametre | değer | kaynak |
|---|---|---|
| getiri | 0.1666 | `configs/cost.yaml`, `saglam_kredi_getirisi.mean` (varsayım) |
| temerrüt kaybı | 0.3519 | `configs/cost.yaml`, `temerrut_kaybi.mean` (varsayım) |
| hurdle (toplam) | 0.1100 | `configs/cost.yaml`, asgari marj + fon maliyeti + işletme gideri (tez varsayımı) |
| birim değer, p = 0 | 0.0566 | getiri − hurdle |
| başa-baş p | 0.1092 | (getiri − hurdle) / (getiri + temerrüt kaybı) |

> **Bu tablo ne demek:** Hesapta kullanılan getiri, temerrüt kaybı ve hurdle; yapılandırmadan okundu.

> **Ne DEMEK DEĞİL:** Bu değerler ölçülmüş fiyatlama değil, varsayımdır; gerçek bir kurumun getirisini ya da kaybını göstermez.

## 2. Aday kümesi

| dilim | v1 REJECTED (destek içi) | δ = 0.012 (varsayılan): kurum yolu planı geçerli | δ = 0.03: kurum yolu planı geçerli |
|---|---|---|---|
| kalibrasyon | 52229 | 4355 | 1297 |
| boşluk | 59529 | 5151 | 1607 |

> **Bu tablo ne demek:** Dilim başına v1 tarafından reddedilen kayıt sayısı ve δ başına, kurum yolu (karşı teklif) planı geçerli olan kayıt sayısı.

> **Ne DEMEK DEĞİL:** Aday kümesi bir öneri listesi değildir; müşterinin teklifi kabul edeceği anlamına gelmez.

## 3. Segment × φ × δ

| dilim | δ | segment | φ | kayıt | ort. L' (USD) | toplam beklenen fazla kâr (USD) | kayıt başına (USD) |
|---|---|---|---|---|---|---|---|
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 0.00 | 280 | 6,980 | -7,312 | -26.1 |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 0.25 | 280 | 6,980 | 3,162 | 11.3 |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 0.50 | 280 | 6,980 | 13,636 | 48.7 |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 0.75 | 280 | 6,980 | 24,110 | 86.1 |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 1.00 | 280 | 6,980 | 34,584 | 123.5 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.00 | 3257 | 9,131 | -196,010 | -60.2 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.25 | 3257 | 9,131 | -49,619 | -15.2 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.50 | 3257 | 9,131 | 96,773 | 29.7 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.75 | 3257 | 9,131 | 243,164 | 74.7 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1.00 | 3257 | 9,131 | 389,555 | 119.6 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.00 | 4355 | 9,374 | -426,077 | -97.8 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.25 | 4355 | 9,374 | -188,579 | -43.3 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.50 | 4355 | 9,374 | 48,919 | 11.2 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.75 | 4355 | 9,374 | 286,416 | 65.8 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1.00 | 4355 | 9,374 | 523,914 | 120.3 |
| kalibrasyon | 0.03 | (i) GUCLU | 0.00 | 0 | - | 0 | - |
| kalibrasyon | 0.03 | (i) GUCLU | 0.25 | 0 | - | 0 | - |
| kalibrasyon | 0.03 | (i) GUCLU | 0.50 | 0 | - | 0 | - |
| kalibrasyon | 0.03 | (i) GUCLU | 0.75 | 0 | - | 0 | - |
| kalibrasyon | 0.03 | (i) GUCLU | 1.00 | 0 | - | 0 | - |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 0.00 | 112 | 7,507 | -4,203 | -37.5 |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 0.25 | 112 | 7,507 | 2,015 | 18.0 |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 0.50 | 112 | 7,507 | 8,232 | 73.5 |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 0.75 | 112 | 7,507 | 14,450 | 129.0 |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 1.00 | 112 | 7,507 | 20,668 | 184.5 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 0.00 | 1297 | 10,029 | -122,091 | -94.1 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 0.25 | 1297 | 10,029 | -32,661 | -25.2 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 0.50 | 1297 | 10,029 | 56,769 | 43.8 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 0.75 | 1297 | 10,029 | 146,199 | 112.7 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 1.00 | 1297 | 10,029 | 235,629 | 181.7 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 0.00 | 345 | 7,868 | -9,847 | -28.5 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 0.25 | 345 | 7,868 | 4,512 | 13.1 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 0.50 | 345 | 7,868 | 18,871 | 54.7 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 0.75 | 345 | 7,868 | 33,231 | 96.3 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 1.00 | 345 | 7,868 | 47,590 | 137.9 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.00 | 3910 | 9,205 | -231,552 | -59.2 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.25 | 3910 | 9,205 | -55,514 | -14.2 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.50 | 3910 | 9,205 | 120,525 | 30.8 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.75 | 3910 | 9,205 | 296,563 | 75.8 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1.00 | 3910 | 9,205 | 472,601 | 120.9 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.00 | 5151 | 9,416 | -477,499 | -92.7 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.25 | 5151 | 9,416 | -202,156 | -39.2 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.50 | 5151 | 9,416 | 73,187 | 14.2 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.75 | 5151 | 9,416 | 348,530 | 67.7 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1.00 | 5151 | 9,416 | 623,872 | 121.1 |
| boşluk | 0.03 | (i) GUCLU | 0.00 | 0 | - | 0 | - |
| boşluk | 0.03 | (i) GUCLU | 0.25 | 0 | - | 0 | - |
| boşluk | 0.03 | (i) GUCLU | 0.50 | 0 | - | 0 | - |
| boşluk | 0.03 | (i) GUCLU | 0.75 | 0 | - | 0 | - |
| boşluk | 0.03 | (i) GUCLU | 1.00 | 0 | - | 0 | - |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 0.00 | 168 | 7,348 | -6,790 | -40.4 |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 0.25 | 168 | 7,348 | 2,502 | 14.9 |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 0.50 | 168 | 7,348 | 11,795 | 70.2 |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 0.75 | 168 | 7,348 | 21,087 | 125.5 |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 1.00 | 168 | 7,348 | 30,380 | 180.8 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 0.00 | 1607 | 9,893 | -142,973 | -89.0 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 0.25 | 1607 | 9,893 | -34,594 | -21.5 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 0.50 | 1607 | 9,893 | 73,785 | 45.9 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 0.75 | 1607 | 9,893 | 182,165 | 113.4 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 1.00 | 1607 | 9,893 | 290,544 | 180.8 |

> **Bu tablo ne demek:** Her segment, φ ve δ için kayıt sayısı, ortalama yeni tutar, nokta tahminiyle toplam beklenen fazla kâr ve kayıt başına değer; reddetmenin değeri 0 alındı.

> **Ne DEMEK DEĞİL:** Gerçekleşen kâr değildir; p_point = p_önce − φ·Δ_point varsayımına ve cost.yaml varsayımlarına bağlıdır, φ bilinmeyen bir etki payıdır.

## 4. Başa-baş φ

| dilim | δ | segment | kayıt | başa-baş φ |
|---|---|---|---|---|
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 280 | 0.175 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3257 | 0.335 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 4355 | 0.449 |
| kalibrasyon | 0.03 | (i) GUCLU | 0 | - (segment boş) |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 112 | 0.169 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 1297 | 0.341 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 345 | 0.171 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3910 | 0.329 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 5151 | 0.434 |
| boşluk | 0.03 | (i) GUCLU | 0 | - (segment boş) |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 168 | 0.183 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 1607 | 0.330 |

> **Bu tablo ne demek:** Segment ve δ başına toplam beklenen fazla kârın sıfır olduğu φ; ızgara noktaları arasında doğrusal enterpolasyon.

> **Ne DEMEK DEĞİL:** Gerçek etki payının bu değeri aşacağı ya da aşmayacağı anlamına gelmez; tek başına bir karar kuralı değildir.

## 5. Çapraz kontrol: φ = 0, p_point ile gözlenen sonuç

| dilim | δ | segment | kayıt | ort. p_point (önce) | gözlenen temerrüt oranı | toplam, p_point (φ = 0) | toplam, gözlenen | kayıt başına, p_point | kayıt başına, gözlenen |
|---|---|---|---|---|---|---|---|---|---|
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 280 | 0.1169 | 0.1464 | -7,312 | -44,720 | -26.1 | -159.7 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3257 | 0.1217 | 0.1240 | -196,010 | -349,927 | -60.2 | -107.4 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 4355 | 0.1285 | 0.1323 | -426,077 | -591,096 | -97.8 | -135.7 |
| kalibrasyon | 0.03 | (i) GUCLU | 0 | - | - | 0 | 0 | - | - |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 112 | 0.1190 | 0.1607 | -4,203 | -29,767 | -37.5 | -265.8 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 1297 | 0.1262 | 0.1334 | -122,091 | -219,299 | -94.1 | -169.1 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 345 | 0.1169 | 0.1362 | -9,847 | -144,948 | -28.5 | -420.1 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3910 | 0.1216 | 0.1128 | -231,552 | -166,259 | -59.2 | -42.5 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 5151 | 0.1277 | 0.1192 | -477,499 | -437,436 | -92.7 | -84.9 |
| boşluk | 0.03 | (i) GUCLU | 0 | - | - | 0 | 0 | - | - |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 168 | 0.1197 | 0.0655 | -6,790 | 20,515 | -40.4 | 122.1 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 1607 | 0.1261 | 0.1164 | -142,973 | -147,884 | -89.0 | -92.0 |

> **Bu tablo ne demek:** φ = 0'da aynı değer formülünün, modelin nokta tahmini ile kaydın gözlenen sonucu (etiketler yalnızca değerlendirme için) kullanılarak hesaplanmış hâli yan yana.

> **Ne DEMEK DEĞİL:** Gözlenen sonuç kaydın özgün kredi tutarındaki sonucudur, L' tutarında bir sonucu ölçmez; iki sütunun yakınlığı etki payı hakkında bilgi vermez.

## 6. Δ_point ≤ 0 olan kayıtlar

| dilim | δ | segment | kayıt | Δ_point ≤ 0 olan kayıt | ort. Δ_point |
|---|---|---|---|---|---|
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 280 | 0 | 0.0441 |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3257 | 0 | 0.0382 |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 4355 | 0 | 0.0444 |
| kalibrasyon | 0.03 | (i) GUCLU | 0 | 0 | - |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 112 | 0 | 0.0574 |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 1297 | 0 | 0.0522 |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 345 | 0 | 0.0443 |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3910 | 0 | 0.0383 |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 5151 | 0 | 0.0438 |
| boşluk | 0.03 | (i) GUCLU | 0 | 0 | - |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 168 | 0 | 0.0583 |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 1607 | 0 | 0.0526 |

> **Bu tablo ne demek:** Planın nokta tahmininde düşüş göstermeyen (Δ_point ≤ 0) kayıt sayısı ve ortalama Δ_point; formül bu kayıtlara da olduğu gibi uygulandı.

> **Ne DEMEK DEĞİL:** Bu sayı etiket ya da geçerlilik kuralının bir parçası değildir; o kural p_high üzerindedir ve burada değiştirilmedi.

