# ADR-006: Demo v0 recourse tasarımı

Durum: **Kabul edildi** (2026-11-11; A ve B kararları aşağıda işlendi). Kapsam: demo v0, iki eylem. ADR-005'in dört eylemlik
kataloğunun demo için daraltılmış hâlidir; ADR-005 değişmez.

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri,
> kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

## Amaç ve dil
Reddedilen (onay eşiğinin üstünde) bir başvuru için "modele göre, şu değişiklikle bu profildeki
benzer kişilerin riski eşiğin altında kalır" diyebilen, tamamen deterministik bir tarama.
Çıktı bir ilişkidir (kanıt sınıfı M), sonuç vaadi değildir. Sayısal süre, maliyet ve yürütme
değerleri "varsayım" etiketlidir.

## 1. Katalog (yalnızca iki eylem)

`revolving_paydown` (sahip: müşteri) ve `loan_amount_reduction` (sahip: kurum; ADR-005'teki
`counteroffer_lower_amount`'ın demo adı). Diğer eylemler (`cure_delinquency`, `settle_collections`)
demoda yoktur. Seviyeler katalogdaki gibidir:

| Eylem | Seviye | Hedef | Süre (hafta, varsayım) |
|---|---|---|---|
| revolving_paydown | util_70 / util_50 / util_30 | `revol_util` hedefi 70 / 50 / 30 (yüzde) | 4-12 / 8-20 / 12-32 |
| loan_amount_reduction | amnt_90 / amnt_75 / amnt_50 | `loan_amnt` x 0,90 / 0,75 / 0,50, 100'e yuvarla | 0-1 |

Bir eylemden bir seviye seçilir. Bir plan en çok 2 eylemdir (config: `max_eylem`, varsayılan 2).

### 1.1 `revolving_paydown`: özellik güncellemeleri

Ölçülen ön koşul (eğitim dilimi, 306.462 kayıt): `total_bal_ex_mort >= revol_bal` ve
`tot_cur_bal >= total_bal_ex_mort` ihlali yok (yalnızca boş değerler farklı); `revol_util` ile
`revol_bal / total_rev_hi_lim x 100` farkının medyanı 0,03 puan, kayıtların %96'sında 1 puandan az.
Yani bakiye özdeşlikleri veriyle tutarlı.

Gösterim: `u`=mevcut `revol_util`, `h`=hedef, `B`=mevcut `revol_bal`, `Δ`=ödenen tutar.

| Özellik | Güncelleme | Tür |
|---|---|---|
| `revol_util` | `h` (yalnızca `u > h`) | özdeşlik (hedefin kendisi) |
| `revol_bal` | `B x h / u` | özdeşlik: limit sabit, oran ile ölçeklenir |
| `Δ` | `B - B x h / u` | özdeşlik (nakit çıkışı = bakiye farkı) |
| `total_bal_ex_mort` | `- Δ` (alt sınır 0, kırpılırsa "kırpıldı") | özdeşlik: revolving bakiye toplamın parçası |
| `tot_cur_bal` | `- Δ` (alt sınır 0, kırpılırsa "kırpıldı") | özdeşlik: aynı gerekçe |
| `dti` | `- 100 x m x Δ / (annual_inc / 12)` (alt sınır 0, kırpılırsa "kırpıldı") | **varsayım**, `m` = aylık asgari ödeme oranı = 0,02. **Varsayılan KAPALI** (`dti_guncelle: false`, muhafazakâr: dti değişmez). Açık varyant yalnızca duyarlılık raporunda (adım 3) |

Uygulanabilirlik: `u` ve `B` boş değil, `u > h`, `B > 0`. Aksi hâlde seviye uygulanmaz.
Uygulama koşulu varsayımı: ödeme müşterinin nakdinden yapılır, yeni borç açılmaz.

### 1.2 `loan_amount_reduction`: özellik güncellemeleri

| Özellik | Güncelleme | Tür |
|---|---|---|
| `loan_amnt` | `round(loan_amnt x çarpan, -2)`; sonuç `< 1000` ise seviye uygulanmaz | tanım |

Başka özellik güncellenmez. Veri sözlüğüne göre `dti` istenen krediyi içermez; bu bu çalışmada
**doğrulanmadı**, varsayımdır (aşağıda).

### 1.3 Bağlı alanlar: modelde olan ve olmayan
- `installment`: PRICING sınıfında, **yasak** ve model girdisi değil. Güncellenmez, hesaba girmez.
- `loan_to_income`: manifestoda **yok**, model girdisi değil. Eklenmez (yeni özellik = yeni model).
- `dti`, `revol_bal`, `total_bal_ex_mort`, `tot_cur_bal`: modelde var, yukarıdaki tabloda.

### 1.4 Formülü belirsiz alanlar (uydurma yok, güncellenmez, listede kalır)
| Alan | Durum |
|---|---|
| `fico_range_low/high` | Gerçekte kullanım azalınca skor değişir, ama formül ve bağımsız bir kaynak yok. Sabit tutulur. Model skoru görünce plan olduğundan farklı davranabilir. |
| `dti` formülü (`m`, gelir bölümü) | Asgari ödeme oranı ve ödemenin dti'ye girdiği varsayımdır, ölçülmedi. Bu yüzden varsayılan kapalı. |
| `dti` ve istenen kredi | Tanımın istenen krediyi dışladığı doğrulanmadı. |
| `total_rev_hi_lim`, `total_bc_limit`, `open_acc`, `total_acc`, `acc_open_past_24mths` | Hesap kapatılmaz, limit değişmez varsayılır. Doğrulanmadı. |
| `tot_cur_bal`, `total_bal_ex_mort` boşsa | Boş kalır (model boşu kendi işler), güncellenmez. Eğitimde oranlar %7,4 ve %2,0. |
| `loan_amnt` etkisinin yönü | Model bu özelliği **kısıtsız** öğrendi (`monotone.yaml`). Etki işareti bilinmiyor, bu yüzden yalnızca tam yeniden skorlama kabul eder. |

## 2. Kabul kriteri

Her aday plan için **tam vektör yeniden skorlanır**: eylem etkileri uygulanmış tüm 30'a yakın
özellik, aynı kalibratör ve modelden geçer. Kısayol veya türev tahmini yoktur.

Geçerli plan koşulları (hepsi sağlanmalı):
1. **Eşik koşulu:** `p_after < onay_esigi - δ`, `p_after = p_high` (karar A). `δ` config
   parametresi, varsayılan **0,02**, etiket "varsayım: ölçülmedi". **δ'nın anlamı:** dönem
   kayması ve model belirsizliği için bir güven payı varsayımıdır. Venn-Abers aralığı değildir:
   aralık zaten `p_high` içinde, δ onun üstüne konan ayrı bir paydır ve istatistiksel bir
   kapsama özelliği taşımaz (ADR-004 band'ı 0,0027).
2. **Derin seviye koşulu:** bir eylemin seviyeleri sığdan derine sıralıdır. Bir seviyenin
   `p_after` değeri **başlangıç PD'sinden** veya **aynı eylemin bir üst (daha sığ) seviyesinden**
   yüksekse o seviye geçersizdir ve hiçbir planda yer almaz. Çok eylemli planda `p_after`
   başlangıç PD'sinden yüksekse plan geçersizdir.
3. **Destek koşulu:** sonuç vektörü `support.yaml` içinde kalmalıdır (min/max). Dışına çıkan plan
   geçersizdir. Kırpılan alan "kırpıldı" işaretlenir, işaretsiz kırpma yoktur.
4. **Uygulanabilirlik:** her eylemin koşulu sağlanmalı.

**Karar A (kabul edildi): `p_after = p_high`.** Kabul edilen her planın sonuç vektörü
`decide_with_support()` ile APPROVED almak zorundadır; bu, kabul kriterinin 5. koşulu ve
property testlerinden biridir (invariant).

5. **Karar uyumu:** sonuç vektörü ve `p_after` üçlüsüyle `decide_with_support()` APPROVED vermeli
   (δ = 0'da yakınlık bandı R2/R3 devreye girebilir, o zaman plan geçersizdir).

## 3. Arama

Aday kümesi: boş plan hariç, tek eylem (3 + 3 = 6) ve iki eylem (3 x 3 = 9) olmak üzere **15
plan**. Hepsi taranır; budama yoktur (bu yüzden budamalı/budamasız denklik testi gerekmez).
Eylemler farklı özellik kümelerini oynattığı için etkiler birbirine girmez (sıra bağımsız,
testte doğrulanır).

Geçerli planlar yol tipine göre gruplanır. Her grupta **sıralama anahtarı**, küçükten büyüğe:
1. `maliyet_usd`, 2. `sure_ust` (hafta, varsayım), 3. eylem sayısı, 4. plan id (`eylem:seviye`
çiftlerinin sıralı birleşimi). Beraberlik kalmaz; aynı girdi aynı planı verir. Gruplar arasında
sıralama yoktur.

**Karar B (kabul edildi): maliyet USD, yollar arası sıralama YOK.** Maliyet her iki eylem için
USD ve tek değerdir: `revolving_paydown` = `Δ` (nakit çıkışı), `loan_amount_reduction` =
`loan_amnt - yeni_tutar` (karşılanmayan talep). Farklı kaynaklı iki maliyeti tek sıraya koymak bir
varsayım gerektirdiği için **yollar birbiriyle sıralanmaz**: üç yol tipi (`customer`, `hybrid`,
`institution`) için ayrı ayrı, kendi içindeki en ucuz geçerli plan gösterilir. Yol, eylemlerin
sahip kümesi ve eylem ailelerinden oluşan bir **imzadır**; imza yalnızca plan yapısına bağlıdır,
skor veya PD'ye bağlı değildir. Seçilen plan kendi yolunun (imzasının) en ucuz geçerli planıdır.
Süre: plan süresi = eylem sürelerinin **en büyüğü** (paralel yürütme varsayımı), alt/üst sınır
ayrı tutulur.

Yürütme olasılığı bu demoda **sıralamaya girmez**, rapora da yazılmaz (ölçülmedi).

Sonuç tipi kapalıdır: `PLAN` (yol başına bir plan: eylem/seviye listesi, USD maliyet, süre
aralığı, `p_after` üçlüsü, kırpılan alanlar) veya açık değer **`PLAN_YOK`**. Boş liste, `None` ya da istisna yoktur.

## 4. `PLAN_YOK` modu

Geçerli plan yoksa çıktı **yalnızca** şunları içerir (yol veya plan yok):
- `bagli_kisitlar`: kapalı listeden nedenler, eylem bazında: `UYGULANAMAZ` (koşul sağlanmıyor,
  örn. `revol_util` en düşük hedefin altında), `SEVIYE_GECERSIZ` (derin seviye koşulu), `DESTEK_DISI`,
  `ETKI_YETERSIZ` (en iyi seviye kombinasyonu bile eşik − δ'ya ulaşmıyor; yalnızca etiket, sayı yok).
- `esige_uzaklik`: **mevcut** `p_point - onay_esigi` (ölçülmüş bugünkü durum, gelecek değil).

Çıktıda yol, plan, süre, maliyet, tarih, `p_after` veya "şu kadar iyileşirse" gibi **hiçbir**
sayısal vaat yoktur. En iyi durum `p_after` değeri yalnızca iç hesapta tutulur, dışarı verilmez.
Yeniden başvuru tarihi bu demoda yoktur (katalog süreleri varsayım; ADR-005 limited mod, ayrı iş).

## 5. Dürüst beklenti
Demoda iki kaldıraç var: kullanım oranı ve tutar. Reddedilenlerin önemli bir kısmında
`PLAN_YOK` çıkması **beklenen ve dürüst** sonuçtur; sonuçları güzelleştirmek için eylem
eklenmez. Adım 3 (kalibrasyon dilimi) bunu sayıyla gösterecek.

## 6. Adımlar (onaydan sonra)
2. `Scorer` arayüzü (`skorla(vektor) -> (p_low, p_point, p_high)`; test için sentetik monoton
   skorlayıcı, gerçek için model + kalibratör), motor, property testleri: aynı girdi aynı plan,
   geçersiz plan asla seçilmez, `PLAN_YOK`'ta sayısal vaat çıkmaz, kabul edilen plan `decide()`'dan
   APPROVED alır.
3. Kalibrasyon diliminde (test dilimi kullanılmaz) reddedilenler için δ ∈ {0; 0,01; 0,02; 0,03}:
   geçerli planı olan oran, eylem dağılımı, medyan maliyet. Sayılar yorumsuz.

## 7. Kapsam dışı
Politika v2 / `ret_esigi` / `plan_available` bağlama, golden v2, çok boyutlu destek, tutarlılık
kuralları, `cure_delinquency` ve `settle_collections`, yeniden başvuru tarihi.
