# Demo v0: karşı teklif adaylarında kalibrasyon ve seçilim kontrolü

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

## Tanım

**Kapsam.** Yalnızca kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08); test dilimi yüklenmez. Motor, politika (v1), katalog ve `configs/cost.yaml` değişmez. Aday kümeleri `docs/demo_counteroffer_economics.md` ile aynıdır: v1 REJECTED (destek içi) kayıtlardan, kurum yolu (`loan_amount_reduction`) planı geçerli olanlar; segmentler (i) GUCLU, (ii) GUCLU+KOSULLU, (iii) planı geçerli olan hepsi; δ ∈ {0,012 (varsayılan), 0,03}; geçerlilik ve etiket `p_high` kuralıyla. Gözlenen sonuç (`target`: 1 = temerrüt) yalnızca değerlendirme içindir; plan seçimine, geçerliliğe ve etikete girmez.

**Gösterim.** Her tablo dilim (kalibrasyon, boşluk) × δ × segment için ayrı satırdır. Boş segmentte "-" yazılır.

**Bootstrap (tüm aralıklar).** Kayıt bazlı, yerine koymalı; 2000 tekrar; sabit seed 7 (`numpy.random.default_rng(7)`, her hücre için yeniden başlatılır); yüzdelik aralık (%2,5 ve %97,5). Aday kümesinin kendisi sabit alınır; adayın seçilmesindeki belirsizlik aralığa girmez.

**1. Segment içi kalibrasyon.** Aday kümesinde: ortalama p_point (önce, φ = 0), GÖZLENEN temerrüt oranı, fark = gözlenen − tahmin (yüzde puan değil, oran farkı), farkın bootstrap %95 aralığı.

**2. Seçilim kontrolü.** Aday kayıtlar, kümelerinin (dilim × δ × segment) içinde Δ_point = `p_point_önce − p_point_sonra` değerinin beş eşit sayılı dilimine (kantil 0-20, 20-40, 40-60, 60-80, 80-100) ayrılır. Sınırlar, kümenin kendi Δ_point değerlerinden `numpy.percentile` (doğrusal, varsayılan) ile %20, %40, %60, %80 noktaları olarak hesaplanır; kova k, `[sınır_k, sınır_k+1)` aralığındadır, son kova üst sınırı içerir. Kümede 100'den az kayıt varsa kova kurulmaz ("n < 100" yazılır). Her kovada: kayıt sayısı, ortalama Δ_point, ortalama p_point (önce), gözlenen oran, fark = gözlenen − tahmin ve farkın bootstrap %95 aralığı. Kova sınırları ve bu kural, hiçbir sayı görülmeden bu belgeye yazılmıştır.

**3. Gözlenen-temelli başa-baş φ.** Toplam beklenen fazla kâr, φ'nin doğrusal işlevi olarak yazılır:

`T(φ) = T_gözlenen + φ · S`

- `T_gözlenen = Σ L' × [ (1 − y) · getiri − y · temerrüt_kaybı − hurdle ]` (φ = 0 başlangıcı, GÖZLENEN temerrütten).
- `S = Σ L' × Δ_point × (getiri + temerrüt_kaybı)` (φ'ye bağlı değişim; eğim modelin Δ_point değerinden alınır).
- Başa-baş φ = `−T_gözlenen / S`.

**Eğim varsayımı.** φ'ye bağlı değişimin eğimi, gözlenen değil, modelin kendi Δ_point tahminidir; gözlenen sonuçlar yalnızca başlangıç noktasını (φ = 0) belirler. Eğimin gerçekte farklı olması başa-baş φ'yi değiştirir; bu rapor onu ölçmez.

Gösterim: `T_gözlenen ≥ 0` ise "≤ 0,00"; başa-baş φ > 1 ise ">1,00"; aksi halde iki ondalıkla. Aralığın uçları aynı kuralla gösterilir (bootstrap'in her tekrarında −T/S yeniden hesaplanır). Ayrıca T_gözlenen ve T(1) = T_gözlenen + S (USD) verilir. getiri, temerrüt kaybı ve hurdle `configs/cost.yaml`'dan, `counteroffer_economics.load_cost` ile okunur.

## Sonuçlar

Test dilimi kullanılmadı. Bootstrap: 2000 tekrar, seed 7. Aday kümeleri `docs/demo_counteroffer_economics.md` ile aynıdır.

## 1. Segment içi kalibrasyon

| dilim | δ | segment | kayıt | ort. p_point (önce) | gözlenen temerrüt oranı | fark = gözlenen − tahmin | fark, bootstrap %95 aralığı |
|---|---|---|---|---|---|---|---|
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 280 | 0.1169 | 0.1464 | +0.0296 | [-0.0097; +0.0723] |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3257 | 0.1217 | 0.1240 | +0.0024 | [-0.0085; +0.0143] |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 4355 | 0.1285 | 0.1323 | +0.0038 | [-0.0053; +0.0143] |
| kalibrasyon | 0.03 | (i) GUCLU | 0 | - | - | - | - |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 112 | 0.1190 | 0.1607 | +0.0417 | [-0.0211; +0.1136] |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 1297 | 0.1262 | 0.1334 | +0.0072 | [-0.0118; +0.0254] |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 345 | 0.1169 | 0.1362 | +0.0193 | [-0.0156; +0.0570] |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3910 | 0.1216 | 0.1128 | -0.0088 | [-0.0190; +0.0014] |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 5151 | 0.1277 | 0.1192 | -0.0085 | [-0.0170; +0.0003] |
| boşluk | 0.03 | (i) GUCLU | 0 | - | - | - | - |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 168 | 0.1197 | 0.0655 | -0.0542 | [-0.0900; -0.0124] |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 1607 | 0.1261 | 0.1164 | -0.0097 | [-0.0249; +0.0065] |

> **Bu tablo ne demek:** Aday kümelerinde modelin ortalama nokta tahmini ile gözlenen temerrüt oranı yan yana, farkın bootstrap aralığıyla.

> **Ne DEMEK DEĞİL:** Fark, kümenin dışındaki kayıtlar ya da başka bir dilim için bir şey söylemez; aralık adayın seçilmesindeki belirsizliği içermez.

## 2. Seçilim kontrolü: Δ_point kovaları

| dilim | δ | segment | kova | Δ_point aralığı | kayıt | ort. Δ_point | ort. p_point (önce) | gözlenen oran | fark = gözlenen − tahmin | fark, bootstrap %95 aralığı |
|---|---|---|---|---|---|---|---|---|---|---|
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 1 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 2 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 3 | [0.0376; 0.0454) | 144 | 0.0376 | 0.1159 | 0.1250 | +0.0091 | [-0.0395; +0.0647] |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 4 | [0.0454; 0.0462) | 68 | 0.0454 | 0.1159 | 0.1765 | +0.0606 | [-0.0277; +0.1635] |
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 5 | [0.0462; 0.0654] | 68 | 0.0565 | 0.1199 | 0.1618 | +0.0419 | [-0.0461; +0.1304] |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 2 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3 | [0.0298; 0.0406) | 1771 | 0.0307 | 0.1160 | 0.1135 | -0.0025 | [-0.0167; +0.0127] |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 4 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 5 | [0.0406; 0.1061] | 1486 | 0.0470 | 0.1284 | 0.1366 | +0.0082 | [-0.0087; +0.0257] |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 2 | [0.0298; 0.0376) | 1602 | 0.0300 | 0.1160 | 0.1124 | -0.0036 | [-0.0192; +0.0114] |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 3 | [0.0376; 0.0406) | 169 | 0.0378 | 0.1164 | 0.1243 | +0.0079 | [-0.0394; +0.0613] |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 4 | [0.0406; 0.0581) | 1694 | 0.0448 | 0.1285 | 0.1375 | +0.0090 | [-0.0064; +0.0261] |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 5 | [0.0581; 0.1394] | 890 | 0.0707 | 0.1531 | 0.1596 | +0.0065 | [-0.0176; +0.0319] |
| kalibrasyon | 0.03 | (i) GUCLU | - | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 1 | [0.0522; 0.0539) | 3 | 0.0525 | 0.1162 | 0.0000 | -0.1162 | [-0.1167; -0.1159] |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 2 | [0.0539; 0.0547) | 40 | 0.0540 | 0.1160 | 0.0750 | -0.0410 | [-0.1160; +0.0590] |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 3 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 4 | [0.0547; 0.0646) | 37 | 0.0547 | 0.1160 | 0.2703 | +0.1543 | [+0.0192; +0.2895] |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 5 | [0.0646; 0.0654] | 32 | 0.0651 | 0.1267 | 0.1562 | +0.0296 | [-0.0954; +0.1546] |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 1 | - | 0 | - | - | - | - | - |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 2 | [0.0376; 0.0462) | 518 | 0.0405 | 0.1159 | 0.1255 | +0.0095 | [-0.0175; +0.0385] |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 3 | [0.0462; 0.0545) | 260 | 0.0490 | 0.1240 | 0.1385 | +0.0145 | [-0.0242; +0.0567] |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 4 | [0.0545; 0.0632) | 247 | 0.0567 | 0.1289 | 0.1174 | -0.0114 | [-0.0487; +0.0334] |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 5 | [0.0632; 0.1282] | 272 | 0.0737 | 0.1455 | 0.1581 | +0.0126 | [-0.0307; +0.0583] |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 1 | - | 0 | - | - | - | - | - |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 2 | - | 0 | - | - | - | - | - |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 3 | [0.0376; 0.0454) | 185 | 0.0376 | 0.1159 | 0.1568 | +0.0409 | [-0.0132; +0.0949] |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 4 | [0.0454; 0.0539) | 86 | 0.0457 | 0.1161 | 0.1628 | +0.0467 | [-0.0231; +0.1281] |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 5 | [0.0539; 0.0655] | 74 | 0.0594 | 0.1205 | 0.0541 | -0.0664 | [-0.1074; -0.0125] |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1 | [0.0254; 0.0298) | 1 | 0.0254 | 0.1159 | 0.0000 | -0.1159 | [-0.1159; -0.1159] |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 2 | - | 0 | - | - | - | - | - |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3 | [0.0298; 0.0406) | 2183 | 0.0307 | 0.1160 | 0.1099 | -0.0061 | [-0.0194; +0.0072] |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 4 | - | 0 | - | - | - | - | - |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 5 | [0.0406; 0.1061] | 1726 | 0.0479 | 0.1287 | 0.1165 | -0.0122 | [-0.0272; +0.0026] |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1 | [0.0254; 0.0298) | 1 | 0.0254 | 0.1159 | 0.0000 | -0.1159 | [-0.1159; -0.1159] |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 2 | [0.0298; 0.0376) | 1963 | 0.0299 | 0.1160 | 0.1060 | -0.0100 | [-0.0233; +0.0037] |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 3 | [0.0376; 0.0406) | 220 | 0.0378 | 0.1163 | 0.1455 | +0.0291 | [-0.0164; +0.0791] |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 4 | [0.0406; 0.0562) | 1892 | 0.0447 | 0.1288 | 0.1232 | -0.0056 | [-0.0200; +0.0093] |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 5 | [0.0562; 0.1229] | 1075 | 0.0687 | 0.1494 | 0.1312 | -0.0182 | [-0.0382; +0.0015] |
| boşluk | 0.03 | (i) GUCLU | - | - | 0 | - | - | - | - | - |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 1 | [0.0522; 0.0539) | 6 | 0.0524 | 0.1160 | 0.0000 | -0.1160 | [-0.1163; -0.1159] |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 2 | [0.0539; 0.0547) | 51 | 0.0540 | 0.1160 | 0.0392 | -0.0768 | [-0.1160; -0.0179] |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 3 | [0.0547; 0.0548) | 44 | 0.0547 | 0.1159 | 0.0682 | -0.0477 | [-0.1159; +0.0432] |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 4 | [0.0548; 0.0654) | 31 | 0.0632 | 0.1240 | 0.1290 | +0.0050 | [-0.0924; +0.1337] |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 5 | [0.0654; 0.0664] | 36 | 0.0655 | 0.1264 | 0.0556 | -0.0709 | [-0.1267; +0.0125] |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 1 | - | 0 | - | - | - | - | - |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 2 | [0.0376; 0.0462) | 635 | 0.0402 | 0.1159 | 0.1323 | +0.0163 | [-0.0104; +0.0415] |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 3 | [0.0462; 0.0553) | 318 | 0.0501 | 0.1225 | 0.0786 | -0.0439 | [-0.0745; -0.0124] |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 4 | [0.0553; 0.0646) | 319 | 0.0574 | 0.1303 | 0.1160 | -0.0144 | [-0.0460; +0.0203] |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 5 | [0.0646; 0.1229] | 335 | 0.0740 | 0.1445 | 0.1224 | -0.0222 | [-0.0560; +0.0140] |

> **Bu tablo ne demek:** Aday kayıtlar Δ_point'e göre beş eşit sayılı dilime ayrıldığında, her dilimde tahmin ve gözlenen oran farkı.

> **Ne DEMEK DEĞİL:** Kova içi fark, Δ_point ile farkın nedenini göstermez; kovalar küçük kümelerde az kayıt içerir ve aralıklar geniştir.

## 3. Gözlenen-temelli başa-baş φ

| dilim | δ | segment | kayıt | T_gözlenen (USD) | T(1) (USD) | başa-baş φ | başa-baş φ, bootstrap %95 aralığı |
|---|---|---|---|---|---|---|---|
| kalibrasyon | 0.012 (varsayılan) | (i) GUCLU | 280 | -44,720 | -2,824 | >1,00 | [≤ 0,00; >1,00] |
| kalibrasyon | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3257 | -349,927 | 235,637 | 0,60 | [0,20; >1,00] |
| kalibrasyon | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 4355 | -591,096 | 358,894 | 0,62 | [0,33; 0,91] |
| kalibrasyon | 0.03 | (i) GUCLU | 0 | - | - | - | - |
| kalibrasyon | 0.03 | (ii) GUCLU+KOSULLU | 112 | -29,767 | -4,896 | >1,00 | [≤ 0,00; >1,00] |
| kalibrasyon | 0.03 | (iii) planı geçerli olan hepsi | 1297 | -219,299 | 138,421 | 0,61 | [0,16; >1,00] |
| boşluk | 0.012 (varsayılan) | (i) GUCLU | 345 | -144,948 | -87,512 | >1,00 | [0,92; >1,00] |
| boşluk | 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 3910 | -166,259 | 537,893 | 0,24 | [≤ 0,00; 0,61] |
| boşluk | 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 5151 | -437,436 | 663,935 | 0,40 | [0,14; 0,65] |
| boşluk | 0.03 | (i) GUCLU | 0 | - | - | - | - |
| boşluk | 0.03 | (ii) GUCLU+KOSULLU | 168 | 20,515 | 57,685 | ≤ 0,00 | [≤ 0,00; 0,54] |
| boşluk | 0.03 | (iii) planı geçerli olan hepsi | 1607 | -147,884 | 285,633 | 0,34 | [≤ 0,00; 0,76] |

> **Bu tablo ne demek:** φ = 0 başlangıcı gözlenen temerrütten, φ'ye bağlı değişim modelin Δ_point eğimiyle hesaplanan toplamın sıfır olduğu φ ve bootstrap aralığı.

> **Ne DEMEK DEĞİL:** Eğim gözlenmedi, modelden alındı; '>1,00' etkinin tahmin edilenden büyük olması gerektiği bir senaryoyu gösterir, gerçek etkiyi ölçmez.

