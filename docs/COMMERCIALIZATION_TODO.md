# Commercialization Readiness — Living TODO

Bu dosya, "sektörel başarıya / gerçek kurum pilotuna giden yolda ne eksik"
sorusuna verilen cevapları canlı tutmak için var. Buraya:

- yeni aklına gelen maddeleri,
- kapanan milestone/phase'lerden çıkan "yapılması gerekenler" notlarını,
- veri/güvenlik/regülasyon/mühendislik/iş geliştirme ile ilgili açık konuları

ekle. Bu liste, sıradaki milestone kararlarını (`.planning/ROADMAP.md`,
`.planning/STATE.md`) beslemek için bir girdi olarak kullanılacak — buradaki
maddeler olgunlaştıkça resmi roadmap'e faz olarak taşınabilir.

Durum etiketleri: `[ ]` açık, `[~]` kısmen yapıldı / devam ediyor, `[x]` tamam.

---

## 1. Algoritmik Kanıt / Coverage

- [ ] v2.7 milestone'ını Phase 77'ye (Cohort Rerun & Comparative Evaluation,
      n=3000) kadar bitir — "weak evidence" sınıflandırmasından çık.
- [ ] Action çeşitliliği gerçek olsun: tek action türü (`adjust_requested_loan_amount`)
      %100 dominance'tan çıkmalı (Phase 73-75 hedefi).
- [ ] Phase 77 sonrası tek bir "kanıt paketi" raporu üret (W2a baseline'a
      kıyasla coverage/movement/diversity/trust karşılaştırması).

## 2. Güvenlik / Veri İşleme Hijyeni

- [ ] `CREDIT_COACH_ALLOW_INSECURE_API=1` bypass'ını pilot/production path'inde
      hard-fail veya tamamen kaldır (`credit-coach/src/credit_coach/api/auth.py:171`).
- [ ] Telemetry export için auth/signed-request desteği ekle.
- [ ] Veri retention / encryption-at-rest / encryption-in-transit politikasını
      yazılı hale getir — kurum sorduğunda hazır cevap olsun.
- [ ] On-prem / kurum-sandbox'ında çalıştırılabilirlik için minimum deployment
      gereksinimlerini dokümante et.

## 3. Regülasyon / Hukuki Konumlandırma

- [ ] "Biz kredi kararı vermiyoruz, mevcut karara recourse/açıklama katmanı
      ekliyoruz" konumlandırmasını hukuki dile çevir (mevcut decision-ownership
      ve audit-chain katmanlarına dayanarak).
- [ ] Bu konumlandırma için hukuk/uyumluluk danışmanından görüş al.
- [ ] Adverse-action / ECOA-benzeri çerçevelerle ilişkiyi netleştiren kısa bir
      "ne değiliz" beyanı oluştur.

## 4. Kademeli Veri Talebi Stratejisi

- [ ] Kurumlara sunulacak 3 aşamalı veri talebi planını yaz:
  1. anonim/sentetik örnek veri ya da kurum sandbox'ında kod çalıştırma
  2. küçük anonim tarihsel kohort (örn. 500-1000 satır, PII'siz)
  3. daha geniş/canlı entegrasyon (sadece 1-2 başarılı olduktan sonra)
- [ ] Bu planı `PILOT_EXECUTION_GUIDE.md` ile hizala / referans ver.

## 5. Mühendislik Hardening (Due Diligence Bar'ı)

- [ ] `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
      (~4300 satır) parçala — en azından candidate generation / metrics /
      artifact writing ayrı modüllere.
- [ ] p95/p99 latency sayılarını somutlaştır ("N müşteri için X saniye")
      — kurum teknik ekibi bunu sorar.
- [ ] Config sprawl (`credit-coach/configs/experiments/`) için canonical
      experiment family + manifest.
- [ ] Schema/persistence drift için migration/version katmanı.

## 6. Sunulabilir Kanıt Paketi / Pilot Teklifi

- [ ] `INVESTOR_BRIEF.md`, `PILOT_PACKAGE_SCHEMA.md`,
      `DECISION_EXPLANATION_PACK.md` + Phase 77 raporunu tek bir
      "bu sistemi gördüğünüzde ne alırsınız" paketine birleştir.
- [ ] Bu paketin "leakage yok" kuralına (bkz. `PILOT_READINESS.md`) uyduğunu
      doğrula.

---

## Milestone Kapanışlarından Gelen Notlar

> Her milestone kapandığında, ortaya çıkan ve roadmap'e henüz girmemiş
> "yapılması gerekenler" buraya tarih ve kaynak fazla eklenir.

- (henüz not yok)

---

## Arşiv — Tamamlanan Maddeler

> Yukarıdaki listelerden `[x]` olan maddeler, referans için buraya
> tarih ve kısa not ile taşınabilir.

- (henüz yok)
