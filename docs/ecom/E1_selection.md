# E1 — Model ve ayar seçimi (yalnızca doğrulama kümesi)

Üretildi: `python -m credit_coach.ecom.e1_hillstrom select`. Bu belge test kümesi çalışmadan ÖNCE commit'lenir; commit sırası seçimin test sonucundan önce yapıldığının kanıtıdır. Test kümesi bu adımda okunmadı.

Bölme karması `8bd4e53c0df90ae360feb93d94d880c3c91109f596cef48fc6fa8edb913e8437`, eğitim kümesinde $p$ = 0,667101. Çalışma süresi 17,6 s.

## Izgara ve doğrulama Qini'si

Toplam 12 kombinasyon: 2 aile × öğrenme hızı {0,05; 0,1} × yaprak sayısı {7; 15; 31}; `max_iter` = 200, erken durdurma kapalı, `random_state` = 20261111. Ölçüt: doğrulama kümesinde Qini alanı (PLAN 2.2, yamuk kuralı, 100 nokta, N ile bölünmüş).

| Ayar | Aile | Öğrenme hızı | Yaprak | Doğrulama Qini |
|---|---|---|---|---|
| `T_lr0.05_leaf7_it200` **(seçilen)** | T | 0,05 | 7 | 0,000395 |
| `T_lr0.05_leaf15_it200` | T | 0,05 | 15 | 0,000359 |
| `T_lr0.05_leaf31_it200` | T | 0,05 | 31 | -0,000356 |
| `T_lr0.1_leaf7_it200` | T | 0,10 | 7 | -0,000370 |
| `T_lr0.1_leaf15_it200` | T | 0,10 | 15 | -0,000468 |
| `T_lr0.1_leaf31_it200` | T | 0,10 | 31 | -0,000205 |
| `TO_lr0.05_leaf7_it200` | TO | 0,05 | 7 | 0,000033 |
| `TO_lr0.05_leaf15_it200` | TO | 0,05 | 15 | -0,001563 |
| `TO_lr0.05_leaf31_it200` | TO | 0,05 | 31 | -0,001143 |
| `TO_lr0.1_leaf7_it200` | TO | 0,10 | 7 | -0,000726 |
| `TO_lr0.1_leaf15_it200` | TO | 0,10 | 15 | -0,001242 |
| `TO_lr0.1_leaf31_it200` | TO | 0,10 | 31 | -0,002374 |

> **Bu tablo ne demek:** Her ayarın doğrulama kümesinde Qini alanı; en yüksek olan seçildi (eşitlikte ızgara sırası).
>
> **Ne DEMEK DEĞİL:** Doğrulama Qini'si test sonucunu öngörmez; aynı küme hem ayar hem seçim için kullanıldığı için iyimser olabilir.

## Seçim

- **Kapı modeli (tek):** `T_lr0.05_leaf7_it200`.
- Ailelerin en iyileri (testte yan yana raporlanır, kapıya yalnızca kapı modeli girer): T = `T_lr0.05_leaf7_it200`, TO = `TO_lr0.05_leaf7_it200`.
- Belirlenimcilik: seçilen ayar aynı veri ve seed ile iki kez eğitildi; doğrulama tahminleri bit düzeyinde aynı: **evet**.

## Test kümesinde yapılacaklar (önceden kayıt)

- Modeller yalnızca eğitim kümesinde (doğrulama eklenmeden) yukarıdaki ayarlarla yeniden eğitilir; test kümesi bir kez tahmin edilir; `docs/ecom/test_run_hillstrom.lock` yazılır, kilit varsa komut reddeder.
- Kapı ölçütleri PLAN bölüm 6 E1 (DONDURULDU): Qini %95 alt sınırı > 0; kalibrasyon eğimi [0,5; 1,5] ve alt sınırı > 0; genel düzey farkı aralığı 0'ı içerir.
- Bootstrap B = 1000, tabakalı (tedavi ve kontrol ayrı), seed 20261111; desiller ham test kümesinde tau sırasına göre sabitlenir.
- Politika değeri tablosu (kapıya GİRMEZ, PLAN 2.3 ve 4.1): değer sonucu `spend`; kapı modelinin ailesi ve ayarı `spend` sonucunda (T ailesinde regresyon) yalnızca eğitim kümesinde ayar yapılmadan eğitilir; $\pi_{mod} = 1[g\,\hat\tau_{spend} - c > 0]$; destek dışı satırlarda (eğitimdeki %0,5–%99,5 aralığı dışında bir özellik) $\pi_{mod} = 1$; ızgara $g \in \{0{,}2; 0{,}3; 0{,}4\}$, $c \in \{0{,}01; 0{,}10; 0{,}50\}$; birincil hücre $g = 0{,}30$, $c = 0{,}10$.

<!-- SECIM-JSON-BASLANGIC -->
```json
{
 "secilen": "T_lr0.05_leaf7_it200",
 "secilen_aile": "T",
 "aile_en_iyi": {
  "T": "T_lr0.05_leaf7_it200",
  "TO": "TO_lr0.05_leaf7_it200"
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
 "bolme_karmasi": "8bd4e53c0df90ae360feb93d94d880c3c91109f596cef48fc6fa8edb913e8437",
 "p_egitim": 0.667101
}
```
<!-- SECIM-JSON-BITIS -->
