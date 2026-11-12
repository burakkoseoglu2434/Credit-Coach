# E2 — Model ve ayar seçimi (yalnızca doğrulama kümesi)

Üretildi: `python -m credit_coach.ecom.e2_criteo select`. Bu belge test kümesi çalışmadan ÖNCE commit'lenir; commit sırası seçimin test sonucundan önce yapıldığının kanıtıdır. Test kümesi bu adımda okunmadı.

Bölme karması `c5fa21e7aef3581fb4c76be0c55fe44e78148e9a3ae02eece3d24b9d0e43a1ef`, eğitim kümesinde $p$ = 0,850000. Toplam çalışma süresi 11,4 dk; tepe bellek 2,52 GiB (sınır: fiziksel belleğin %80'i).

## Izgara ve doğrulama Qini'si

E1 ile aynı ızgara: toplam 12 kombinasyon (2 aile × öğrenme hızı {0,05; 0,1} × yaprak {7; 15; 31}); `max_iter` = 200, erken durdurma kapalı, `random_state` = 20261111. Ölçüt: doğrulama Qini alanı. Eğitim süresi sütunu tek ayarın tüm eğitimidir (T ailesinde iki model); sınır 60 dk.

| Ayar | Aile | Öğrenme hızı | Yaprak | Doğrulama Qini | Eğitim süresi (s) |
|---|---|---|---|---|---|
| `T_lr0.05_leaf7_it200` | T | 0,05 | 7 | 0,003112 | 46,9 |
| `T_lr0.05_leaf15_it200` | T | 0,05 | 15 | 0,003199 | 61,9 |
| `T_lr0.05_leaf31_it200` | T | 0,05 | 31 | 0,003173 | 79,3 |
| `T_lr0.1_leaf7_it200` | T | 0,10 | 7 | 0,003200 | 49,6 |
| `T_lr0.1_leaf15_it200` | T | 0,10 | 15 | 0,003136 | 62,3 |
| `T_lr0.1_leaf31_it200` | T | 0,10 | 31 | 0,003080 | 68,8 |
| `TO_lr0.05_leaf7_it200` | TO | 0,05 | 7 | 0,003389 | 38,1 |
| `TO_lr0.05_leaf15_it200` | TO | 0,05 | 15 | 0,003359 | 37,5 |
| `TO_lr0.05_leaf31_it200` | TO | 0,05 | 31 | 0,003373 | 38,5 |
| `TO_lr0.1_leaf7_it200` | TO | 0,10 | 7 | 0,003340 | 32,9 |
| `TO_lr0.1_leaf15_it200` **(seçilen)** | TO | 0,10 | 15 | 0,003391 | 34,8 |
| `TO_lr0.1_leaf31_it200` | TO | 0,10 | 31 | 0,003315 | 36,7 |

> **Bu tablo ne demek:** Her ayarın doğrulama kümesinde Qini alanı ve eğitim süresi; en yüksek Qini seçildi.
>
> **Ne DEMEK DEĞİL:** Doğrulama Qini'si test sonucunu öngörmez; aynı küme hem ayar hem seçim için kullanıldığı için iyimser olabilir.

## Desil dengesi (doğrulama kümesi; yalnızca tedavi ataması)

Eşitlik kuralı PLAN 2.1 sonradan notuna göre: sıralama $(-\hat\tau,\ \text{anahtar})$, anahtar = splitmix64(satır kimliği, seed 20261111). Karşılaştırma için eski kural (satır kimliği) da gösterilir. Genel kontrol payı 0,150.

| Model | Ayar | En büyük eşit blok | Kural | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T | `T_lr0.1_leaf7_it200` | 0,0501 | anahtar (yeni) | 0,135 | 0,149 | 0,154 | 0,154 | 0,151 | 0,152 | 0,152 | 0,151 | 0,151 | 0,152 |
| T | `T_lr0.1_leaf7_it200` | 0,0501 | satır kimliği (eski) | 0,135 | 0,149 | 0,154 | 0,154 | 0,147 | 0,151 | 0,150 | 0,129 | 0,176 | 0,156 |
| TO | `TO_lr0.1_leaf15_it200` | 0,4002 | anahtar (yeni) | 0,133 | 0,150 | 0,153 | 0,153 | 0,155 | 0,152 | 0,151 | 0,151 | 0,151 | 0,151 |
| TO | `TO_lr0.1_leaf15_it200` | 0,4002 | satır kimliği (eski) | 0,133 | 0,150 | 0,147 | 0,160 | 0,136 | 0,125 | 0,000 | 0,000 | 0,510 | 0,139 |

> **Bu tablo ne demek:** Doğrulama kümesinde tahmine göre sıralanmış desillerde kontrol grubunun payı; rastgele atamada her desilde genel paya yakın olması beklenir.
>
> **Ne DEMEK DEĞİL:** Sonuç değişkeni kullanılmadı; bu tablo modelin isabeti hakkında bir şey söylemez, yalnızca sıralama kuralının tedaviyi desillere dengeli dağıtıp dağıtmadığını gösterir.

## Seçim

- **Kapı modeli (tek):** `TO_lr0.1_leaf15_it200`.
- Ailelerin en iyileri (testte yan yana): T = `T_lr0.1_leaf7_it200`, TO = `TO_lr0.1_leaf15_it200`.
- Belirlenimcilik: seçilen ayar iki kez eğitildi; doğrulama tahminleri bit düzeyinde aynı: **evet**.
- Bootstrap süre ölçümü (doğrulama kümesi, 20 adım, testteki hesapların aynısı): adım başına 1,054 s; B = 1000 için öngörülen 17,6 dk. Sınır 2 saat; aşarsa test çalıştırılmaz, kullanıcıya sorulur.

## Test kümesinde yapılacaklar (önceden kayıt)

- Modeller yalnızca eğitim kümesinde yukarıdaki ayarlarla yeniden eğitilir; test kümesi bir kez tahmin edilir; `docs/ecom/test_run_criteo.lock` yazılır, kilit varsa komut reddeder.
- Kapı ölçütleri PLAN bölüm 6 E2 (DONDURULDU): Qini %95 alt sınırı > 0; kalibrasyon eğimi [0,7; 1,3]; en az 8/10 desilde $|\Delta_d| \le 0{,}25\,|\tau^{obs}_{test}|$ ya da $\Delta_d$'nin %95 aralığı 0'ı içerir.
- Bootstrap B = 1000, tabakalı, seed 20261111; desiller ham test kümesinde sabit.
- Politika değeri tablosu (kapıya GİRMEZ, PLAN 2.3, 4.2): değer sonucu `conversion`, birim $m$ (dönüşüm başına değer); kapı modelinin ailesi ve ayarı `conversion` üzerinde yalnızca eğitimde, ayar yapılmadan eğitilir; $\pi_{mod} = 1[\hat\tau_{conv} > k]$, destek dışı satırlarda 1; $k \in \{0{,}0001; 0{,}0003; 0{,}001; 0{,}003; 0{,}01\}$, birincil $k = 0{,}001$.
- İkincil duyarlılık analizi (kapıya GİRMEZ, ön kayıt `e54c9cd`): $\hat p(x)$ eğitim kümesinde `HistGradientBoostingClassifier` (öğrenme hızı 0,1, `max_leaf_nodes` 31, `max_iter` 200, erken durdurma kapalı, `random_state` 20261111); test satırlarından $\hat p(x) < 0{,}01$ ya da $> 0{,}99$ olanlar kırpılır, oran raporlanır; ağırlık tedavide $1/\hat p$, kontrolde $1/(1-\hat p)$. Raporlanan: özellik başına ham ve ağırlıklı SMD, ham ve ağırlıklı genel `visit` farkı, kapı modelinin ham (tüm test ve kırpılmış) ve ağırlıklı Qini alanı (nokta tahmini).

<!-- SECIM-JSON-BASLANGIC -->
```json
{
 "secilen": "TO_lr0.1_leaf15_it200",
 "secilen_aile": "TO",
 "aile_en_iyi": {
  "T": "T_lr0.1_leaf7_it200",
  "TO": "TO_lr0.1_leaf15_it200"
 },
 "ayarlar": {
  "T_lr0.05_leaf7_it200": {
   "aile": "T",
   "learning_rate": 0.05,
   "max_leaf_nodes": 7,
   "max_iter": 200
  },
  "T_lr0.05_leaf15_it200": {
   "aile": "T",
   "learning_rate": 0.05,
   "max_leaf_nodes": 15,
   "max_iter": 200
  },
  "T_lr0.05_leaf31_it200": {
   "aile": "T",
   "learning_rate": 0.05,
   "max_leaf_nodes": 31,
   "max_iter": 200
  },
  "T_lr0.1_leaf7_it200": {
   "aile": "T",
   "learning_rate": 0.1,
   "max_leaf_nodes": 7,
   "max_iter": 200
  },
  "T_lr0.1_leaf15_it200": {
   "aile": "T",
   "learning_rate": 0.1,
   "max_leaf_nodes": 15,
   "max_iter": 200
  },
  "T_lr0.1_leaf31_it200": {
   "aile": "T",
   "learning_rate": 0.1,
   "max_leaf_nodes": 31,
   "max_iter": 200
  },
  "TO_lr0.05_leaf7_it200": {
   "aile": "TO",
   "learning_rate": 0.05,
   "max_leaf_nodes": 7,
   "max_iter": 200
  },
  "TO_lr0.05_leaf15_it200": {
   "aile": "TO",
   "learning_rate": 0.05,
   "max_leaf_nodes": 15,
   "max_iter": 200
  },
  "TO_lr0.05_leaf31_it200": {
   "aile": "TO",
   "learning_rate": 0.05,
   "max_leaf_nodes": 31,
   "max_iter": 200
  },
  "TO_lr0.1_leaf7_it200": {
   "aile": "TO",
   "learning_rate": 0.1,
   "max_leaf_nodes": 7,
   "max_iter": 200
  },
  "TO_lr0.1_leaf15_it200": {
   "aile": "TO",
   "learning_rate": 0.1,
   "max_leaf_nodes": 15,
   "max_iter": 200
  },
  "TO_lr0.1_leaf31_it200": {
   "aile": "TO",
   "learning_rate": 0.1,
   "max_leaf_nodes": 31,
   "max_iter": 200
  }
 },
 "belirlenimcilik_bit_esit": true,
 "bolme_karmasi": "c5fa21e7aef3581fb4c76be0c55fe44e78148e9a3ae02eece3d24b9d0e43a1ef",
 "p_egitim": 0.85,
 "egitim_sureleri_s": {
  "T_lr0.05_leaf7_it200": 46.9,
  "T_lr0.05_leaf15_it200": 61.9,
  "T_lr0.05_leaf31_it200": 79.3,
  "T_lr0.1_leaf7_it200": 49.6,
  "T_lr0.1_leaf15_it200": 62.3,
  "T_lr0.1_leaf31_it200": 68.8,
  "TO_lr0.05_leaf7_it200": 38.1,
  "TO_lr0.05_leaf15_it200": 37.5,
  "TO_lr0.05_leaf31_it200": 38.5,
  "TO_lr0.1_leaf7_it200": 32.9,
  "TO_lr0.1_leaf15_it200": 34.8,
  "TO_lr0.1_leaf31_it200": 36.7
 },
 "tepe_bellek_gib": 2.52,
 "desil_dengesi": {
  "T": {
   "ayar": "T_lr0.1_leaf7_it200",
   "en_buyuk_esit_blok": 0.05014989709998648,
   "kontrol_payi_anahtar": [
    0.13468911842971187,
    0.14938195656528083,
    0.15351655269106412,
    0.15392071303899968,
    0.15136753328969815,
    0.1515136341526224,
    0.15152436407336403,
    0.1508340725056511,
    0.15095567827405648,
    0.15229388642695937
   ],
   "kontrol_payi_satir_kimligi": [
    0.13468554178946465,
    0.14938910984577528,
    0.1535129760508169,
    0.15397793928295517,
    0.1472937254775726,
    0.1506910068957624,
    0.15012947437694926,
    0.12881269850353372,
    0.17552719677243983,
    0.15597783905776652
   ]
  },
  "TO": {
   "ayar": "TO_lr0.1_leaf15_it200",
   "en_buyuk_esit_blok": 0.40017232265037816,
   "kontrol_payi_anahtar": [
    0.13283284214140606,
    0.15022962030387135,
    0.15280122464162066,
    0.1531839251480729,
    0.15475104706517734,
    0.15206086011044664,
    0.1514134882257003,
    0.15070531345675126,
    0.1508591089873816,
    0.15116008741340028
   ],
   "kontrol_payi_satir_kimligi": [
    0.13283999542190048,
    0.1502367735843658,
    0.14697487767890355,
    0.15986866577012218,
    0.136055881627091,
    0.12541131362843,
    0.0,
    0.0,
    0.5099967094909725,
    0.1386131885504183
   ]
  }
 },
 "kontrol_payi_genel": 0.14999974963500362,
 "bootstrap_adim_s": 1.054,
 "bootstrap_ongorulen_s": 1054.0
}
```
<!-- SECIM-JSON-BITIS -->
