# E-ticaret uplift doğrulama planı (taslak, onay bekliyor)

Durum: **PLAN**. Bu belge kod, veri indirme ya da hesap içermez. Kapı ölçütleri (bölüm 6) kullanıcı onayından sonra, hiçbir sonuç görülmeden dondurulur; dondurulduktan sonra değiştirilirse değişiklik belgeye tarih ve gerekçeyle "sonradan" etiketiyle yazılır.

Yazım tarihi: 2026-11-11. Dal: `ecom-uplift-plan` (kaynak: `origin/main`, c8ec459).

> **Bu belge ne demek:** Kredi hattında doğrulanamayan bir fikrin (önerilen hamlenin tahmin edilen etkisi) rastgele deneyle toplanmış halka açık e-ticaret verilerinde nasıl sınanacağının ön kaydı.
>
> **Ne DEMEK DEĞİL:** Bir ürün iddiası, bir kâr vaadi ya da kredi önerilerinin işe yaradığına dair kanıt değildir. E-ticaret sonuçları kredi kararlarına aktarılmaz.

---

## 0. Bağlam ve sınırlar

- Credit Coach kredi demosu donduruldu. Kredi politikası (`configs/policy`), katalog (`configs/catalog`), `configs/cost.yaml`, `docs/CLAIMS.md` ve mevcut raporlar **değişmez**. Bu çalışmanın kodu kredi koduna bağımlı olmaz; ortak yardımcılar gerekirse kopyalanmaz, yalnızca okunur (ör. `configs/forbidden_phrases.json`).
- Kredide önerilerin gerçek etkisi ölçülemedi: rastgele deney verisi yok ve sonuç 36 ay sonra gözlenir. E-ticarette tedavinin rastgele atandığı halka açık veri setleri var; burada **tahmin edilen fark** ile **kontrol grubuyla ölçülen fark** yan yana konabilir.
- Kapsam: **tek adımlı hamle** (bir müşteriye bir kez bir şey yapmak ya da yapmamak). Sıralı zincir neden dışarıda: bölüm 7.

> **Bu bölüm ne demek:** Çalışmanın neyi değiştirmediği ve neden e-ticaret verisine bakıldığı.
>
> **Ne DEMEK DEĞİL:** E-ticaret verisinde görülen bir uyumun kredi verisinde de olacağını söylemez; iki alanın tedavisi, sonucu ve süresi farklıdır.

---

## 1. Veri seti envanteri

Kaynaklara 2026-11-11'de bakıldı. Erişilemeyen ya da iki kaynağın çeliştiği her nokta "doğrulanamadı" diye yazıldı; E0 kapısında dosyanın kendisinden yeniden kontrol edilir.

### 1.1 Hillstrom (MineThatData E-Mail Analytics and Data Mining Challenge, 2008)

| Başlık | Değer | Kaynak |
|---|---|---|
| Boyut | 64.000 müşteri (son 12 ayda alışveriş yapmış) | [MineThatData blog, 2008-03](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html) |
| Özellikler (8) | `recency` (son alışverişten bu yana ay), `history_segment` (geçen yıl harcama dilimi), `history` (geçen yıl harcama, $), `mens`, `womens` (geçen yıl ilgili kategoriden alım, 0/1), `zip_code` (Urban/Suburban/Rural), `newbie` (son 12 ayda yeni, 0/1), `channel` (geçen yıl alım kanalı) | aynı |
| Tedavi | `segment`: Mens E-Mail / Womens E-Mail / No E-Mail; her biri **rastgele** 1/3 | aynı |
| Sonuçlar (e-posta sonrası 2 hafta) | `visit` (0/1), `conversion` (0/1), `spend` ($) | aynı |
| Lisans / kullanım şartı | **doğrulanamadı** — kaynak sayfada lisans ya da şart yazmıyor | aynı; ayrıca [TFDS katalog](https://www.tensorflow.org/datasets/catalog/hillstrom) |
| Dönüşüm/ziyaret oranları | **doğrulanamadı** (bu aşamada veri açılmadı; E0'da ölçülür) | — |
| Bilinen sınırlar | Tek kampanya, tek ülke (ABD olduğu varsayılır, **doğrulanamadı**), 2 haftalık pencere; maliyet ve marj alanı yok; küçük örneklem (bir kol ≈ 21.300); `conversion` seyrek olduğu için desil bazında güç düşük | — |

### 1.2 Criteo Uplift Prediction Dataset

| Başlık | Değer | Kaynak |
|---|---|---|
| Boyut | 13.979.592 satır | [Hugging Face `criteo/criteo-uplift`](https://huggingface.co/datasets/criteo/criteo-uplift), [TFDS katalog](https://www.tensorflow.org/datasets/catalog/criteo) |
| Çelişki | Aynı kartın açıklamasında "25M rows" (TFDS'de 25.309.483) geçiyor; hangi sürüme ait olduğu **doğrulanamadı**. Plan 13.979.592 satırlık dosyayı hedefler; E0'da sayılır | aynı |
| Özellikler | `f0`–`f11` (12 sayısal, anonim, değerleri rastgele izdüşümle dönüştürülmüş) | HF kartı |
| Tedavi | `treatment` (1 = reklam hedeflemesine açık, 0 = rastgele dışlanmış kontrol); tedavi oranı ≈ 0,85 (TFDS: 0,846) | HF kartı, TFDS |
| Maruz kalma | `exposure`: tedavi grubunda reklamı gerçekten görüp görmediği. Rastgele atanan değişken bu değil, `treatment` | HF kartı |
| Sonuçlar | `visit` (ortalama ≈ 0,047), `conversion` (ortalama ≈ 0,0029); **gelir/harcama alanı yok** | HF kartı |
| Toplanma | Birden çok artımlılık (incrementality) testinin birleşimi; her testte nüfusun rastgele bir bölümü reklamdan dışlanmış. Gizlilik için **eşit olmayan** alt örnekleme yapılmış; bu yüzden özgün artımlılık düzeyi buradan çıkarılamaz | HF kartı; [Diemert ve ark., arXiv:2111.10106](https://arxiv.org/abs/2111.10106) |
| Lisans | HF etiketi **CC BY-NC-SA 4.0** (ticari olmayan, aynı lisansla paylaşım). Criteo AI Lab'ın birincil sayfasına bu ortamdan erişilemedi → birincil kaynaktan **doğrulanamadı**. Not: arXiv sayfasındaki CC BY-NC-ND makalenin lisansıdır, verinin değil | HF kartı |
| Sürüm | HF kartında sürüm yazmıyor; "v2.1" adı ikincil kaynaklarda geçiyor → **doğrulanamadı** | — |
| Atıf şartı | Diemert, Betlei, Renaudin, Amini (2018), "A Large Scale Benchmark for Uplift Modeling", AdKDD & TargetAd @ KDD | HF kartı |
| Bilinen sınırlar | Özellikler yorumlanamaz; birden çok testin birleşimi olduğu için tedavi oranı ve temel oran testten teste değişebilir ve test kimliği verilmiyor; eşit olmayan alt örnekleme yüzünden mutlak oranlar gerçek kampanyayı temsil etmez; maliyet ve gelir yok | — |

### 1.3 Sonraki adaylar (bu plana DAHİL DEĞİL)

Lenta (BTL kampanyası), X5 RetailHero, MegaFon (sentetik uplift), Open Bandit Dataset (ZOZOTOWN, bandit günlükleri). Alanları, boyutları ve lisansları bu aşamada **doğrulanmadı**; yalnızca isim olarak listelenir.

> **Bu bölüm ne demek:** Hangi alanların, hangi tedavi ve sonuç tanımlarının kullanılacağı ve bunların hangi kaynağa dayandığı.
>
> **Ne DEMEK DEĞİL:** Lisansın bu kullanıma izin verdiğinin hukuki teyidi değildir (bkz. bölüm 9, soru 5). "Doğrulanamadı" yazan değerler tahmin edilmedi; E0'da dosyadan ölçülür.

### 1.4 `configs/ecom_data_source.yaml` şablonu (E0'da oluşturulur; şimdi yalnızca tasarım)

```yaml
# Dış veri kaynakları (e-ticaret doğrulama). Dosyalar depoya KOPYALANMAZ.
# Yol bu makineye aittir; sha256 açılmış CSV içeriğinin SHA-256 değeridir.
hillstrom:
  ad: MineThatData E-Mail Analytics Challenge (2008)
  kaynak_url: https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html
  indirme_tarihi: null        # E0'da doldurulur
  yol: null
  sha256: null
  boyut_bayt: null
  satir: null                 # beklenen 64000
  lisans: dogrulanamadi
  sutunlar: [recency, history_segment, history, mens, womens, zip_code, newbie, channel, segment, visit, conversion, spend]
criteo_uplift:
  ad: Criteo Uplift Prediction Dataset
  kaynak_url: https://huggingface.co/datasets/criteo/criteo-uplift
  surum: dogrulanamadi
  indirme_tarihi: null
  yol: null
  sha256: null
  gz_sha256: null
  boyut_bayt: null
  satir: null                 # beklenen 13979592
  lisans: CC-BY-NC-SA-4.0     # HF etiketi; birincil kaynakta E0'da teyit
  atif: "Diemert, Betlei, Renaudin, Amini (2018), AdKDD & TargetAd @ KDD"
  sutunlar: [f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, treatment, conversion, visit, exposure]
bolme:
  seed: 20261111
  oranlar: {egitim: 0.6, dogrulama: 0.2, test: 0.2}
  tabaka: [treatment, birincil_sonuc]
```

---

## 2. Soruların operasyonelleştirilmesi

### 2.1 Gösterim

- $T_i \in \{0,1\}$ tedavi, $Y_i$ sonuç, $X_i$ özellikler; $p = P(T=1)$ deney tasarımından bilinir (Hillstrom: 0,5 seçilen iki kol içinde; Criteo: eğitim kümesinde ölçülen oran, E0'da sabitlenir).
- $\hat\tau(x)$: modelin tahmin ettiği koşullu fark, $\hat\tau(x) = \hat\mu_1(x) - \hat\mu_0(x)$.
- Gözlenen fark (bir küme $S$ için): $\tau^{obs}_S = \bar Y_{S,T=1} - \bar Y_{S,T=0}$.
- Tüm metrikler **test kümesinde**, test satırları $\hat\tau$'ya göre azalan sıralanarak hesaplanır; eşitlikler satır kimliğine göre bozulur (deterministik).
- Bootstrap: $B = 1000$, sabit seed, tedavi ve kontrol kendi içinde yeniden örneklenir (tabakalı); %95 aralık yüzdelik yöntemiyle (2,5 ve 97,5). Model yeniden eğitilmez; aralık test örneklemesinin belirsizliğini verir.

### 2.2 Soru 1 — Tahmin edilen fark ölçülen farkla uyuşuyor mu?

**(a) Sıralama: Qini eğrisi ve alanı.** Üst $\phi$ oranında ($\phi \in \{0{,}01, 0{,}02, \dots, 1\}$): $n_t(\phi), n_c(\phi)$ kişi sayıları, $R_t(\phi), R_c(\phi)$ sonuç toplamları.

$$Q(\phi) = R_t(\phi) - R_c(\phi)\,\frac{n_t(\phi)}{n_c(\phi)}$$

Rastgele sıralamanın doğrusu $Q_{rnd}(\phi) = \phi\,Q(1)$. Qini alanı (yamuk kuralı, 100 noktada):

$$\text{Qini} = \frac{1}{N}\sum_{k=1}^{100}\Big[Q(\phi_k) - Q_{rnd}(\phi_k)\Big]\,\Delta\phi$$

$N$ test kümesi boyutudur (ölçek bağımsızlığı için). AUUC de aynı ızgarada $U(\phi) = \big(\tfrac{R_t}{n_t} - \tfrac{R_c}{n_c}\big)(n_t+n_c)$ ile raporlanır; kapı ölçütü Qini'dir.

**(b) Kalibrasyon: desil tablosu.** Test satırları $\hat\tau$'ya göre 10 eşit sayılı desile ($d = 1..10$) ayrılır.

$$\bar{\hat\tau}_d = \frac{1}{|S_d|}\sum_{i\in S_d}\hat\tau(x_i),\qquad \tau^{obs}_d = \bar Y_{d,T=1}-\bar Y_{d,T=0},\qquad \Delta_d = \bar{\hat\tau}_d - \tau^{obs}_d$$

Her $\Delta_d$ için bootstrap %95 aralığı. Özet ölçü **kalibrasyon eğimi** $\beta$: 10 noktada, $|S_d|$ ağırlıklı, sabit terimli doğrusal regresyon $\tau^{obs}_d = \alpha + \beta\,\bar{\hat\tau}_d$; aralığı bootstrap ile. $\beta = 1$ tam uyum, $\beta < 1$ tahminlerin ölçülen farktan geniş yayıldığını gösterir. Ayrıca genel düzey: $\overline{\hat\tau}$ ile $\tau^{obs}_{test}$ farkı ve aralığı.

### 2.3 Soru 2 — "Hiçbir şey yapma" kuralı herkese göndermeye göre değer katıyor mu?

Değer birimi: müşteri başına net değer $v_i = m\cdot Y_i - c\cdot\pi(x_i)$ ($m$ sonuç başına marj, $c$ hamle başına maliyet; bölüm 4). Bir politika $\pi(x)\in\{0,1\}$'in test kümesindeki değeri, tedavi rastgele atandığı için ters olasılık ağırlığıyla:

$$\hat V(\pi) = \frac{1}{N}\sum_{i}\left[\frac{\pi(x_i)\,T_i}{p} + \frac{(1-\pi(x_i))(1-T_i)}{1-p}\right]\big(m\,Y_i - c\,\pi(x_i)\big)$$

Kıyaslanan üç politika:

| Politika | Tanım |
|---|---|
| Herkese gönder | $\pi_{hep}(x) = 1$ |
| Hiçbirine gönderme | $\pi_{hic}(x) = 0$ |
| Modelle hedefle ("hiçbir şey yapma" kuralıyla) | $\pi_{mod}(x) = \mathbb 1\big[m\,\hat\tau(x) - c > 0\big]$ ve destek dışı satırlarda $\pi_{mod}=\pi_{hep}$ (bölüm 5) |

Metrik: $\Delta V = \hat V(\pi_{mod}) - \hat V(\pi_{hep})$ ve $\hat V(\pi_{mod}) - \hat V(\pi_{hic})$, eşleştirilmiş bootstrap %95 aralığıyla (aynı bootstrap örneğinde üç politika birlikte hesaplanır). Ek: hedeflenen oran $\bar\pi_{mod}$ ve dışarıda bırakılan kişilerde ölçülen fark $\tau^{obs}_{\pi_{mod}=0}$ (kural doğru kişileri mi dışlıyor?).

### 2.4 Soru 3 — Etki tahminin yarısı kadar çıksa hamle kârlı kalır mı?

Hedeflenen küme $H = \{i : \pi_{mod}(x_i)=1\}$. Etki payı $s$ (gerçek farkın tahmine oranı) için tahmini kişi başı kâr:

$$\Pi(s) = s\,m\,\overline{\hat\tau}_H - c,\qquad s^* = \frac{c}{m\,\overline{\hat\tau}_H}\ \ (\text{başa-baş etki payı})$$

Ölçülen oran: $r = \tau^{obs}_H / \overline{\hat\tau}_H$, bootstrap aralığıyla. Ölçülen kişi başı kâr: $\Pi^{obs} = m\,\tau^{obs}_H - c$.

Raporlanan: $s \in \{1;\ 0{,}75;\ 0{,}5;\ 0{,}25\}$ için $\Pi(s)$; $s^*$; $r$ ve aralığı; $\Pi^{obs}$ ve aralığı. Soru 3'ün iki parçası: (i) **plan düzeyi**: $s^* \le 0{,}5$ mi (tahmin yarıya inse de pozitif mi)? (ii) **gerçeklik kontrolü**: ölçülen $r$'nin aralığı $s^*$'ın üstünde mi? Bu, kredideki başa-baş etki payı analizinin karşılığıdır; farkı, $r$'nin burada gözlenebilmesidir.

Not: $\pi_{mod}$ zaten $\hat\tau$'ya göre seçildiği için $\overline{\hat\tau}_H$ yukarı yanlı olabilir (seçim etkisi); $r$ bu yanlılığı da içerir ve ayrıca raporlanır.

> **Bu bölüm ne demek:** Üç sorunun hangi formülle, hangi kümede, hangi belirsizlik aralığıyla sayıya dönüştürüleceği.
>
> **Ne DEMEK DEĞİL:** Formüller bir sonucu önceden belirlemez; $m$ ve $c$ varsayımdır ve politika değeri onlara bağlıdır. Bootstrap aralığı modelin yeniden eğitilmesinden doğan belirsizliği içermez.

---

## 3. Deney tasarımı

### 3.1 Kümeler ve bölme

- **Hillstrom birincil karşılaştırma:** Womens E-Mail (T=1) ve No E-Mail (T=0) satırları (≈ 42.700). Mens E-Mail kolu ikincil karşılaştırmadır ve kapı ölçütüne girmez (bölüm 9, soru 2).
- **Criteo:** `treatment` rastgele atanan değişkendir; analiz atamaya göre yapılır (intention-to-treat). `exposure` model girdisi ya da tedavi tanımı olarak **kullanılmaz** (atamadan sonra oluşur, sızıntı olur).
- **Birincil sonuç:** her iki sette `visit` (Hillstrom'da değer hesabı için `spend` ayrıca kullanılır; Criteo'da değer hesabı `conversion` üzerinden). Bkz. bölüm 9, soru 3.
- **Bölme:** eğitim / doğrulama / test = 0,6 / 0,2 / 0,2; tabaka = (tedavi × birincil sonuç), böylece her kümede tedavi oranı ve sonuç oranı korunur. Seed 20261111. Bölme satır kimliğinin sabit bir karmasıyla atanır ve kimlik listesi (dosya değil, karması) `configs/ecom_data_source.yaml`'a yazılır.
- **Zaman bölmesi yok:** iki sette de tarih alanı yok. Depo kuralı "bölme `issue_d` ile zamana göredir, rastgele bölme yasaktır" kredi verisi içindir; burada uygulanamaz. Bu istisna ancak kullanıcı onayı ve bir ADR ile geçerli olur (bölüm 9, soru 1).

### 3.2 Test kümesi bir kez çalışır

- Tüm ayar (hiperparametre, model seçimi, eşik) **yalnızca doğrulama kümesinde** yapılır.
- Test değerlendirmesi tek bir komutla çalışır; çalıştığında `docs/ecom/test_run_<set>.lock` dosyasına commit kimliği, veri SHA-256'ı, bölme karması ve zaman yazılır. Kilit varsa komut ikinci kez çalışmayı reddeder. Kilit dosyası commit'lenir.
- Test sonucundan sonra yapılan her değişiklik "sonradan" etiketiyle ayrı bölümde raporlanır; kapı kararını değiştirmez.

### 3.3 Model ailesi (en çok 2)

| Model | Tanım | Gerekçe |
|---|---|---|
| **A. İki modelli yaklaşım (T-learner)** | $\hat\mu_1, \hat\mu_0$: her kolda ayrı `HistGradientBoostingClassifier` (scikit-learn, sabit `random_state`); $\hat\tau = \hat\mu_1 - \hat\mu_0$ | En basit, en yaygın referans; mevcut hattaki "olasılık modeli + fark" düşüncesinin doğrudan karşılığı; olasılık çıktısı kalibrasyon tablosuyla doğrudan kıyaslanır |
| **B. Dönüştürülmüş sonuç (transformed outcome) regresyonu** | $Z_i = Y_i\,\frac{T_i - p}{p(1-p)}$ hedefiyle tek bir `HistGradientBoostingRegressor`; $E[Z\mid X] = \tau(X)$ | Doğrudan farkı öğrenir; $p$ deney tasarımından bilindiği için yansız; Criteo'daki 0,85/0,15 dengesizliğini ağırlıkla ele alır; ek kütüphane gerektirmez |

- Neden uplift ağacı ya da X/R-learner değil: ek bağımlılık (ör. `causalml`) ve belirlenimcilik denetimi maliyeti; iki aile, soru 1'i "yöntem seçimine duyarlı mı?" diye sınamak için yeterli. Uplift ağacı park listesindedir.
- Ayar ızgarası doğrulamada, en çok 12 kombinasyon (öğrenme hızı × yaprak sayısı × iterasyon), ölçüt doğrulama Qini'si. Seçilen ayar, test çalışmadan önce bu belgeye ek olarak yazılır.
- Belirlenimcilik: aynı veri + seed iki kez çalıştırıldığında $\hat\tau$ bit düzeyinde aynı olmalı (E1'de test). LLM, DiCE, LIME, KernelSHAP kullanılmaz.

> **Bu bölüm ne demek:** Hangi satırların hangi kümeye gideceği, modelin ne zaman ayarlanıp ne zaman bir kez sınanacağı ve hangi iki model ailesinin neden seçildiği.
>
> **Ne DEMEK DEĞİL:** Seçilen iki ailenin en iyi uplift yöntemleri olduğunu söylemez; amaç en yüksek skoru bulmak değil, tahmin edilen ve ölçülen farkın uyuşmasını sınamaktır.

---

## 4. Değer ve maliyet varsayımları

**Kural (veriye bakmadan yazıldı):** $m$ ve $c$ veri açılmadan önce bu belgede sabitlenir; veriye bakılarak değiştirilmez. Her değer **varsayım** etiketlidir. Tek nokta yerine ızgara raporlanır; kapı E3 yalnızca kullanıcının onayladığı **birincil hücrede** değerlendirilir (bölüm 9, soru 4).

### 4.1 Hillstrom (gelir alanı var)

| Parametre | Izgara | Etiket |
|---|---|---|
| Brüt marj oranı $g$ (harcamanın yüzdesi) | 0,20 / 0,30 / 0,40 | varsayım |
| E-posta başına maliyet $c$ ($) | 0,01 / 0,10 / 0,50 | varsayım (0,50 kupon/ek maliyet senaryosu) |
| Değer sonucu | $m\,Y_i := g\cdot \text{spend}_i$ (yani $m=g$, $Y=\text{spend}$) | tanım |
| Önerilen birincil hücre | $g = 0{,}30$, $c = 0{,}10$ | **varsayım, onay bekliyor** |

### 4.2 Criteo (gelir alanı yok)

Mutlak değer anlamsız olduğundan (alt örnekleme ve anonimlik) yalnızca **oran** kullanılır: $k = c/m$, dönüşüm başına değere göre hamle maliyeti. Başa-baş koşulu $\hat\tau_{conv}(x) > k$.

| Parametre | Izgara | Etiket |
|---|---|---|
| $k = c/m$ | 0,0001 / 0,0003 / 0,001 / 0,003 / 0,01 | varsayım |
| Önerilen birincil hücre | $k = 0{,}001$ | **varsayım, onay bekliyor** |

Dürüstlük notu: HF kartındaki ortalama dönüşüm oranı (≈ 0,0029) bu ızgara yazılmadan önce görüldü. Izgara bu yüzden geniş (iki büyüklük mertebesi) tutuldu; birincil hücrenin seçimi bu bilgiden bağımsız değildir ve raporda böyle yazılır.

> **Bu bölüm ne demek:** Politika değeri ve kâr hesabında kullanılacak marj ve maliyetin, sonuç görülmeden seçilmiş varsayım ızgarası.
>
> **Ne DEMEK DEĞİL:** Bu sayılar gerçek bir şirketin marjı ya da e-posta/reklam maliyeti değildir; bir hücrede "kârlı" çıkan sonuç başka hücrelerde ya da gerçek bir kampanyada aynı çıkmayabilir.

---

## 5. Mevcut hattan taşınanlar ve karşılıkları

| Kredideki fikir | E-ticaret karşılığı | Not |
|---|---|---|
| Destek dışı kontrolü (`configs/support.yaml`) | Test satırının her özelliği eğitim kümesinin [%0,5; %99,5] yüzdelik aralığında mı; değilse `DESTEK_DISI`. Bu satırlarda model hedeflemez, $\pi_{mod} = \pi_{hep}$ (varsayılan iş davranışı). Oran raporlanır | RCT'de tedavi açısından ortak destek zaten var; kontrol özellik uzayı içindir |
| "Hiçbir şey yapma" kuralı | $m\,\hat\tau(x) - c \le 0$ ise gönderme ($\hat\tau \le 0$ olanlar kendiliğinden dışarıda) | Soru 2'nin konusu |
| Güvenlik payı | İkincil politika $\pi_{mod}^{0.5}(x) = \mathbb 1[0{,}5\,m\,\hat\tau(x) - c > 0]$; yalnızca raporlanır, kapıya girmez | Kredideki δ'nın karşılığı |
| Etki payı duyarlılığı | $s$ ızgarası, $s^*$, ölçülen $r$ (bölüm 2.4) | Fark: burada $r$ ölçülebilir |
| "Ne demek / ne DEMEK DEĞİL" rapor formatı | Her tablo ve şekil altında iki satır; `docs/ecom/*.md` | Bu belgede uygulandı |
| Yasaklı ifade taraması | `configs/forbidden_phrases.json` aynen; bu belge taramaya eklendi; ileride `docs/ecom/*.md` tümü | Liste değiştirilmez |
| Belirlenimcilik, sabit seed, Pandera şeması, SHA-256 ile veri kaydı | Aynı | — |
| Sonuçlar görülmeden ölçüt yazma (pilot protokolü alışkanlığı) | Bölüm 6 | — |

**Taşınmayanlar ve nedeni**

| Kredideki parça | Neden taşınmıyor |
|---|---|
| Kredi politikası, onay kuralı, temerrüt kalibrasyonu | Farklı karar ve sonuç; donduruldu |
| Öneri (recourse) kataloğu ve monoton kısıtlar | Kredide hamleyi müşteri yapar (özelliğini değiştirir); burada hamleyi şirket yapar (e-posta/reklam). Criteo özellikleri anonim, monotonluk tanımlanamaz |
| Zamana göre bölme | Tarih alanı yok (bölüm 3.1) |
| PostgreSQL, FastAPI uçları, UI | Doğrulama çalışması; servis gerekmiyor |
| `cost.yaml` | Kredi maliyetidir; e-ticaret varsayımları bölüm 4'te ayrı |

> **Bu bölüm ne demek:** Kredi hattındaki hangi denetim ve rapor alışkanlıklarının burada hangi biçimde yeniden kurulacağı.
>
> **Ne DEMEK DEĞİL:** Kredi kodunun yeniden kullanılacağını ya da e-ticaret sonuçlarının kredi kurallarını değiştireceğini söylemez.

---

## 6. Kapılar (onay için önerilen ölçütler)

Toplam süre hedefi: **9 iş günü** (1–2 hafta). Her kapı ayrı PR; bir kapı kalırsa sonraki kapı kullanıcı onayı olmadan başlamaz.

### E0 — Veri ve lisans doğrulaması (1 gün)

- **Soru:** Elimizdeki dosyalar belgelenen kaynakla aynı mı, randomizasyon dosyada görünüyor mu ve lisans bu çalışmaya izin veriyor mu?
- **Görülebilir çıktı:** `configs/ecom_data_source.yaml` (dolu), `docs/ecom/E0_data_check.md` (sayılar, denge tablosu, lisans notu), Pandera şeması, rastgele bölme ADR'si.
- **Geçti ölçütü (hepsi):**
  1. Hillstrom satır = 64.000; her `segment` payı 1/3 ± 0,01.
  2. Criteo satır = 13.979.592 (ya da kullanıcı onaylı başka sürüm sayısı); tedavi oranı 0,846 ± 0,005.
  3. Pandera şeması satırların %100'ünde geçer (eksik değer, tür, değer aralığı).
  4. Denge: her özellik için T/C standartlaştırılmış ortalama farkı |SMD| < 0,05 (Hillstrom: Womens ve No E-Mail arasında; Criteo: tüm set).
  5. Lisans notu yazıldı ve kullanıcı onayladı (Criteo NC şartı; Hillstrom için şart bulunamadıysa bu açıkça yazıldı).
- **Durdurma kuralı:** 1–4'ten biri kalırsa modelleme yapılmaz; fark raporlanır, kullanıcıya sorulur. 5 onaylanmazsa ilgili set çıkarılır.

### E1 — Hillstrom (3 gün)

- **Soru:** Küçük ve yorumlanabilir sette tahmin edilen fark, ölçülen farkla sıralama ve düzey olarak uyuşuyor mu?
- **Görülebilir çıktı:** `docs/ecom/E1_hillstrom.md` — Qini eğrisi, desil tablosu ($\bar{\hat\tau}_d$, $\tau^{obs}_d$, $\Delta_d$, aralıklar), kalibrasyon eğimi, politika değeri tablosu, belirlenimcilik testi, test kilidi.
- **Geçti ölçütü (doğrulamada seçilen tek model, testte; birincil sonuç `visit`):**
  1. Qini alanının bootstrap %95 alt sınırı > 0.
  2. Kalibrasyon eğimi $\hat\beta \in [0{,}5;\ 1{,}5]$ ve bootstrap alt sınırı > 0.
  3. Genel düzey: $\overline{\hat\tau} - \tau^{obs}_{test}$ farkının %95 aralığı 0'ı içerir.
- **Güç notu:** Test ≈ 8.500 satır, desil başına kol başına ≈ 425 kişi; desil aralıkları geniş olacak. Bu yüzden desil bazında tek tek ölçüt yok; ölçüt eğim ve genel düzeydir.
- **Durdurma kuralı:** Ölçüt 1 kalırsa E2 yine yapılabilir (büyük örneklem), ancak yalnızca kullanıcı onayıyla; test yeniden çalıştırılmaz, model değiştirilmez.

### E2 — Criteo'da yeniden üretim (3 gün)

- **Soru:** Aynı tasarım, büyük ve farklı tedavi oranlı bir sette aynı sonucu veriyor mu?
- **Görülebilir çıktı:** `docs/ecom/E2_criteo.md` — E1 ile aynı tablolar, iki modelin yan yana sonucu, bellek/süre notu, test kilidi.
- **Geçti ölçütü (birincil sonuç `visit`):**
  1. Qini alanının bootstrap %95 alt sınırı > 0.
  2. Kalibrasyon eğimi $\hat\beta \in [0{,}7;\ 1{,}3]$ (örneklem büyük olduğu için E1'den dar).
  3. En az 8/10 desilde $|\Delta_d| \le 0{,}25\cdot|\tau^{obs}_{test}|$ ya da $\Delta_d$'nin aralığı 0'ı içerir.
- **Durdurma kuralı:** Bellek yetmezse belgede önceden tanımlı deterministik alt örnek (satır kimliği karmasına göre ilk %25) kullanılır ve raporda yazılır; başka değişiklik yapılmaz. Ölçütlerden biri kalırsa E3 yalnızca Hillstrom için, kullanıcı onayıyla yapılır.

### E3 — Değer analizi ve rapor (2 gün)

- **Soru:** Birincil maliyet hücresinde modelle hedefleme ("hiçbir şey yapma" kuralı dahil) herkese göndermeye göre ölçülen net değerde fark yaratıyor mu ve fark etki tahminin yarısında da pozitif kalıyor mu?
- **Görülebilir çıktı:** `docs/ecom/E3_value.md` — üç politikanın $\hat V$ tablosu ve tüm ızgara, $s^*$, $r$, $\Pi^{obs}$, özet ve "ne demek / ne DEMEK DEĞİL"; yasaklı ifade taraması geçer.
- **Geçti ölçütü (her set için ayrı karar, birincil hücrede):**
  1. Soru 2: $\Delta V = \hat V(\pi_{mod}) - \hat V(\pi_{hep})$ bootstrap %95 alt sınırı > 0.
  2. Soru 3 (plan): $s^* \le 0{,}5$.
  3. Soru 3 (gerçeklik): ölçülen $r$'nin %95 alt sınırı $\ge s^*$.
- **Sonuç dili:** Üçü geçerse "bu varsayımlar altında ölçülen fark pozitif"; aralık 0'ı içerirse "fark gösterilemedi"; üst sınır < 0 ise "ölçülen değer kaybı". Kalan ölçüt de bir sonuçtur ve aynı ağırlıkla raporlanır.
- **Durdurma kuralı:** E3'ten sonra yeni model, yeni maliyet hücresi ya da yeni veri seti eklenmez; bunlar yeni bir plan gerektirir.

> **Bu bölüm ne demek:** Her adımın tek sorusu ve sonuç görülmeden yazılmış sayısal geçti/kaldı eşikleri (öneri).
>
> **Ne DEMEK DEĞİL:** Eşikler bilimsel bir standart değildir, bu çalışma için seçilmiş karar kurallarıdır; bir kapının geçmesi hamlenin başka bir şirkette ya da kredide işe yarayacağını göstermez.

---

## 7. Karmaşıklık bütçesi ve park listesi

**Bütçe:** 2 veri seti, 2 model ailesi, 1 birincil sonuç, 1 birincil maliyet hücresi, 4 kapı, ≈ 9 iş günü. Yeni bağımlılık yok (scikit-learn, pandas/duckdb, pandera zaten var).

**Bilerek yapılmayanlar**

| Konu | Neden |
|---|---|
| Sıralı zincir (reklam → indirim → …) | Aday setlerin hiçbirinde ardışık adımlar ayrı ayrı rastgele atanmamış; ikinci adımın etkisi birinci adımın sonucuna bağlıdır ve bunu ölçmek ardışık randomizasyon (SMART tasarımı) ya da dinamik tedavi rejimi/çevrimdışı politika değerlendirmesi gerektirir. Bu, hem veri hem yöntem olarak ayrı bir çalışmadır ve 1–2 haftalık bütçeye sığmaz |
| Uplift ağacı/orman, X/R/DR-learner | İki aile soru 1 için yeterli; ek bağımlılık ve belirlenimcilik denetimi |
| Canlı sistem, API ucu, UI | Doğrulama çalışması |
| Kimlik doğrulama, kullanıcı hesabı | Gerek yok |
| Gerçek müşteri verisi | Yalnızca halka açık setler |
| Hukuk/KVKK ayrıntıları | Lisans notu E0'da; hukuki değerlendirme kapsam dışı |
| Lenta, X5, MegaFon, Open Bandit | Sonraki aday (bölüm 1.3) |
| Çok kollu seçim (Mens vs Womens hangisi) | Tek hamle var/yok kararıyla sınırlı |

> **Bu bölüm ne demek:** Kapsamın bilinçli olarak dar tutulduğu ve neyin neden dışarıda kaldığı.
>
> **Ne DEMEK DEĞİL:** Park edilen konuların önemsiz olduğunu ya da ileride yapılacağını söylemez.

---

## 8. Riskler ve sınırlar

| Risk / sınır | Etkisi | Azaltma |
|---|---|---|
| Criteo özellikleri anonim ve izdüşümlü | Hangi müşteri tipinin dışarıda bırakıldığı yorumlanamaz; destek dışı kontrolü yalnızca sayısal | Yorum Hillstrom'da; Criteo'da yalnızca sayısal uyum |
| Criteo birden çok testin birleşimi, test kimliği yok | Bir testin baskın olması sonuçları ona bağlayabilir; tedavi oranı testler arasında değişiyorsa $p$ tek sayı değildir ve IPW yanlı olabilir | E0'da özelliklere göre tedavi oranı dengesi (SMD) kontrol edilir; sınır raporda yazılır |
| Eşit olmayan alt örnekleme | Mutlak oranlar ve değerler gerçek kampanyayı temsil etmez | Yalnızca $k=c/m$ oranı kullanılır |
| Tek adımlı etki, kısa pencere (Hillstrom 2 hafta) | Uzun dönem ya da tekrarlanan gönderimin etkisi ölçülmez | İddia tek adım ve pencereyle sınırlı |
| Tedavi atama mekanizması sete özgü | Bir e-posta kampanyasında ya da reklam dışlamasında görülen uyum başka hamleye taşınmaz | Sonuçlar set ve hamle adıyla raporlanır |
| Hillstrom küçük | Desil aralıkları geniş, ölçütler zayıf güçlü | E2 büyük örneklemle tekrar |
| Seçim yanlılığı ($\overline{\hat\tau}_H$) | Hedeflenen grupta tahmin şişebilir | $r$ ayrıca raporlanır |
| Lisans (NC-SA, Hillstrom belirsiz) | Ticari ürünleşmeye engel olabilir | Bölüm 9, soru 5 |
| **İddia sınırı** | Bu bir **doğrulama çalışmasıdır, ürün iddiası değildir**; sonuçlar "tahmin edilen fark" ve "ölçülen fark" diliyle yazılır, "hamle şu etkiyi yaratır" türü kesin ifade ve kâr vaadi dili kullanılmaz | Yasaklı ifade taraması + gözden geçirme |

> **Bu bölüm ne demek:** Sonuçların hangi koşullarda yanıltıcı olabileceği ve her biri için alınan önlem.
>
> **Ne DEMEK DEĞİL:** Listelenmeyen bir riskin olmadığını söylemez; önlemler riskleri ortadan kaldırmaz, görünür kılar.

---

## 9. Açık sorular (kullanıcıya)

1. **Rastgele bölme istisnası:** CLAUDE.md "rastgele bölme yasaktır" der (kredi, `issue_d`). Tarih alanı olmayan bu iki sette tabakalı rastgele bölmeyi bir ADR ile onaylıyor musun?
2. **Hillstrom birincil kolu:** Womens E-Mail vs No E-Mail birincil, Mens ikincil (kapı dışı) olsun mu? Alternatif: iki e-posta kolu birleşik "herhangi e-posta".
3. **Birincil sonuç:** Uyum soruları (Q1) için `visit` mi, `conversion` mı? Öneri `visit` (dönüşüm iki sette de seyrek, güç düşük); değer hesabı Hillstrom'da `spend`, Criteo'da `conversion`.
4. **Birincil maliyet hücresi:** Hillstrom $g=0{,}30$, $c=0{,}10$ $; Criteo $k=0{,}001$ — onay ya da değişiklik?
5. **Lisans:** Criteo CC BY-NC-SA 4.0 ticari olmayan kullanım şartı taşıyor; depoda `docs/COMMERCIALIZATION_TODO.md` var. Bu çalışmanın ticari olmayan doğrulama olarak kalacağını onaylıyor musun? Hillstrom için şart bulunamadı; bu durumda kullanalım mı?
6. **Dondurulmuş sürüm:** Belirtilen `demo-v0.3` etiketi uzak depoda bulunamadı (mevcut: `demo-v0-final`, `demo-v0.1`, `demo-v0.2`); `main` = c8ec459 ve `pilot-protocol-revision` dalı main'e birleşmemiş. Dondurulan nokta hangisi; etiket atılacak mı?
7. **Kod yeri:** `backend/src/credit_coach/ecom/` mi, ayrı paket (`ecom/` kökünde, kendi `pyproject.toml`'u) mu? Öneri: ayrı alt paket `backend/src/credit_coach/ecom/`, kredi modüllerini içe aktarmaz; testle denetlenir.
8. **Criteo boyutu:** Tamamı (≈ 14 M satır) mı, baştan deterministik %25 alt örnek mi? Öneri: tamamı, bellek yetmezse bölüm 6/E2'deki önceden tanımlı alt örnek.
9. **Kapı eşikleri:** Bölüm 6'daki sayılar (Qini alt sınırı > 0; eğim [0,5; 1,5] / [0,7; 1,3]; 8/10 desil ve %25 tolerans; $s^* \le 0{,}5$; $r$ alt sınırı $\ge s^*$; SMD < 0,05) onaylanırsa belge dondurulur.

> **Bu bölüm ne demek:** Plan dondurulmadan önce kullanıcının karar vermesi gereken noktalar.
>
> **Ne DEMEK DEĞİL:** Önerilen varsayılanlar karar yerine geçmez; onay gelmeden E0 başlamaz.
