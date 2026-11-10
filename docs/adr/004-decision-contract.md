# ADR-004: Karar sözleşmesi ve politika tablosu

Durum: **Kabul edildi** (A, B, C kararları aşağıda işlendi).

## Amaç
Aynı girdi her zaman aynı kararı versin ve eski bir karar bayt düzeyinde yeniden üretilebilsin.
Bunun için karar bir saf fonksiyondur: `decide(girdi, politika) -> çıktı`. Saat, rastgelelik, ağ ve
dosya okuma karar fonksiyonunun içinde yoktur. Politika dosyadan önce yüklenir ve fonksiyona nesne
olarak verilir. Kayıt zamanı yalnızca kayıt katmanında atanır (3.3).

## Kabul edilen kararlar
- **A. Zayıf destek bayrağı türetilir.** `decide` bayrağı girdiden almaz; `ham_skor` ile politikadaki
  aralıklardan kendi içinde hesaplar. Böylece bayrak politika sürümüne bağlıdır ve yeniden
  oynatmada aynı sonucu verir. Aralık sınırları değişirse politika sürümü değişir.
- **B. Yakınlık kuralı `p_point` kullanır.** Venn-Abers nokta tahmini, AUC/ECE ve band'ı ölçtüğümüz
  kalibre PD ile aynı büyüklüktür; `|p_point - eşik| <= 3 x band` kuralı band ile tutarlıdır. Aralığın
  eşiği kesmesi (R2) ayrıca durur, ikisi birbirini tamamlar. `p_point` karar girdisidir.
- **C. Dışarıda `NEEDS_REVIEW -> CONDITIONAL`.** Belirsizlik yüzünden otomatik ret üretilmez.
  `conditional_type = DATA_ISSUE`. İç durum kayıtta `NEEDS_REVIEW` olarak kalır, dışarı sızmaz.
  *Kural istisnası:* plan bağlı CONDITIONAL sayısal bir `upgrade_condition` gerektirir (4. hafta).
  `DATA_ISSUE` alt türü için sayısal koşul yoktur; bunun yerine kapalı, açık bir süreç koşulu
  yazılır: `upgrade_condition = "HUMAN_REVIEW_COMPLETED"` ("insan incelemesi tamamlanmalı"). Bu,
  "finansal durum iyileşirse" türü belirsiz ifade yasağını delmez, çünkü koşul sabit ve doğrulanabilir.

## Karar girdisi (Pydantic, `extra="forbid"`, NaN/Inf yasak)

| Alan | Tür | Not |
|---|---|---|
| `basvuru` | izinli özellikler (manifestodan), hepsi zorunlu, değer `None` olabilir | yalnızca model girdisi; ad/kimlik alanı yok. `decide` bu alanları KULLANMAZ, kayıt için taşır |
| `p_low`, `p_point`, `p_high` | float, `0 <= p_low <= p_point <= p_high <= 1` | Venn-Abers aralığı ve nokta tahmini |
| `ham_skor` | float [0, 1] | modelin kalibre edilmemiş skoru |
| `politika_surumu` | str (örn. `"v1"`) | bilinmiyorsa veya verilen politikayla eşleşmiyorsa hata, varsayılan yok |
| `plan_available` | bool \| null | 4. haftaya kadar hep `null` |

## Karar çıktısı

Dış durum (3 değer): `APPROVED`, `CONDITIONAL`, `REJECTED`.
İç durum (4 değer): yukarıdakiler + `NEEDS_REVIEW`.

İki ayrı çıktı tipi: `InternalDecision` (kayıt ve yeniden oynatma, `ic_durum` içerir) ve
`PublicDecision` (dışarı verilen; tipinde `NEEDS_REVIEW` ve iç gerekçe kodları yoktur).
`InternalDecision` alanları: `dis_durum`, `ic_durum`, `gerekce_kodlari`, `tetiklenen_kurallar`,
`conditional_type`, `upgrade_condition`, `politika_surumu`.

### Gerekçe kodları (kapalı liste, bu sırayla sıralanır)

| Kod | İç durum | Dışarı açık mı |
|---|---|---|
| `PD_BELOW_THRESHOLD` | APPROVED | evet |
| `PD_ABOVE_THRESHOLD` | REJECTED veya CONDITIONAL | evet |
| `PLAN_AVAILABLE` | CONDITIONAL (plan bağlı, 4. hafta) | evet |
| `NO_PLAN_AVAILABLE` | REJECTED (`plan_available == false`) | evet |
| `REVIEW_REQUIRED` | NEEDS_REVIEW | evet |
| `HARD_REJECT_THRESHOLD` | REJECTED (ret eşiği, v1'de pasif) | evet |
| `INTERVAL_STRADDLES_THRESHOLD` | NEEDS_REVIEW | hayır, yalnızca kayıt |
| `WITHIN_BAND_OF_THRESHOLD` | NEEDS_REVIEW | hayır, yalnızca kayıt |
| `WEAK_SUPPORT_NEAR_THRESHOLD` | NEEDS_REVIEW | hayır, yalnızca kayıt |

Her kararda en az bir kod vardır.

## Kural sırası

R1, R2 ve R3 birbirinden bağımsız değerlendirilir; eşleşenlerin hepsi `tetiklenen_kurallar`'a yazılır.
Durumu belirleyen öncelik: R1 > (R2 veya R3) > son kural. R4, R5, R6 son kurallardır: yalnızca
R1-R3'ün hiçbiri eşleşmediğinde tam biri tetiklenir.

| # | Kural kimliği | Koşul | İç durum | Kod |
|---|---|---|---|---|
| 0 | `R0_PRECONDITIONS` | sürüm biliniyor ve eşleşiyor, `0 <= p_low <= p_point <= p_high <= 1`, `ham_skor` [0,1], NaN yok | ihlalde HATA (karar yok) | yok |
| 1 | `R1_HARD_REJECT` | `ret_esigi != null` ve `p_low > ret_esigi` | REJECTED | `HARD_REJECT_THRESHOLD` (v1'de ret eşiği null, pasif) |
| 2 | `R2_THRESHOLD_BAND` | aralık, her iki yanda `band` genişletilince eşiği içeriyor | NEEDS_REVIEW | `REVIEW_REQUIRED` + (`INTERVAL_STRADDLES_THRESHOLD` eğer `p_low <= eşik <= p_high`, değilse `WITHIN_BAND_OF_THRESHOLD`) |
| 3 | `R3_WEAK_SUPPORT_NEAR` | `ham_skor` zayıf destek aralığında VE `\|p_point - eşik\| <= 3 x band` | NEEDS_REVIEW | `REVIEW_REQUIRED` + `WEAK_SUPPORT_NEAR_THRESHOLD` |
| 4 | `R4_APPROVE` | (R1-R3 yok) ve `p_high < onay_esigi` | APPROVED | `PD_BELOW_THRESHOLD` |
| 5 | `R5_NOT_APPROVED_PLAN` | (R1-R3 yok), R4 sağlanmadı ve `plan_available == true` | CONDITIONAL (plan bağlı) | `PD_ABOVE_THRESHOLD`, `PLAN_AVAILABLE` |
| 6 | `R6_NOT_APPROVED` | diğer tüm durumlar | REJECTED | `PD_ABOVE_THRESHOLD` (+ `NO_PLAN_AVAILABLE` eğer `plan_available == false`) |

R1-R3 durumu NEEDS_REVIEW iken dış durum `CONDITIONAL`, `conditional_type = DATA_ISSUE`,
`upgrade_condition = "HUMAN_REVIEW_COMPLETED"`.

Girdi hataları (R0) açık hata fırlatır (`InvalidDecisionInput`); sessiz karar ve varsayılan yok. Hata,
karar kaydına NEEDS_REVIEW olarak yazılmaz; karar kaydına yalnızca geçerli girdili kararlar girer.

## Politika tablosu: `configs/policy/v1.yaml`

```yaml
surum: v1
kural_sirasi: [R1_HARD_REJECT, R2_THRESHOLD_BAND, R3_WEAK_SUPPORT_NEAR, R4_APPROVE, R5_NOT_APPROVED_PLAN, R6_NOT_APPROVED]
onay_esigi: <cost.yaml'dan türeyen sayı>
band: <decision.yaml>
zayif_destek_araliklari: [[a, b], ...]
zayif_destek_yakinlik_carpani: 3
ret_esigi: null                # 4. haftada recourse fizibilitesinden türetilecek
kaynak: {cost_yaml_sha256, decision_yaml_sha256, getiri, kayip, hurdle}
```

- `decide` dosya okumaz; `load_policy(surum)` ayrı bir fonksiyondur ve bilinmeyen sürümde hata verir.
- Politika dosyasının SHA-256'sı `bundle.lock.json`'a girer. v1 commit'teki hâliyle dondurulur.
- Eşik politika üretilirken `cost.yaml`'dan çözümsel hesaplanır, test eşitliği doğrular.
- `ret_esigi` doluysa `onay_esigi`'nden büyük olmak zorundadır.
- 4. haftada `v2.yaml` (ret eşiği dolu, `plan_available` bağlı) eklenir; v1 dokunulmaz kalır.

## Ön koşul bulguları (insana-git oranı)

Kalibrasyon diliminde nihai kuralla insana-git oranı: leave-one-month-out aralıklarla %1,88,
dondurulmuş kalibratörle %0,12. Test dilimi de %0,12. Fark hata değil: iki farklı kalibratör.
İzotonik basamakların konumu, eşiğin (0,109) ±band penceresine kaç kaydın düştüğünü belirliyor.
`R3` bu eşikte hiç tetiklenmiyor (zayıf destek aralıkları eşikten uzakta); v1'de yalnızca sentetik
senaryolarla tetiklenebilir.

## Kayıt ve replay notları (3.3, 3.4)
- **Üretim uyarısı:** üretimde `cc_app` şifresi ve veritabanı sahibi rolü ayrılmalı; migration'daki
  `cc_app_dev` yalnızca geliştirme varsayılanıdır. Sahip rolü trigger'ı kapatabilir; bunu yalnızca
  zincir doğrulaması (`verify_chain`) ve replay yakalar.
- **Replay kapsamı:** yalnızca karar katmanı (`decide`). Kayıt `p_low/p_point/p_high/ham_skor`
  değerlerini girdi olarak taşır; model ve skor üretimi yeniden çalıştırılmaz. Skor katmanı için ayrı kontrol
  gerekir (henüz yok).
- Her kayıt `politika_sha256` (politika dosyası) ve `bundle_sha256` (`bundle.lock.json`) taşır.
  Politika dosyası hash'i uymazsa replay durur; bundle farkı yalnızca raporlanır.
