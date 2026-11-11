# Pilot protokolü v0: tek kollu, tavanlı, rastgele seçilmiş karşı teklif pilotu (tasarım ve yöntem; sayılar henüz hesaplanmadı)

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Bu bölüm sonuçlardan ÖNCE yazıldı ve commit'lendi; hesap bu tasarıma ve yönteme göre yapılır, sonuç görüldükten sonra değiştirilmez. Hukuki görüş değildir; hukuk ve uyum bölümü yalnızca bir uzmana sorulacak soruların listesidir.

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

## Hukuk ve uyum

Karar verilmez, görüş verilmez; bir hukuk ve uyum uzmanına sorulacak sorular listelenir (kapsam: karşı teklif bildirimi, deneysel kredi onayı, olumsuz karar bildirimi).

## Sınırlar

36 aylık sonuç gecikmesi; erken gösterge çalışması yapılmadı; seçilim ve kabul farkı; 2012-15 ABD verisi; maliyet ve hurdle değerleri varsayımdır; p_point senaryosu (φ) ölçülmüş bir etki değildir.
