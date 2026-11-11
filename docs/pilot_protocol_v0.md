# Pilot protokolü v0: tek kollu, tavanlı, rastgele seçilmiş karşı teklif pilotu

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

## Tasarım

**Soru.** Karşı teklif verilen ve fonlanan krediler, hurdle üstünde pozitif ortalama getiri sağlıyor mu? Reddetmenin değeri tanım gereği 0 alınır; bu yüzden karar için kontrol kolu gerekmez. φ (modelin öngördüğü etkinin gerçekleşen payı) bu soru için ölçülmez; yalnızca mekanizmayı anlamak ve ölçeklemek için gerekir, bu belgede güç hesabının bir senaryo parametresidir.

**Kollar.** Tek kol: karşı teklif. Kontrol kolu yok.

**Aday havuzu.** `docs/demo_counteroffer_economics.md` ile aynı tanım: v1 REJECTED (destek içi) başvurulardan, kurum yolu (`loan_amount_reduction`) planı geçerli olanlar; geçerlilik ve etiket `p_high` kuralıyla. Segmentler: (ii) GUCLU+KOSULLU, (iii) planı geçerli olan hepsi. δ ∈ {0,012 (varsayılan), 0,03}. Hesap için kalibrasyon dilimi (2015-03..06) ve boşluk ayları (2015-01, 02, 07, 08) TEK havuzda birleştirilir; test dilimi yüklenmez.

**Seçim.** Havuzdan basit rastgele örnek (yerine koymasız). Tohum ve örnek listesi, pilot başlamadan önce kayda geçirilir; seçimi kişi ya da etiket belirlemez. Teklif edilen kişi sayısı, fonlanacak kredi sayısının kabul oranına bölünmesiyle bulunur.

**Birincil çıktı.** Kredi başına gerçekleşen hurdle üstü getiri (USD): `R = L' × [ (1 − y) · getiri − y · temerrüt_kaybı − hurdle ]`; y gerçekleşen sonuç (1 = temerrüt), L' planın yeni tutarı. getiri, temerrüt kaybı ve hurdle (toplam) `configs/cost.yaml`'dan, `counteroffer_economics.load_cost` ile okunur ve değiştirilmez.

**Hipotez ve test.** H0: E[R] ≤ 0; H1: E[R] > 0 (tek yönlü). α = 0,05. Test, kredi başına R değerlerinin ortalaması üzerinde normal yaklaşımla yapılır.

## Hesap yöntemi

**Senaryo.** φ ∈ {0; 0,25; 0,50; 0,75; 1,00}. Her havuz kaydı i için `p_i(φ) = p_point_önce − φ · Δ_point`, `Δ_point = p_point_önce − p_point_sonra`. Bu, nokta tahminidir; geçerlilik ve etiket `p_high` kuralıyla kalır, karıştırılmaz. Sonuç y_i, p_i(φ) olasılıklı Bernoulli kabul edilir.

**Ortalama ve standart sapma (L' ağırlıklı).** a = getiri − hurdle, b = getiri + temerrüt_kaybı. Kayıt i için R_i, y = 0 iken `L'_i · a`, y = 1 iken `L'_i · (a − b)`. Rastgele seçilmiş bir kredi için:

- `μ(φ) = ortalama_i [ L'_i · ( a − b · p_i ) ]`
- `E[R²] = ortalama_i [ L'_i² · ( p_i · (a − b)² + (1 − p_i) · a² ) ]`
- `σ(φ) = karekök( E[R²] − μ(φ)² )` (kayıtlar arası ve Bernoulli değişkenliğinin ikisini de içerir).

Ayrıca ort. L' (USD), `σ / ort. L'` ve `μ / ort. L'` (yüzde) verilir.

**Gereken fonlanan kredi sayısı.** `N = yukarı_yuvarla( ((z_{1−α} + z_güç) · σ(φ) / μ(φ))² )`, z_{1−α} = 1,6449 (α = 0,05, tek yönlü), güç %80 için z = 0,8416, %90 için z = 1,2816 (`statistics.NormalDist().inv_cdf`). σ, senaryo φ altında alınır. `μ(φ) ≤ 0` ise N "tanımsız (μ ≤ 0)" yazılır.

**Teklif edilecek kişi sayısı.** Kabul oranı a ∈ {0,3; 0,5; 0,7}: `yukarı_yuvarla( N / a )`. Teklifi kabul edenler, teklif edilenlerin rastgele alt kümesi sayılır; bu varsayım Sınırlar bölümünde yeniden anılır.

**φ = 0 senaryosu ve en kötü durum.** φ = 0'da kredi başına beklenen hurdle üstü değer μ(0). İki ayrı büyüklük, KARIŞTIRILMAZ:

- *Hurdle üstü değer*: `L' × [ (1 − y)·getiri − y·temerrüt_kaybı − hurdle ]`; hurdle, asgari marj, fon maliyeti ve işletme giderinin toplamıdır; bu değer negatif olabilir ve NAKİT KAYIP DEĞİLDİR.
- *Hurdle öncesi net sonuç (nakit görünümü, yaklaşık)*: `L' × [ (1 − y)·getiri − y·temerrüt_kaybı ]`; cost.yaml'ın ortalama getiri ve temerrüt kaybı varsayımlarıyla.

N kredilik pilot için N ∈ {100, 250, 500, 1000, 2000} ve referans pilot sayısı (aşağıda) için: φ = 0'da beklenen toplam hurdle üstü değer (N · μ(0)); en kötü durum, N kredinin tamamının temerrüde düşmesidir: hurdle üstü `−N · L' · (temerrüt_kaybı + hurdle)`, hurdle öncesi net `−N · L' · temerrüt_kaybı`; L' olarak ortalama L' ve kredi başına tavan (aşağıda) ayrı ayrı alınır.

**Bütçe tavanı ve durdurma kuralı önerisi (kurallar, sayıları veri belirler).** Değerler `configs/pilot.yaml`'a `varsayım` etiketiyle yazılır:

- `pilot_kredi_sayisi`: (ii) GUCLU+KOSULLU, δ = 0,012, φ = 0,50 senaryosunda %80 güç için gereken N, bir sonraki 100'e yukarı yuvarlanmış.
- `kredi_basina_tavan_usd`: aynı havuzda L' değerinin %90'lık dilimi, bir sonraki 500 USD'ye yukarı yuvarlanmış.
- `butce_tavani_usd` = `pilot_kredi_sayisi` × `kredi_basina_tavan_usd` (fonlanan toplam anaparanın üst sınırı; aşılmaz).
- `durdurma_esigi`: gerçekleşen kümülatif hurdle öncesi net sonuç, fonlanan toplam anaparanın −%5'inin altına düşerse yeni fonlama durur (sabit varsayım).
- Ayrıca α = 0,05, güç {0,8; 0,9}, φ ızgarası ve kabul oranı ızgarası aynı dosyada, aynı etiketle bulunur.

## Sonuçlar

Test dilimi kullanılmadı. Havuz: kalibrasyon dilimi ve boşluk ayları birleşik. Hurdle üstü değer ile hurdle öncesi net sonuç ayrı büyüklüklerdir; hurdle üstü değer nakit kayıp değildir.

## 1. Parametreler

| parametre | değer | kaynak |
|---|---|---|
| getiri | 0.1666 | `configs/cost.yaml`, `saglam_kredi_getirisi.mean` (varsayım) |
| temerrüt kaybı | 0.3519 | `configs/cost.yaml`, `temerrut_kaybi.mean` (varsayım) |
| hurdle (toplam) | 0.1100 | `configs/cost.yaml` (tez varsayımı) |
| a = getiri − hurdle | 0.0566 | |
| b = getiri + temerrüt kaybı | 0.5185 | |
| α (tek yönlü) | 0.05 | tasarım |
| z (α = 0,05; güç %80; güç %90) | 1.6449; 0.8416; 1.2816 | `statistics.NormalDist` |

> **Bu tablo ne demek:** Hesapta kullanılan getiri, temerrüt kaybı, hurdle, α ve z değerleri.

> **Ne DEMEK DEĞİL:** Bu değerler ölçülmüş fiyatlama değil varsayımdır; gerçek bir kurumun getirisini ya da kaybını göstermez.

## 2. Aday havuzu

| δ | segment | kayıt (havuz) | ort. L' (USD) | L' %90 (USD) | L' en büyük (USD) |
|---|---|---|---|---|---|
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 7167 | 9,171 | 21,440 | 31,500 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 9506 | 9,397 | 21,000 | 31,500 |
| 0.03 | (ii) GUCLU+KOSULLU | 280 | 7,412 | 17,500 | 17,500 |
| 0.03 | (iii) planı geçerli olan hepsi | 2904 | 9,954 | 17,500 | 31,500 |

> **Bu tablo ne demek:** δ ve segment başına havuzdaki kayıt sayısı ve karşı teklif tutarı L' dağılımı.

> **Ne DEMEK DEĞİL:** Havuz bir öneri listesi değildir; havuzdaki bir kişinin teklifi kabul edeceği anlamına gelmez.

## 3. Kredi başına getiri: ortalama ve standart sapma

| δ | segment | φ | μ (USD) | σ (USD) | σ / ort. L' | μ / ort. L' |
|---|---|---|---|---|---|---|
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.00 | -59.7 | 2,013.2 | 22.0% | -0.7% |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.25 | -14.7 | 1,943.2 | 21.2% | -0.2% |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.50 | 30.3 | 1,869.6 | 20.4% | 0.3% |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.75 | 75.3 | 1,791.7 | 19.5% | 0.8% |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1.00 | 120.3 | 1,709.2 | 18.6% | 1.3% |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.00 | -95.1 | 2,089.8 | 22.2% | -1.0% |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.25 | -41.1 | 2,009.3 | 21.4% | -0.4% |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.50 | 12.8 | 1,924.1 | 20.5% | 0.1% |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.75 | 66.8 | 1,833.2 | 19.5% | 0.7% |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1.00 | 120.7 | 1,736.0 | 18.5% | 1.3% |
| 0.03 | (ii) GUCLU+KOSULLU | 0.00 | -39.3 | 1,750.4 | 23.6% | -0.5% |
| 0.03 | (ii) GUCLU+KOSULLU | 0.25 | 16.1 | 1,654.4 | 22.3% | 0.2% |
| 0.03 | (ii) GUCLU+KOSULLU | 0.50 | 71.5 | 1,550.5 | 20.9% | 1.0% |
| 0.03 | (ii) GUCLU+KOSULLU | 0.75 | 126.9 | 1,437.0 | 19.4% | 1.7% |
| 0.03 | (ii) GUCLU+KOSULLU | 1.00 | 182.3 | 1,311.3 | 17.7% | 2.5% |
| 0.03 | (iii) planı geçerli olan hepsi | 0.00 | -91.3 | 2,166.1 | 21.8% | -0.9% |
| 0.03 | (iii) planı geçerli olan hepsi | 0.25 | -23.2 | 2,065.1 | 20.7% | -0.2% |
| 0.03 | (iii) planı geçerli olan hepsi | 0.50 | 45.0 | 1,956.5 | 19.7% | 0.5% |
| 0.03 | (iii) planı geçerli olan hepsi | 0.75 | 113.1 | 1,839.0 | 18.5% | 1.1% |
| 0.03 | (iii) planı geçerli olan hepsi | 1.00 | 181.2 | 1,710.8 | 17.2% | 1.8% |

> **Bu tablo ne demek:** φ senaryosu başına, rastgele seçilmiş bir kredinin hurdle üstü getirisinin ortalaması (μ) ve standart sapması (σ), L' ağırlıklı Bernoulli sonuçla.

> **Ne DEMEK DEĞİL:** μ gerçekleşen kâr değildir; p_point = p_önce − φ·Δ_point senaryosuna ve cost.yaml varsayımlarına bağlıdır, φ bilinmeyen bir etki payıdır.

## 4. Gereken fonlanan kredi sayısı

| δ | segment | φ | N, güç %80 | N, güç %90 |
|---|---|---|---|---|
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.00 | tanımsız (μ ≤ 0) | tanımsız (μ ≤ 0) |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.25 | tanımsız (μ ≤ 0) | tanımsız (μ ≤ 0) |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.50 | 23,508 | 32,563 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.75 | 3,500 | 4,848 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1.00 | 1,249 | 1,729 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.00 | tanımsız (μ ≤ 0) | tanımsız (μ ≤ 0) |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.25 | tanımsız (μ ≤ 0) | tanımsız (μ ≤ 0) |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.50 | 138,718 | 192,147 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.75 | 4,658 | 6,452 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1.00 | 1,279 | 1,771 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.00 | tanımsız (μ ≤ 0) | tanımsız (μ ≤ 0) |
| 0.03 | (ii) GUCLU+KOSULLU | 0.25 | 65,023 | 90,068 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.50 | 2,906 | 4,025 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.75 | 793 | 1,098 |
| 0.03 | (ii) GUCLU+KOSULLU | 1.00 | 320 | 444 |
| 0.03 | (iii) planı geçerli olan hepsi | 0.00 | tanımsız (μ ≤ 0) | tanımsız (μ ≤ 0) |
| 0.03 | (iii) planı geçerli olan hepsi | 0.25 | tanımsız (μ ≤ 0) | tanımsız (μ ≤ 0) |
| 0.03 | (iii) planı geçerli olan hepsi | 0.50 | 11,710 | 16,220 |
| 0.03 | (iii) planı geçerli olan hepsi | 0.75 | 1,636 | 2,266 |
| 0.03 | (iii) planı geçerli olan hepsi | 1.00 | 552 | 764 |

> **Bu tablo ne demek:** H0: E[R] ≤ 0'ı tek yönlü α = 0,05 ile reddetmek için, senaryo μ ve σ altında, %80 ve %90 güçle gereken fonlanan kredi sayısı.

> **Ne DEMEK DEĞİL:** Gerçekte φ'nin senaryodaki değer olacağı anlamına gelmez; μ ≤ 0 olan senaryoda pozitif ortalama beklenmediği için N tanımsızdır.

## 5. Teklif edilecek kişi sayısı

| δ | segment | φ | güç | teklif, kabul 0,3 | teklif, kabul 0,5 | teklif, kabul 0,7 |
|---|---|---|---|---|---|---|
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.50 | 80 | 78,360 | 47,016 | 33,583 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.50 | 90 | 108,544 | 65,126 | 46,519 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.75 | 80 | 11,667 | 7,000 | 5,000 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 0.75 | 90 | 16,160 | 9,696 | 6,926 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1.00 | 80 | 4,164 | 2,498 | 1,785 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1.00 | 90 | 5,764 | 3,458 | 2,470 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.50 | 80 | 462,394 | 277,436 | 198,169 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.50 | 90 | 640,490 | 384,294 | 274,496 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.75 | 80 | 15,527 | 9,316 | 6,655 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 0.75 | 90 | 21,507 | 12,904 | 9,218 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1.00 | 80 | 4,264 | 2,558 | 1,828 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1.00 | 90 | 5,904 | 3,542 | 2,530 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.25 | 80 | 216,744 | 130,046 | 92,890 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.25 | 90 | 300,227 | 180,136 | 128,669 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.50 | 80 | 9,687 | 5,812 | 4,152 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.50 | 90 | 13,417 | 8,050 | 5,750 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.75 | 80 | 2,644 | 1,586 | 1,133 |
| 0.03 | (ii) GUCLU+KOSULLU | 0.75 | 90 | 3,660 | 2,196 | 1,569 |
| 0.03 | (ii) GUCLU+KOSULLU | 1.00 | 80 | 1,067 | 640 | 458 |
| 0.03 | (ii) GUCLU+KOSULLU | 1.00 | 90 | 1,480 | 888 | 635 |
| 0.03 | (iii) planı geçerli olan hepsi | 0.50 | 80 | 39,034 | 23,420 | 16,729 |
| 0.03 | (iii) planı geçerli olan hepsi | 0.50 | 90 | 54,067 | 32,440 | 23,172 |
| 0.03 | (iii) planı geçerli olan hepsi | 0.75 | 80 | 5,454 | 3,272 | 2,338 |
| 0.03 | (iii) planı geçerli olan hepsi | 0.75 | 90 | 7,554 | 4,532 | 3,238 |
| 0.03 | (iii) planı geçerli olan hepsi | 1.00 | 80 | 1,840 | 1,104 | 789 |
| 0.03 | (iii) planı geçerli olan hepsi | 1.00 | 90 | 2,547 | 1,528 | 1,092 |

> **Bu tablo ne demek:** Fonlanacak kredi sayısını, kabul oranına bölerek bulunan teklif sayısı.

> **Ne DEMEK DEĞİL:** Kabul oranı bilinmiyor; teklifi kabul edenlerin teklif edilenlerden farklı olabileceği hesaba katılmadı.

## 6. φ = 0 senaryosu ve en kötü durum

| δ | segment | N | ort. L' (USD) | L' tavan (USD) | beklenen hurdle üstü toplam, φ = 0 (USD) | beklenen hurdle öncesi net toplam, φ = 0 (USD) | en kötü: hurdle üstü, ort. L' (USD) | en kötü: hurdle üstü, tavan (USD) | en kötü: hurdle öncesi net, ort. L' (USD) | en kötü: hurdle öncesi net, tavan (USD) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 100 | 9,171 | 21,500 | -5,966 | 94,916 | -423,593 | -993,039 | -322,711 | -756,539 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 250 | 9,171 | 21,500 | -14,914 | 237,291 | -1,058,983 | -2,482,598 | -806,778 | -1,891,348 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 500 | 9,171 | 21,500 | -29,828 | 474,581 | -2,117,966 | -4,965,197 | -1,613,556 | -3,782,697 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 1,000 | 9,171 | 21,500 | -59,657 | 949,163 | -4,235,932 | -9,930,394 | -3,227,112 | -7,565,394 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 2,000 | 9,171 | 21,500 | -119,314 | 1,898,326 | -8,471,864 | -19,860,788 | -6,454,224 | -15,130,788 |
| 0.012 (varsayılan) | (ii) GUCLU+KOSULLU | 23,600 | 9,171 | 21,500 | -1,407,904 | 22,400,245 | -99,967,990 | -234,357,295 | -76,159,841 | -178,543,295 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 100 | 9,397 | 21,500 | -9,505 | 93,856 | -434,006 | -993,039 | -330,644 | -756,539 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 250 | 9,397 | 21,500 | -23,763 | 234,641 | -1,085,014 | -2,482,598 | -826,610 | -1,891,348 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 500 | 9,397 | 21,500 | -47,527 | 469,282 | -2,170,029 | -4,965,197 | -1,653,220 | -3,782,697 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 1,000 | 9,397 | 21,500 | -95,053 | 938,565 | -4,340,057 | -9,930,394 | -3,306,439 | -7,565,394 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 2,000 | 9,397 | 21,500 | -190,106 | 1,877,130 | -8,680,114 | -19,860,788 | -6,612,878 | -15,130,788 |
| 0.012 (varsayılan) | (iii) planı geçerli olan hepsi | 23,600 | 9,397 | 21,500 | -2,243,254 | 22,150,134 | -102,425,349 | -234,357,295 | -78,031,961 | -178,543,295 |
| 0.03 | (ii) GUCLU+KOSULLU | 100 | 7,412 | 21,500 | -3,926 | 77,603 | -342,335 | -993,039 | -260,805 | -756,539 |
| 0.03 | (ii) GUCLU+KOSULLU | 250 | 7,412 | 21,500 | -9,815 | 194,009 | -855,837 | -2,482,598 | -652,013 | -1,891,348 |
| 0.03 | (ii) GUCLU+KOSULLU | 500 | 7,412 | 21,500 | -19,631 | 388,017 | -1,711,673 | -4,965,197 | -1,304,025 | -3,782,697 |
| 0.03 | (ii) GUCLU+KOSULLU | 1,000 | 7,412 | 21,500 | -39,262 | 776,035 | -3,423,347 | -9,930,394 | -2,608,050 | -7,565,394 |
| 0.03 | (ii) GUCLU+KOSULLU | 2,000 | 7,412 | 21,500 | -78,523 | 1,552,069 | -6,846,693 | -19,860,788 | -5,216,100 | -15,130,788 |
| 0.03 | (ii) GUCLU+KOSULLU | 23,600 | 7,412 | 21,500 | -926,577 | 18,314,419 | -80,790,979 | -234,357,295 | -61,549,983 | -178,543,295 |
| 0.03 | (iii) planı geçerli olan hepsi | 100 | 9,954 | 21,500 | -9,128 | 100,365 | -459,748 | -993,039 | -350,255 | -756,539 |
| 0.03 | (iii) planı geçerli olan hepsi | 250 | 9,954 | 21,500 | -22,819 | 250,912 | -1,149,369 | -2,482,598 | -875,638 | -1,891,348 |
| 0.03 | (iii) planı geçerli olan hepsi | 500 | 9,954 | 21,500 | -45,638 | 501,824 | -2,298,738 | -4,965,197 | -1,751,276 | -3,782,697 |
| 0.03 | (iii) planı geçerli olan hepsi | 1,000 | 9,954 | 21,500 | -91,275 | 1,003,649 | -4,597,475 | -9,930,394 | -3,502,551 | -7,565,394 |
| 0.03 | (iii) planı geçerli olan hepsi | 2,000 | 9,954 | 21,500 | -182,551 | 2,007,298 | -9,194,951 | -19,860,788 | -7,005,102 | -15,130,788 |
| 0.03 | (iii) planı geçerli olan hepsi | 23,600 | 9,954 | 21,500 | -2,154,102 | 23,686,111 | -108,500,416 | -234,357,295 | -82,660,204 | -178,543,295 |

> **Bu tablo ne demek:** φ = 0'da (karşı teklif riski değiştirmez) N kredi için beklenen toplam hurdle üstü değer ve hurdle öncesi net sonuç; en kötü durumda tüm kredilerin temerrüde düşmesi, ort. L' ve kredi başına tavanla.

> **Ne DEMEK DEĞİL:** Hurdle üstü değer nakit kayıp değildir (hurdle asgari marj, fon maliyeti ve işletme giderini içerir); en kötü durum tüm kredilerin aynı anda temerrüde düşmesidir ve olası bir sonuç tahmini değil bir üst sınırdır.

## 7. Bütçe tavanı ve durdurma kuralı önerisi

| öğe | değer | kural |
|---|---|---|
| `pilot_kredi_sayisi` | 23,600 | (ii) GUCLU+KOSULLU, δ = 0,012, φ = 0,50, güç %80 için gereken N, sonraki 100'e yukarı yuvarlanmış |
| `kredi_basina_tavan_usd` | 21,500 | aynı havuzda L' %90'lık dilimi, sonraki 500 USD'ye yukarı yuvarlanmış |
| `butce_tavani_usd` | 507,400,000 | `pilot_kredi_sayisi` × `kredi_basina_tavan_usd` |
| `durdurma_esigi` | -0.05 | gerçekleşen kümülatif hurdle öncesi net sonuç / fonlanan toplam anapara bu değerin altına düşerse yeni fonlama durur |

> **Kural çıktısı notu:** `pilot_kredi_sayisi` (23,600) bu veride aynı segment ve δ'daki havuz kaydından (7,167) büyüktür; yerine koymasız rastgele örnek bu havuzdan alınamaz. Bu değerler tasarımdaki kuralın mekanik çıktısıdır, kural sonuç görüldükten sonra değiştirilmedi; uygulanabilir bir pilot boyutu önerisi olarak okunmamalıdır.

> **Bu tablo ne demek:** Tasarımdaki kurallarla hesaplanan değerler; `configs/pilot.yaml` dosyasına `varsayım` etiketiyle yazıldı.

> **Ne DEMEK DEĞİL:** Bunlar bir kredi verenin risk iştahını temsil etmez; öneridir ve bir yetkili tarafından belirlenmelidir.

## Hukuk ve uyum

Bu liste hukuki görüş değildir; karar verilmemiştir. Kredi verenin yargı alanı bilinmiyor (veri 2012-15 ABD verisidir); sorular bir hukuk ve uyum uzmanına yöneltilmek üzere yazıldı.

1. **Karşı teklif bildirimi.** Reddedilen bir başvuruya daha düşük tutarlı karşı teklif sunulduğunda, olumsuz karar bildirimi ile karşı teklif hangi sırayla, hangi içerik ve sürelerle iletilmelidir? Teklif reddedilir ya da yanıtsız kalırsa ayrı bir bildirim gerekir mi?
2. **Deneysel kredi onayı.** Politika gereği reddedilecek başvurulardan rastgele seçilenlere kredi sunmak hangi izin, kayıt ve izleme koşullarına bağlıdır? Rastgele seçimin, seçilmeyen ya da seçilen gruplar arasındaki farklı etki bakımından nasıl belgelenmesi gerekir? Pilot için düzenleyiciye bildirim ya da izin gerekir mi?
3. **Olumsuz karar bildirimi.** Reddedilen başvuruya gönderilen bildirimde hangi gerekçelerin, hangi ayrıntıyla ve modelin kullanıldığı bilgisinin yer alması gerekir? Karşı teklifin tutarı ve dayanağı bu bildirimin parçası mıdır?
4. **Katılımcıya bilgi.** Müşteriye teklifin bir pilotun parçası olduğu söylenmeli midir? Pilot verisinin saklanması ve sonradan analizi için hangi rıza ve saklama koşulları geçerlidir?
5. **Koşullar.** Karşı teklif yalnızca tutarı değiştiriyorsa (faiz ve vade aynı) bu, ayrı bir kredi ürünü ya da farklı bir fiyatlama sayılır mı?

## Sınırlar

- **36 aylık sonuç gecikmesi.** Gerçekleşen getiri vade sonunda bilinir; birincil çıktı pilot başladıktan yaklaşık 36 ay sonra ölçülebilir. Durdurma kuralı fonlama bittikten sonra devreye girebilir; fonlanan anapara pilot başında taahhüt edilir, bu yüzden asıl koruma bütçe tavanıdır.
- **Erken gösterge çalışması yok.** Vadeden önce karar vermeye yarayacak göstergeler (geç ödeme, ilk temerrüt zamanı) ayrı bir çalışma gerektirir ve bu belgede yapılmadı.
- **Seçilim ve kabul farkı.** Teklifi kabul edenlerin teklif edilenlerden farklı olması (örneğin daha düşük risk ya da daha yüksek ihtiyaç) güç hesabına ve sonuca yansır; kabul oranı yalnızca teklif sayısını ölçekler, kabul edenlerin temerrüt oranını değiştirmez varsayılmıştır.
- **2012-15 ABD verisi.** Havuz ve olasılıklar bu dönemin kredilerinden gelir; bugünkü bir kredi veren için geçerliliği doğrulanmadı.
- **Varsayımlar.** getiri, temerrüt kaybı ve hurdle `configs/cost.yaml`'daki varsayımlardır; φ ölçülmüş bir etki değil, bir senaryo parametresidir; normal yaklaşım küçük N ve çarpık R için yaklaşıktır.

## Revizyon 1 (sonradan)

Bu bölüm, yukarıdaki sonuçlar görüldükten SONRA, ayrı bir değişiklikle eklenen sonradan revizyondur. Yukarıdaki Tasarım, Hesap yöntemi, Sonuçlar, Hukuk ve uyum ve Sınırlar bölümlerinin metni değiştirilmemiştir. Bu bölümün "Revizyon tanımı" kısmı, sayılar hesaplanmadan önce yazılmış ve commit'lenmiştir; "Revizyon sonuçları" kısmı bu tanımdan üretilir.

Yukarıdaki Tablo 6 ve Tablo 7'deki "bütçe tavanı" ve "en kötü durum" ifadelerinin yerini bu bölümdeki nominal anapara ve zarar kuyruğu alır; Tablo 4'teki "varsayılan φ için gereken N" yerine, uygulanabilir N için en küçük saptanabilir etki verilir. Eski metin silinmedi ve değiştirilmedi.

### Revizyon tanımı

**Kapsam.** Test dilimi kullanılmaz; havuz yukarıdaki gibi kalibrasyon dilimi (2015-03..06) ve boşluk aylarıdır (2015-01, 02, 07, 08). Motor, politika, katalog ve `configs/cost.yaml` değişmez. Segmentler: (ii) GUCLU+KOSULLU ve (iii) planı geçerli olan hepsi. δ ∈ {0,012; 0,03}. Aday havuzu, kredi başına değer ve p_point senaryosu yukarıdaki "Hesap yöntemi" bölümündeki gibidir.

**Açık varsayımlar.**
1. getiri ve temerrüt kaybı, `configs/cost.yaml` ortalamalarıdır (getiri `saglam_kredi_getirisi.mean`, temerrüt kaybı `temerrut_kaybi.mean`); hurdle `decision.total_hurdle`'dır.
2. Ürün ya da risk bazlı fiyat farkı yoktur: her kredi için aynı getiri kullanılır.
3. Bir kredinin sonucu, p = p_point_önce − φ·Δ_point olasılıklı bağımsız bir Bernoulli olayıdır; seçilen krediler havuzdan yerine koymayla çekilir (sonlu havuz düzeltmesi yok).
4. Normal yaklaşım ve Monte Carlo sonuçları yaklaşıktır.

**a) En küçük saptanabilir etki (MDE).** N ∈ {250; 500; 1.000; 2.000} fonlanan kredi, güç %80, α = 0,05 tek yönlü. Her (δ, segment, N) için:
- μ_min(N) = (z_(0,95) + z_(0,80)) · σ₀ / √N. σ₀, "Hesap yöntemi"ndeki σ'nın φ = 0 senaryosundaki değeridir (L' ağırlıklı Bernoulli).
- μ_min(N) USD olarak ve havuzdaki ort. L'nin yüzdesi olarak verilir.
- Karşılık gelen φ: μ(φ), φ'ye göre doğrusaldır (p, φ'de doğrusal olduğundan); μ_min(N), φ ∈ {0; 0,25; 0,50; 0,75; 1,00} noktalarındaki μ(φ) değerleri arasında doğrusal enterpolasyonla φ'ye çevrilir. μ_min(N) > μ(1,00) ise ">1,00" yazılır; μ_min(N) ≤ μ(0) ise "≤ 0,00" yazılır.
- Referans olarak μ(1,00) de tabloya yazılır.

**b) Nominal anapara ve zarar kuyruğu.** "Bütçe tavanı" iki büyüklüğe ayrılır:
- Nominal anapara = N × havuzdaki ort. L' (USD). Kayıp ya da kayıp üst sınırı değildir.
- Zarar kuyruğu: φ = 0 senaryosunda (p = p_point_önce) N kredilik portföyün toplam sonucunun alt %5 ve alt %1 yüzdelikleri. Toplam, iki biçimde hesaplanır: hurdle üstü (R = L'·[(1−Y)·getiri − Y·temerrüt kaybı − hurdle]) ve hurdle öncesi net (R = L'·[(1−Y)·getiri − Y·temerrüt kaybı]); Y ∈ {0, 1} Bernoulli(p_point_önce) sonuçtur.
- Yöntem: Monte Carlo. Her (δ, segment, N) için 20.000 tekrar; her tekrarda havuzdan yerine koymayla N kayıt çekilir ve her birinin Y sonucu bağımsız olarak üretilir. Tohum 7 (`numpy.random.default_rng(7)`, her (δ, segment, N) için yeniden başlatılır). Yüzdelik, `numpy.percentile` (doğrusal enterpolasyon) ile alınır.
- Beklenen toplam (N × μ, φ = 0) yanına yazılır. Hurdle üstü değer nakit kayıp değildir; hurdle öncesi net sonuç nakit görünüme yaklaşık bir ölçüdür (zamanlama, iskonto ve erken ödeme hesaba katılmaz).
- "Hepsi temerrüt" en kötü durumu bu yüzdeliklerle değiştirilir.

**c) Aday akışı.** Kalibrasyon ve boşluk aylarının her birinde (8 ay) (δ, segment) için aday sayısı sayılır; aylık ortalama = toplam aday / 8. Müşteri ölçeği s ∈ {%100, %10, %1}: %100 = bu verideki aylık aday akışı olduğu gibi; %10 ve %1 bunun doğrusal ölçeğidir. Kabul oranı a ∈ {1,00; 0,70; 0,50; 0,30} (1,00: her aday teklif alır ve kabul eder). N krediyi doldurmak için gereken ay = N / (aylık ortalama aday × s × a), N ∈ {250; 500; 1.000; 2.000}, bir ondalıkla. Akışın sabit olduğu, mevsimsellik olmadığı varsayılır; 36 aylık sonuç gecikmesi bu süreye eklenmez.

**d) `configs/pilot.yaml`.** Eski mekanik çıktılar (`pilot_kredi_sayisi`, `kredi_basina_tavan_usd`, `butce_tavani_usd`) "varsayım, kural çıktısı, uygulanabilir değil" etiketiyle kalır; değerleri değişmez. Revizyon değerleri ayrı `revizyon_1` bölümünde yer alır ve "varsayım" etiketi taşır.
