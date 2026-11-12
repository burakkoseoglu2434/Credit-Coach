# E1 — Hillstrom: tahmin edilen ve ölçülen fark

Üretildi: `python -m credit_coach.ecom.e1_hillstrom test` (test kümesi tek sefer). Kilit: `docs/ecom/test_run_hillstrom.lock` (commit `c0f4617`, 2026-11-12T13:33:06+00:00). Seçim test öncesi `docs/ecom/E1_selection.md`'de commit'lendi.

Tedavi = iki e-posta kolu birleşik, kontrol = No E-Mail; sonuç `visit`; test kümesi 12802 satır; eğitim $p$ = 0,667101. Bootstrap B = 1000, tabakalı. Çalışma süresi 6,5 s.

## Kapı ölçütleri (PLAN bölüm 6, E1; DONDURULDU)

Kapı modeli: `T_lr0.05_leaf7_it200`.

| Ölçüt | Tanım | Ölçülen | Sonuç |
|---|---|---|---|
| 1 | Qini alanı %95 alt sınırı > 0 | alt sınır 0,000151 | geçti |
| 2 | Kalibrasyon eğimi ∈ [0,5; 1,5] ve %95 alt sınırı > 0 | eğim 0,353 [-0,005; 0,688] | **kaldı** |
| 3 | Genel düzey farkı %95 aralığı 0'ı içerir | fark -0,00148 [-0,01274; 0,01047] | geçti |

**Karar (durdurma kuralı):** Kalan ölçüt(ler): 2. Durdurma kuralı: test yeniden çalıştırılmaz, model değiştirilmez.


> **Bu tablo ne demek:** Doğrulamada seçilen tek modelin test kümesinde, sonuç görülmeden dondurulmuş üç eşiğe göre durumu.
>
> **Ne DEMEK DEĞİL:** Geçmek, e-postanın başka bir kampanyada ya da kredide benzer bir fark yaratacağını göstermez; kalmak modelin hiçbir bilgi taşımadığını kanıtlamaz (Hillstrom küçük, güç düşük).

## İki model ailesi yan yana

| Model | Ayar | Qini alanı [%95] | Kalibrasyon eğimi [%95] | Genel düzey farkı [%95] |
|---|---|---|---|---|
| T (kapı) | `T_lr0.05_leaf7_it200` | 0,002661 [0,000151; 0,004961] | 0,353 [-0,005; 0,688] | -0,00148 [-0,01274; 0,01047] |
| TO | `TO_lr0.05_leaf7_it200` | 0,003006 [0,000604; 0,005463] | 0,420 [0,058; 0,800] | -0,00031 [-0,01153; 0,01182] |

> **Bu tablo ne demek:** Her ailenin doğrulamada en iyi ayarının test kümesindeki üç ölçüsü; kapıya yalnızca kapı modeli girer.
>
> **Ne DEMEK DEĞİL:** Ailelerden birinin daha iyi olduğu sonucunu desteklemez; aralıklar örtüşebilir ve seçim tek bir doğrulama kümesine dayanır.

## Qini eğrisi

$Q(\phi)/N$ değerleri; rastgele sıralama doğrusu $\phi\,Q(1)/N$. Eğri 100 noktada hesaplandı, burada 10'da biri gösteriliyor.

| $\phi$ | T: $Q/N$ | TO: $Q/N$ | Rastgele: $\phi Q(1)/N$ (T) |
|---|---|---|---|
| 0,1 | 0,00505 | 0,00671 | 0,00406 |
| 0,2 | 0,01212 | 0,01173 | 0,00811 |
| 0,3 | 0,01679 | 0,01593 | 0,01217 |
| 0,4 | 0,01984 | 0,02015 | 0,01623 |
| 0,5 | 0,02266 | 0,02482 | 0,02028 |
| 0,6 | 0,02772 | 0,02970 | 0,02434 |
| 0,7 | 0,03219 | 0,03128 | 0,02839 |
| 0,8 | 0,03499 | 0,03422 | 0,03245 |
| 0,9 | 0,03783 | 0,03679 | 0,03651 |
| 1,0 | 0,04056 | 0,04056 | 0,04056 |

> **Bu tablo ne demek:** Model sırasına göre en üstteki $\phi$ oranına gönderildiğinde, test kümesinde ölçülen artımlı ziyaret sayısının (kişi başına) rastgele sıralamayla karşılaştırması.
>
> **Ne DEMEK DEĞİL:** Eğrinin rastgele doğrunun üstünde olması tek bir test kümesinde sıralamanın bilgi taşıdığını gösterir; ziyaretin satışa ya da kâra dönüştüğünü göstermez.

## Desil tablosu (kapı modeli)

Desil 1 = en yüksek tahmin. Fark = tahmin edilen − ölçülen; aralık bootstrap %95.

| Desil | Satır | Tahmin edilen fark | Ölçülen fark | Fark | Fark %95 |
|---|---|---|---|---|---|
| 1 | 1281 | 0,1308 | 0,0777 | 0,0532 | [0,0108; 0,0993] |
| 2 | 1280 | 0,0934 | 0,1082 | -0,0148 | [-0,0518; 0,0231] |
| 3 | 1280 | 0,0796 | 0,0707 | 0,0089 | [-0,0296; 0,0478] |
| 4 | 1280 | 0,0714 | 0,0457 | 0,0257 | [-0,0126; 0,0666] |
| 5 | 1280 | 0,0637 | 0,0417 | 0,0220 | [-0,0159; 0,0608] |
| 6 | 1281 | 0,0551 | 0,0758 | -0,0207 | [-0,0564; 0,0145] |
| 7 | 1280 | 0,0458 | 0,0673 | -0,0215 | [-0,0576; 0,0158] |
| 8 | 1280 | 0,0365 | 0,0420 | -0,0056 | [-0,0405; 0,0303] |
| 9 | 1280 | 0,0252 | 0,0413 | -0,0160 | [-0,0534; 0,0232] |
| 10 | 1280 | -0,0083 | 0,0461 | -0,0544 | [-0,0975; -0,0116] |

Kalibrasyon eğimi (10 nokta, satır ağırlıklı): 0,353 [-0,005; 0,688]. Genel düzey: ortalama tahmin − ölçülen = -0,00148 [-0,01274; 0,01047].


> **Bu tablo ne demek:** Tahmin edilen ziyaret farkının, aynı desildeki tedavi ve kontrol gruplarından ölçülen farkla karşılaştırması.
>
> **Ne DEMEK DEĞİL:** Desil başına kontrol grubu küçüktür (yaklaşık 430 kişi); tek tek desil aralıkları geniştir ve tek başına karar dayanağı değildir. Ölçülen fark e-postanın bu kişilerde ne yapacağını değil, bu test kümesinde ölçülen ortalama farkı verir.

## Politika değeri (kapıya GİRMEZ; E3 ızgarası)

Değer = $g \cdot$ spend, maliyet $c$ \$ / e-posta (varsayım, PLAN 4.1). $\pi_{mod}$: kapı modelinin ailesi/ayarıyla `spend` üzerinde eğitilen modelin $g\hat\tau_{spend} - c > 0$ kuralı; destek dışı test satırı oranı 0,0047 (bu satırlarda $\pi_{mod} = 1$). Değerler müşteri başına \$, IPW ile. Birincil hücre kalın.

| $g$ | $c$ | Herkese | Hiçbirine | Modelle | Hedeflenen oran | Modelle − Herkese [%95] | Modelle − Hiçbirine [%95] |
|---|---|---|---|---|---|---|---|
| 0,20 | 0,01 | 0,2745 | 0,1203 | 0,2676 | 0,827 | -0,0069 [-0,0283; 0,0156] | 0,1473 [0,0622; 0,2364] |
| 0,20 | 0,10 | 0,1845 | 0,1203 | 0,1744 | 0,584 | -0,0101 [-0,0707; 0,0517] | 0,0541 [-0,0077; 0,1197] |
| 0,20 | 0,50 | -0,2155 | 0,1203 | 0,1091 | 0,052 | 0,3246 [0,2394; 0,4108] | -0,0112 [-0,0257; 0,0049] |
| 0,30 | 0,01 | 0,4167 | 0,1804 | 0,4107 | 0,834 | -0,0060 [-0,0380; 0,0271] | 0,2303 [0,1033; 0,3631] |
| **0,30** | **0,10** | 0,3267 | 0,1804 | 0,3047 | 0,701 | -0,0220 [-0,0893; 0,0448] | 0,1243 [0,0040; 0,2412] |
| 0,30 | 0,50 | -0,0733 | 0,1804 | 0,1518 | 0,104 | 0,2250 [0,1008; 0,3448] | -0,0287 [-0,0717; 0,0131] |
| 0,40 | 0,01 | 0,5589 | 0,2406 | 0,5476 | 0,836 | -0,0114 [-0,0540; 0,0325] | 0,3070 [0,1376; 0,4829] |
| 0,40 | 0,10 | 0,4690 | 0,2406 | 0,4378 | 0,746 | -0,0312 [-0,1009; 0,0336] | 0,1972 [0,0347; 0,3706] |
| 0,40 | 0,50 | 0,0690 | 0,2406 | 0,2124 | 0,172 | 0,1434 [-0,0121; 0,2985] | -0,0282 [-0,0978; 0,0373] |

> **Bu tablo ne demek:** Varsayılan marj ve maliyetle üç gönderim politikasının test kümesinde ters olasılık ağırlığıyla tahmin edilen müşteri başına değeri ve farkları.
>
> **Ne DEMEK DEĞİL:** Bir kâr vaadi değildir; $g$ ve $c$ varsayımdır, gerçek bir şirketin marjı ya da maliyeti değildir. Kapı kararı ve E3 değerlendirmesi bu tabloya dayanmaz; E3 ayrı bir adımdır.

