# Demo v0: karşı teklif adaylarında kalibrasyon ve seçilim kontrolü (tanım; sayılar henüz hesaplanmadı)

> Etiket: tek fiyatlı kurgusal kredi veren. Bu çalışmadaki kredi veren tek bir sabit getiri, kayıp ve hurdle ile varsayılmıştır; gerçek bir kurumun fiyatlama politikası değildir.

Bu bölüm sonuçlardan ÖNCE yazıldı ve commit'lendi; hesap bu tanıma göre yapılır, sonuç görüldükten sonra değiştirilmez.

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
