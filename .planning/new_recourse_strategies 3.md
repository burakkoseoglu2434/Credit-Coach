# Yeni Aksiyon Semantiği (Action Semantics) ve Recourse Havuzu

Mevcut sistemin 48 feature'lık temel modeli ve `recourse_feasibility.yaml` dosyasındaki kısıtlamaları incelediğimde, sadece "Kredi kartı kullanım oranını azalt (`revol_util` -> %X)" demenin çok ötesine geçebileceğimiz, matematiksel olarak uygulanabilir geniş bir öneri havuzu olduğunu görüyoruz. 

Aşağıdaki liste, DiCE veya Heuristic kuralları kullanılarak üretilip "İnsan diline" (Action Semantics) dökülebilecek detaylı **Öneri Alternatifleri Havuzudur:**

---

## 1. Kredi Kapasitesi ve Limit Yönetimi (Credit Limit Expansion)
Bazen müşterinin borç azaltacak parası yoktur, ancak "Kredi limitini yükseltmek" matematiksel olarak kullanım oranını (Utilization) aynı şekilde düşürür ve PD'ye (Temerrüt olasılığı) pozitif yansır.
*   **Hedef Feature:** `total_bc_limit` (Bankkart / Kredi kartı açık limiti)
    *   *Senaryo:* Müşterinin hesap kapatmasına gerek yok, sadece bankasını arayıp kullanılmayan tavan limitini yükseltmesi risk oranını düşürebilir.
    *   *Kullanıcı Çıktısı:* "Kredi kartı borcunuzu ödemeden bile riskinizi düşürebilirsiniz. Bankanızla görüşerek mevcut toplam kart limitinizi `X TL` seviyesinden `Y TL` seviyesine çıkarın, kullanmasanız dahi bu sizin finansal kapasitenizi güçlü gösterecektir."
*   **Hedef Feature:** `total_rev_hi_lim` / `tot_hi_cred_lim`
    *   *Kullanıcı Çıktısı:* "Kredili mevduat ve tüm dönen kredilerinizdeki (ipoteksiz) toplam yasal üst limitinizi `X TL` oranında artırmak onay ihtimalinizi %Z artırır."

## 2. Kurum İçi Cerrahi Müdahaleler (Surgical Debt Restructuring)
Sistemin müşteriye "Zaten paran yoksa reddedildin" dememesi için farklı kredi tipleri arasında geçiş önermesi.
*   **Hedef Feature:** `tot_cur_bal` vs `total_bal_ex_mort`
    *   *Senaryo:* Müşterinin çok fazla ufak tefek tüketici kredisi (taksitli) borcu var. 
    *   *Kullanıcı Çıktısı:* "Farklı yerlere dağılmış `X TL` tutarındaki ufak kredilerinizi veya borçlarınızı tek bir yere toplayıp (yapılandırma / borç transferi) aylık ödemelerinizi düzene sokmak sizi `APPROVED` bandına taşıyacaktır."
*   **Hedef Feature:** `open_acc` (Açık hesap sayısı)
    *   *Senaryo:* Tutar düşük olsa dahi çok fazla açık kredili ürün olması risk modelini (XGBoost) bozuyordur.
    *   *Kullanıcı Çıktısı:* "Açık kredi ve kart hesap sayınız `X` adettir. İçlerinde en düşük limitli olan `Y` adet hesabınızı veya hiç kullanmadığınız boş hesaplarınızı tamamen kapatın."

## 3. Gelir ve Belgeleme Optimizasyonu (Income & Trust Vectors)
Bazen matematik, paradan ziyade "güvenden" kaynaklı red verebilir.
*   **Hedef Feature:** `verification_status`
    *   *Senaryo:* Modeller, `Not Verified` (Doğrulanmamış gelir) olanları riskli sayar.
    *   *Kullanıcı Çıktısı:* "Beyan ettiğiniz gelir sistemimizde resmi belgelerle 'Doğrulanmamış' olarak görünüyor. `SGK / Maaş Bordrosu` sunarak durumunuzu 'Source Verified' (Doğrulanmış) yapmanız doğrudan kararımızı değiştirecektir."
*   **Hedef Feature:** `annual_inc`
    *   *Kullanıcı Çıktısı:* "Aylık gelir kaynaklarınıza, belgeleyebildiğiniz kira, prim veya serbest zamanlı (freelance) kazançlarınızı da ekleyerek resmi kayıtlı hedefinizi `X TL` seviyesine güncelleyin."

## 4. "Temizlik" ve Geçmiş Skoru Kurtarma (Delinquency Management)
Cezalı durumlardaki küçük hatalar büyük fark yaratır.
*   **Hedef Feature:** `delinq_amnt` (Gecikmiş borç tutarı) ve `acc_now_delinq`
    *   *Senaryo:* Toplam borç $50.000 olabilir ama sadece $500'lık bir kısım gecikmededir (delinquent). Sistemi bloklayan bu küçük tutardır.
    *   *Kullanıcı Çıktısı:* "Toplam borcunuza dokunmanıza gerek yok. Şu an kırmızı bültende / gecikmede görünen `X TL` değerindeki taksitlerinizi hemen kapatıp hesapları 'Güncel' statüye çekmek onay almanız için yeterlidir."
*   **Hedef Feature:** `collections_12_mths_ex_med` veya `tot_coll_amt`
    *   *Kullanıcı Çıktısı:* "İdari / yasal takibe (Collections) düşmüş dosyalarınızdaki `X TL`lik miktarı uzlaşma yoluyla (Settlement) kapattığınız an risk kalkanı kalkacaktır."

## 5. Uygulama/Başvuru Esnekliği (Application Flexing)
Müşteri kredi başvurusunu yapıyordur ve reddedilmiştir. Başvuruyu değiştirtsin.
*   **Hedef Feature:** `loan_amnt` & `installment` & `term`
    *   *Senaryo:* Model $20.000 krediye ve 36 aya red yazar, ama 60 aya veya $15.000'e onay yazar.
    *   *Kullanıcı Çıktısı:* "Başvurduğunuz `X TL`lik kredi limitini `Y TL`'ye düşürürsek VEYA vadeyi `36 aydan 48 aya` çıkarıp aylık taksit yükünüzü (Installment) `Z TL`ye çekersek başvurunuzu şu an **onaylayabiliriz.**"

---

### Sistem Entegrasyonu Nasıl Yapılır?
Bu önerileri üretmek için `recourse.yaml` içindeki **DiCE** motorunun bu feature'ları manipüle etmesine daha fazla izin vermemiz gerekir. Ancak bazıları (örneğin limit artırımı veya verification eklenmesi) Heuristic (Uzman Kuralı) tarafına kodlanarak "Kurum Teklifi" (`Offer Optimization`) katmanından `Narrative`'e çok daha gerçekçi ve yenilikçi bir şekilde, kolaylıkla dökülebilir.
