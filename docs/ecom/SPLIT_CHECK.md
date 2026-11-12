# Bölme yöntemi denetimi (E1 Hillstrom, E2 Criteo)

Salt okunur doğrulama, 2026-11-13. Taban: `ecom-summary` (021872f). Kod, config, kilit dosyası ve
rapor değiştirilmedi; E1/E2 sonuçları yeniden çalıştırılmadı ve değişmez.

**Soru.** ADR-008 ve PLAN 3.1 bölmeyi "satır kimliğinin sabit karmasıyla" diye tanımlıyor;
`uplift.stratified_split` ise tabaka içinde seed'li permütasyon kullanıyor. Kayıtlı bölme
karmaları hangi yöntemle üretildi?

## Sonuç

| Set | Kayıtlı karma (`configs/ecom_data_source.yaml` = `test_run_*.lock`) | (a) satır kimliği karması | (b) seed'li permütasyon | Eşleşen |
|---|---|---|---|---|
| Hillstrom (E1) | `8bd4e53c0df90ae360feb93d94d880c3c91109f596cef48fc6fa8edb913e8437` | `1ad0d05b8af1b6646bc07bde623adb015f6ea23a0d1d7e9ba76d7af1aad35693` | `8bd4e53c0df90ae360feb93d94d880c3c91109f596cef48fc6fa8edb913e8437` | **(b)** |
| Criteo (E2) | `c5fa21e7aef3581fb4c76be0c55fe44e78148e9a3ae02eece3d24b9d0e43a1ef` | `065fed7f176b994b5189d9f0378756b998cd189497de669d52e0c5893dd16ee3` | `c5fa21e7aef3581fb4c76be0c55fe44e78148e9a3ae02eece3d24b9d0e43a1ef` | **(b)** |

- yaml'daki `bolme_hillstrom.karma` ile `test_run_hillstrom.lock` içindeki `bolme_karmasi` aynı;
  `bolme_criteo.karma` ile `test_run_criteo.lock` içindeki de aynı.
- Küme büyüklükleri iki yöntemde de aynı (aynı yuvarlama kuralı): Hillstrom 38.399 / 12.799 /
  12.802, Criteo 8.387.755 / 2.795.918 / 2.795.919. Bunlar yaml'daki `satir` değerleriyle aynı.
- (a) ile (b)'nin aynı etiketi verdiği satır payı: Hillstrom 0,4409, Criteo 0,4399. İki bağımsız
  0,6/0,2/0,2 ataması için beklenen pay 0,6² + 0,2² + 0,2² = 0,44. Yani (a), (b)'nin küçük bir
  çeşidi değil; ayrı bir bölme.
- Girdi dosyalarının SHA-256'sı kayıtlı değerlerle aynı (Hillstrom
  `0e589332…f291aece`, Criteo gz `2716e1bf…f616dc`).

**Bulgu:** E1 ve E2 bölmeleri (b) **tabaka içinde seed'li permütasyon** ile üretilmiştir. yaml'daki
`yontem` alanı ("tabaka (tedavi x visit) içinde seed'li permütasyon; satır kimliği = dosya sırası")
bununla tutarlı. ADR-008 Karar 1'deki ve PLAN 3.1'deki "satır kimliğinin sabit karmasıyla"
ifadesi uygulanan yöntemi tarif etmiyor.

> **Bu sonuç ne demek:** Kayıtlı karmalar `uplift.stratified_split` (seed 20261111, `numpy.random.default_rng`, tabaka = tedavi × visit) çıktısıyla bit düzeyinde aynı. Kilitli test çalıştırmaları bu bölme üzerinde yapıldı.
>
> **Ne DEMEK DEĞİL:** E1/E2 sonuçlarının yanlış olduğunu söylemez; bölme belirlenimci ve kayıtlı karmayla yeniden üretilebilir. Permütasyon yönteminin karma yönteminden daha iyi ya da kötü olduğunu da söylemez. Uyuşmazlık belge ile kod arasında.

## Yöntemler

**(b) Seed'li permütasyon (uygulanan).** Depodaki kod olduğu gibi çağrıldı:
`e1_hillstrom.make_split(a)` ve `e2_criteo.make_split(a)`. Bunlar
`uplift.stratified_split(t*2 + visit)` çağırır: `rng = default_rng(20261111)`, sonra tabakalar
artan sırada gezilir ve her tabakanın satır kimlikleri (dosya sırası) `rng.permutation` ile
karıştırılır. İlk `round(0,6·n)` eğitime, sonraki `round(0,2·n)` doğrulamaya, kalanı teste
atanır. Karma `uplift.split_hash`: etiket dizisinin (int8, satır sırasında) SHA-256'sı.

**(a) Satır kimliği karması (ADR-008 okuması).** ADR-008 ve PLAN 3.1 hangi karma fonksiyonunu ve
karmadan kümeye nasıl geçileceğini belirtmiyor. Kod geçmişinde de (`d384dde`, `943826c`) bu
yöntemle bölme yapan bir uygulama yok. Bu yüzden şu somut okuma kullanıldı. Depodaki tek satır
kimliği karması `uplift.tie_key` (splitmix64, satır kimliği + seed 20261111). Aynı tabakalarda
satırlar bu anahtara göre sıralandı; sayılar (b) ile aynı yuvarlama kuralıyla 0,6/0,2/0,2 atandı.
Karma yine `split_hash` ile alındı.

> **Bu bölüm ne demek:** (b) depodaki fonksiyonun kendisi; (a) belgedeki tarifin depodaki karma fonksiyonuyla yapılmış tek bir somut okuması.
>
> **Ne DEMEK DEĞİL:** (a)'nın eşleşmemesi, "satır kimliği karması" ile yapılabilecek **her** bölmenin kayıtlı karmayla uyuşmadığını kanıtlamaz; başka bir karma fonksiyonu ya da atama kuralı farklı bir karma verirdi. Ama (b) bit düzeyinde eşleştiği için bölmenin hangi yöntemle üretildiği bu denetimde açık değil, belirlidir.

## Açık kalan

- ADR-008 Karar 1 ve PLAN 3.1'deki ifade, uygulanan yöntemle (seed'li permütasyon) uyuşmuyor. Bu
  belge hiçbirini değiştirmez. Düzeltme (ADR'ye "Sonradan" notu ya da yeni ADR) ayrı bir karar.
- PLAN 6'daki E2 durdurma kuralı ("satır kimliği karmasına göre ilk %25" alt örnek) da bir satır
  kimliği karmasından söz ediyor. Bu yol E2'de kullanılmadı; hangi karmanın kastedildiği belirtilmemiş.
- Bu belge `test_forbidden_phrases.py` tarama listesinde değil; listeye eklemek kod değişikliği
  olduğu için yapılmadı.

## Yeniden üretim

Veri dosyaları `configs/ecom_data_source.yaml`'daki yollarda. Betik depoya eklenmedi; aşağıda
aynen veriliyor. `backend/` içinden `PYTHONPATH=src uv run python splitcheck.py hillstrom|criteo`
ile çalışır (Hillstrom < 1 sn, Criteo ≈ 12 sn).

```python
import sys, numpy as np
from pathlib import Path
from credit_coach.ecom import uplift as U, e1_hillstrom as E1, e2_criteo as E2

def by_key(strata, seed=U.SEED, fracs=U.FRACS):
    labels = np.full(len(strata), -1, dtype=np.int8)
    key = U.tie_key(np.arange(len(strata)), seed)
    for s in np.unique(strata):
        idx = np.flatnonzero(strata == s)
        order = idx[np.argsort(key[idx], kind="stable")]
        n_tr = int(round(fracs[0] * len(idx))); n_va = int(round(fracs[1] * len(idx)))
        labels[order[:n_tr]] = U.TRAIN
        labels[order[n_tr:n_tr + n_va]] = U.VALID
        labels[order[n_tr + n_va:]] = U.TEST
    return labels

which = sys.argv[1]
if which == "hillstrom":
    src = E1.load_sources(); a = E1.arrays(E1.load_hillstrom(Path(src["hillstrom"]["yol"]))); mk = E1.make_split
else:
    src = E2.load_sources(); a = E2.load_criteo(Path(src["criteo_uplift"]["yol"])); mk = E2.make_split
strata = a["t"] * 2 + a["visit"].astype(np.int64)
lb, la = mk(a), by_key(strata)
print("b", U.split_hash(lb)); print("a", U.split_hash(la)); print("ayni_pay", (la == lb).mean())
```
