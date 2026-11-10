# ADR-004: Karar sözleşmesi ve politika tablosu

Durum: TASLAK, onay bekliyor. Kod yazılmadı.

## Amaç
Aynı girdi her zaman aynı kararı versin ve eski bir karar bayt düzeyinde yeniden üretilebilsin.
Bunun için karar bir saf fonksiyondur: `decide(girdi, politika) -> çıktı`. Saat, rastgelelik, ağ ve
dosya okuma karar fonksiyonunun içinde yoktur. Politika dosyadan önce yüklenir ve fonksiyona nesne
olarak verilir. Kayıt zamanı yalnızca kayıt katmanında atanır (3.3).

## Karar girdisi (Pydantic, `extra="forbid"`)

| Alan | Tür | Not |
|---|---|---|
| `basvuru` | izinli özellikler (manifestodan) | yalnızca model girdisi; ad/kimlik alanı yok. `decide` bu alanları KULLANMAZ, kayıt için taşır |
| `p_low`, `p_high` | float, `0 <= p_low <= p_high <= 1` | Venn-Abers aralığı |
| `ham_skor` | float [0, 1] | modelin kalibre edilmemiş skoru |
| `politika_surumu` | str (örn. `"v1"`) | bilinmiyorsa hata, varsayılan yok |
| `plan_available` | bool \| null | 4. haftaya kadar hep `null` |

**Açık karar (A):** istediğin listede `zayıf_destek bayrağı` girdi alanıydı. Önerim: bayrağı girdiye
koymamak, `decide` içinde `ham_skor` ve politikadaki aralıklardan türetmek. İki doğruluk kaynağı
(bayrak ve skor) çelişebilir. Girdide istersen, `decide` bayrağı yeniden türetip çelişkide hata verir.

**Açık karar (B):** zayıf destek yakınlık kuralı şu an nokta tahmini kullanıyor. Sözleşmede nokta
tahmini girdi değil; öneri: aralık orta noktası `(p_low + p_high) / 2` (aralıklar ~0,0005 geniş, fark
ihmal edilebilir). Eşik rapordaki sayıları değiştirmez, yalnızca golden set'i bunun üstüne kurar.

## Karar çıktısı

Dış durum (3 değer): `APPROVED`, `CONDITIONAL`, `REJECTED`.
İç durum (4 değer): yukarıdakiler + `NEEDS_REVIEW`.

İki ayrı çıktı tipi vardır: `InternalDecision` (kayıt ve yeniden oynatma, `ic_durum` içerir) ve
`PublicDecision` (dışarı verilen, `dis_durum` içerir, tipinde `NEEDS_REVIEW` yoktur).

**NEEDS_REVIEW -> dış durum eşlemesi (Açık karar C):** dışarıda 3 değerden biri görünmek zorunda.
Önerim `NEEDS_REVIEW -> CONDITIONAL`, gerekçe kodu `REVIEW_REQUIRED`: "onay, bir insan değerlendirmesine
bağlı". Böylece CONDITIONAL "bir koşula bağlı onay" anlamını taşır; koşul v1'de insan incelemesi,
4. haftadan sonra ek olarak müşteri planıdır. Alternatif: NEEDS_REVIEW -> REJECTED (güvenli ama
haksız ret görüntüsü). Onayına göre.

`gerekce_kodlari`: sabit enum, aşağıda. `tetiklenen_kurallar`: tetiklenen kural kimlikleri, kural
sırasına göre.

### Gerekçe kodları (kapalı liste)

| Kod | İç durum | Dışarı açık mı |
|---|---|---|
| `PD_BELOW_THRESHOLD` | APPROVED | evet |
| `PD_ABOVE_THRESHOLD` | REJECTED veya CONDITIONAL | evet |
| `PLAN_AVAILABLE` | CONDITIONAL (4. hafta) | evet |
| `NO_PLAN_AVAILABLE` | REJECTED (`plan_available == false`) | evet |
| `REVIEW_REQUIRED` | NEEDS_REVIEW | evet |
| `HARD_REJECT_THRESHOLD` | REJECTED (ret eşiği, v1'de pasif) | evet |
| `INTERVAL_STRADDLES_THRESHOLD` | NEEDS_REVIEW | hayır, yalnızca kayıt |
| `WITHIN_BAND_OF_THRESHOLD` | NEEDS_REVIEW | hayır, yalnızca kayıt |
| `WEAK_SUPPORT_NEAR_THRESHOLD` | NEEDS_REVIEW | hayır, yalnızca kayıt |

Her kararda en az bir kod vardır.

## Kural sırası (ilk eşleşen durumu belirler; eşleşen tüm kurallar `tetiklenen_kurallar`'a yazılır)

| # | Kural kimliği | Koşul | İç durum | Kod |
|---|---|---|---|---|
| 0 | `R0_PRECONDITIONS` | sürüm biliniyor, `0 <= p_low <= p_high <= 1`, `ham_skor` [0,1] | ihlalde HATA (karar yok) | yok |
| 1 | `R1_HARD_REJECT` | `ret_esigi != null` ve `p_low > ret_esigi` | REJECTED | `HARD_REJECT_THRESHOLD` (v1'de ret eşiği null, pasif) |
| 2 | `R2_THRESHOLD_BAND` | aralık, her iki yanda `band` genişletilince eşiği içeriyor | NEEDS_REVIEW | `INTERVAL_STRADDLES_THRESHOLD` (`p_low <= eşik <= p_high`) yoksa `WITHIN_BAND_OF_THRESHOLD`, her ikisinde `REVIEW_REQUIRED` |
| 3 | `R3_WEAK_SUPPORT_NEAR` | `ham_skor` zayıf destek aralığında VE `\|orta nokta - eşik\| <= 3 x band` | NEEDS_REVIEW | `WEAK_SUPPORT_NEAR_THRESHOLD`, `REVIEW_REQUIRED` |
| 4 | `R4_APPROVE` | `p_high < onay_esigi` | APPROVED | `PD_BELOW_THRESHOLD` |
| 5 | `R5_NOT_APPROVED_PLAN` | R4 sağlanmadı ve `plan_available == true` | CONDITIONAL | `PD_ABOVE_THRESHOLD`, `PLAN_AVAILABLE` |
| 6 | `R6_NOT_APPROVED` | diğer tüm durumlar | REJECTED | `PD_ABOVE_THRESHOLD` (+ `NO_PLAN_AVAILABLE` eğer `plan_available == false`) |

Girdi hataları (R0) açık hata fırlatır (`InvalidDecisionInput`); sessiz karar ve varsayılan yok.
Hata, karar kaydına NEEDS_REVIEW olarak yazılmaz. Karar kaydına yalnızca geçerli girdili kararlar
girer; hatalı girdi ayrı bir günlükte tutulur (3.3'te ele alınır).

## Politika tablosu: `configs/policy/v1.yaml`

```yaml
surum: v1
kural_sirasi: [R1_HARD_REJECT, R2_THRESHOLD_BAND, R3_WEAK_SUPPORT_NEAR, R4_APPROVE, R5_NOT_APPROVED_PLAN, R6_NOT_APPROVED]
onay_esigi: 0.1092...          # cost.yaml'dan türeyen sayı, dosyaya çözümlenmiş yazılır
band: 0.00272...               # decision.yaml
zayif_destek_araliklari: [[0.0037, 0.0462], [0.2571, 0.7817]]
zayif_destek_yakinlik_carpani: 3
ret_esigi: null                # 4. haftada recourse fizibilitesinden türetilecek
kaynak: {cost_yaml_sha256, decision_yaml_sha256, getiri, kayip, hurdle}
```

- `decide` dosya okumaz; `load_policy(surum)` ayrı bir fonksiyondur ve bilinmeyen sürümde hata verir.
- Politika dosyasının SHA-256'sı `bundle.lock.json`'a girer. v1 commit'teki hâliyle dondurulur.
- Eşik, politika üretilirken `cost.yaml`'dan çözümsel olarak hesaplanır ve test eşitliği doğrular.
- 4. haftada `v2.yaml` (ret eşiği dolu, `plan_available` bağlı) eklenir; v1 dokunulmaz kalır.

## Ön koşul bulguları (2. adım: insana-git oranı)

Kalibrasyon diliminde nihai kuralla insana-git oranı: leave-one-month-out aralıklarla **%1,88**,
dondurulmuş (tüm kalibrasyon dilimiyle eğitilmiş) kalibratörle **%0,12**. Test dilimi de %0,12.
Fark hata değil: iki farklı kalibratör. İzotonik basamakların konumu, eşiğin (0,109) ±band (0,0027)
penceresine kaç kaydın düştüğünü belirliyor. Dolayısıyla insana-git oranı eşiğin basamaklara
göre konumuna duyarlıdır, düzgün bir ölçü değildir. Ayrıca `R3` (zayıf destek yakınlığı) bu eşikte
hiç tetiklenmiyor (zayıf destek aralıkları eşikten uzakta); v1'de yalnızca sentetik testle
tetiklenebilir.
