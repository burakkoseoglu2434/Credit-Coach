# E2 — Criteo: tahmin edilen ve ölçülen fark

Üretildi: `python -m credit_coach.ecom.e2_criteo test` (test kümesi tek sefer). Kilit: `docs/ecom/test_run_criteo.lock` (commit `840d646`, 2026-11-12T14:20:23+00:00). Seçim test öncesi `docs/ecom/E2_selection.md`'de commit'lendi.

Tedavi = `treatment` (atamaya göre), sonuç `visit`; test kümesi 2795919 satır; eğitim $p$ = 0,850000. Bootstrap B = 1000, tabakalı. Çalışma süresi 17,0 dk (bootstrap 14,4 dk); tepe bellek 2,69 GiB / fiziksel 8,0 GiB. Alt örneğe geçilmedi; gz açılmadı.

## Kapı ölçütleri (PLAN bölüm 6, E2; DONDURULDU)

Kapı modeli: `TO_lr0.1_leaf15_it200`.

| Ölçüt | Tanım | Ölçülen | Sonuç |
|---|---|---|---|
| 1 | Qini alanı %95 alt sınırı > 0 | alt sınır 0,003026 | geçti |
| 2 | Kalibrasyon eğimi ∈ [0,7; 1,3] | eğim 0,648 [%95: 0,600; 0,699] | **kaldı** |
| 3 | En az 8/10 desilde \|Δ_d\| ≤ 0,25·\|τ_obs\| ya da aralık 0'ı içerir | 8/10 (τ_obs = 0,01034) | geçti |

**Karar (durdurma kuralı):** Kalan ölçüt(ler): 2. Durdurma kuralı: test yeniden çalıştırılmaz, model değiştirilmez. E3 ön kaydı gereği (PLAN bölüm 11) E3 yapılmaz; sonuç: hedefleme değeri bu veriyle gösterilemedi.


> **Bu tablo ne demek:** Doğrulamada seçilen tek modelin test kümesinde, sonuç görülmeden dondurulmuş üç eşiğe göre durumu.
>
> **Ne DEMEK DEĞİL:** Geçmek, reklamın başka bir kampanyada ya da kredide benzer bir fark yaratacağını göstermez; Criteo eşit olmayan alt örnekleme ve birden çok testin birleşimidir, mutlak oranlar gerçek kampanyayı temsil etmez.

## İki model ailesi yan yana

| Model | Ayar | Qini alanı [%95] | Kalibrasyon eğimi [%95] | Genel düzey farkı [%95] |
|---|---|---|---|---|
| T | `T_lr0.1_leaf7_it200` | 0,003015 [0,002775; 0,003232] | 0,910 [0,842; 0,979] | -0,00301 [-0,00366; -0,00241] |
| TO (kapı) | `TO_lr0.1_leaf15_it200` | 0,003246 [0,003026; 0,003476] | 0,648 [0,600; 0,699] | -0,00002 [-0,00066; 0,00058] |

> **Bu tablo ne demek:** Her ailenin doğrulamada en iyi ayarının test kümesindeki üç ölçüsü; kapıya yalnızca kapı modeli girer.
>
> **Ne DEMEK DEĞİL:** Ailelerden birinin genel olarak daha iyi olduğunu göstermez; seçim tek bir doğrulama kümesine dayanır.

## Qini eğrisi

$Q(\phi)/N$; rastgele doğru $\phi\,Q(1)/N$. 100 noktanın 10'da biri.

| $\phi$ | T: $Q/N$ | TO: $Q/N$ | Rastgele (T) |
|---|---|---|---|
| 0,1 | 0,00524 | 0,00539 | 0,00088 |
| 0,2 | 0,00672 | 0,00690 | 0,00176 |
| 0,3 | 0,00740 | 0,00757 | 0,00264 |
| 0,4 | 0,00781 | 0,00808 | 0,00352 |
| 0,5 | 0,00803 | 0,00833 | 0,00440 |
| 0,6 | 0,00821 | 0,00853 | 0,00527 |
| 0,7 | 0,00832 | 0,00859 | 0,00615 |
| 0,8 | 0,00842 | 0,00868 | 0,00703 |
| 0,9 | 0,00848 | 0,00873 | 0,00791 |
| 1,0 | 0,00879 | 0,00879 | 0,00879 |

> **Bu tablo ne demek:** Model sırasına göre en üstteki $\phi$ oranı hedeflendiğinde test kümesinde ölçülen artımlı ziyaretin (kişi başına) rastgele sıralamayla karşılaştırması.
>
> **Ne DEMEK DEĞİL:** Ziyaretin dönüşüme ya da kâra dönüştüğünü göstermez; tek bir test kümesidir.

## Desil tablosu (kapı modeli)

Desil 1 = en yüksek tahmin. Fark = tahmin edilen − ölçülen. Tolerans $0{,}25\,|\tau^{obs}_{test}|$ = 0,00259.

| Desil | Tedavi | Kontrol | Tahmin edilen | Ölçülen | Fark | Fark %95 | Ölçüt 3 |
|---|---|---|---|---|---|---|---|
| 1 | 242389 | 37203 | 0,09441 | 0,06213 | 0,03228 | [0,02758; 0,03674] | değil |
| 2 | 237842 | 41750 | 0,00724 | 0,00686 | 0,00038 | [-0,00198; 0,00261] | uygun |
| 3 | 236823 | 42769 | 0,00243 | 0,00194 | 0,00049 | [-0,00120; 0,00234] | uygun |
| 4 | 236757 | 42835 | 0,00133 | 0,00226 | -0,00094 | [-0,00226; 0,00035] | uygun |
| 5 | 236617 | 42975 | 0,00078 | 0,00053 | 0,00025 | [-0,00099; 0,00139] | uygun |
| 6 | 236880 | 42712 | 0,00033 | 0,00083 | -0,00050 | [-0,00130; 0,00042] | uygun |
| 7 | 237518 | 42074 | 0,00004 | 0,00024 | -0,00020 | [-0,00045; 0,00004] | uygun |
| 8 | 237118 | 42474 | 0,00004 | 0,00028 | -0,00024 | [-0,00047; 0,00001] | uygun |
| 9 | 237389 | 42203 | 0,00004 | 0,00030 | -0,00026 | [-0,00053; -0,00002] | uygun |
| 10 | 237198 | 42393 | -0,00344 | 0,00115 | -0,00459 | [-0,00716; -0,00176] | değil |

Kalibrasyon eğimi: 0,648 [0,600; 0,699]. Genel düzey: ortalama tahmin − ölçülen = -0,00002 [-0,00066; 0,00058].


> **Bu tablo ne demek:** Tahmin edilen ziyaret farkının aynı desildeki tedavi ve kontrol gruplarından ölçülen farkla karşılaştırması ve ölçüt 3'e uygunluğu.
>
> **Ne DEMEK DEĞİL:** Ölçülen fark reklamın bu kişilerde ne yapacağını değil, bu test kümesinde ölçülen ortalama farkı verir; tek tek desiller karar dayanağı değildir.

## Eşit tahminler (kapı modeli, test kümesi)

Test kümesinde en büyük eşit tahmin bloğu satırların **0,4002**'ü ($\hat\tau$ = 0,000039); yayıldığı desiller: 6, 7, 8, 9, 10. T ailesinin en iyisinde en büyük blok 0,0504. Eşitlikler PLAN 2.1 sonradan notundaki sabit anahtarla sıralandı.

| Desil | Satır | Kontrol payı | Desil içi en büyük eşit grup payı | En büyük test bloğunun desildeki payı |
|---|---|---|---|---|
| 1 | 279592 | 0,133 | 0,0013 | 0,0000 |
| 2 | 279592 | 0,149 | 0,0563 | 0,0000 |
| 3 | 279592 | 0,153 | 0,0816 | 0,0000 |
| 4 | 279592 | 0,153 | 0,2442 | 0,0000 |
| 5 | 279592 | 0,154 | 0,2150 | 0,0000 |
| 6 | 279592 | 0,153 | 0,4162 | 0,2978 |
| 7 | 279592 | 0,150 | 1,0000 | 1,0000 |
| 8 | 279592 | 0,152 | 1,0000 | 1,0000 |
| 9 | 279592 | 0,151 | 1,0000 | 1,0000 |
| 10 | 279591 | 0,152 | 0,7037 | 0,7037 |

> **Bu tablo ne demek:** Desillerin ne kadarının aynı tahmini paylaşan satırlardan oluştuğu ve kontrol grubunun desillere dağılımı (sonuç değişkeni kullanılmadı).
>
> **Ne DEMEK DEĞİL:** Büyük bir eşit blok içindeki sıralama modelden değil sabit anahtardan gelir; bu desillerde tahmin edilen fark sabittir ve sıralama bilgi taşımaz.

## Politika değeri (kapıya GİRMEZ; E3 ızgarası)

Değer = dönüşüm × $m$, maliyet $c = k\,m$ (varsayım, PLAN 4.2); değerler müşteri başına $m$ biriminde × 1000, IPW ile. $\pi_{mod} = 1[\hat\tau_{conv} > k]$; destek dışı test satırı oranı 0,0399 (bu satırlarda $\pi_{mod} = 1$). Birincil hücre kalın.

| $k$ | Herkese | Hiçbirine | Modelle | Hedeflenen oran | Modelle − Herkese [%95] | Modelle − Hiçbirine [%95] |
|---|---|---|---|---|---|---|
| 0,0001 | 3,0003 | 2,0148 | 3,0165 | 0,340 | 0,0162 [-0,0135; 0,0470] | 1,0017 [0,8528; 1,1584] |
| 0,0003 | 2,8003 | 2,0148 | 2,9646 | 0,265 | 0,1643 [0,1288; 0,2020] | 0,9498 [0,8032; 1,0991] |
| **0,0010** | 2,1003 | 2,0148 | 2,8405 | 0,138 | 0,7402 [0,6899; 0,7906] | 0,8256 [0,6818; 0,9672] |
| 0,0030 | 0,1003 | 2,0148 | 2,6803 | 0,078 | 2,5799 [2,5147; 2,6427] | 0,6654 [0,5240; 0,8029] |
| 0,0100 | -6,8997 | 2,0148 | 2,2764 | 0,050 | 9,1761 [9,0935; 9,2599] | 0,2615 [0,1420; 0,3922] |

> **Bu tablo ne demek:** Varsayılan maliyet oranıyla üç politikanın test kümesinde IPW ile tahmin edilen müşteri başına değeri (×1000) ve farkları.
>
> **Ne DEMEK DEĞİL:** Bir kâr vaadi değildir; $k$ varsayımdır ve alt örnekleme yüzünden mutlak dönüşüm oranları gerçek kampanyayı temsil etmez. Kapı kararı bu tabloya dayanmaz.

## İkincil duyarlılık analizi: $\hat p(x)$ ağırlıklandırma (kapıya GİRMEZ)

Ön kayıt `e54c9cd`. $\hat p(x)$ aralığı [0,5546; 0,9913]; kırpılan test satırı oranı **0,00000** ($\hat p < 0{,}01$ ya da $> 0{,}99$).

| Ölçü | Ham | Ağırlıklı |
|---|---|---|
| Genel `visit` farkı (tedavi − kontrol) | 0,01034 | 0,00745 |
| Kapı modeli Qini alanı (tüm test / kırpılmış) | 0,003246 / 0,003246 | 0,001506 |

> **Bu tablo ne demek:** Özellik dengesizliğine karşı ters olasılık ağırlığıyla düzeltilmiş genel fark ve Qini'nin ham değerlerle karşılaştırması (nokta tahmini).
>
> **Ne DEMEK DEĞİL:** Kapı kararını değiştirmez; $\hat p(x)$ bir modeldir ve doğru olduğu bilinmez; aralık hesaplanmadı.

| Özellik | SMD ham (test) | SMD ağırlıklı (kırpılmış test) |
|---|---|---|
| `f3` | -0,0488 | 0,0000 |
| `f6` | -0,0398 | 0,0001 |
| `f5` | -0,0283 | 0,0017 |
| `f1` | 0,0239 | 0,0011 |
| `f9` | 0,0231 | -0,0018 |
| `f8` | -0,0205 | 0,0031 |
| `f7` | 0,0189 | -0,0029 |
| `f10` | 0,0089 | -0,0026 |
| `f0` | -0,0074 | -0,0006 |
| `f4` | 0,0059 | -0,0035 |
| `f11` | -0,0056 | -0,0002 |
| `f2` | -0,0056 | -0,0003 |

> **Bu tablo ne demek:** Test kümesinde her özelliğin tedavi/kontrol SMD'si, ham ve $\hat p(x)$ ağırlığıyla; en büyük ham SMD üstte.
>
> **Ne DEMEK DEĞİL:** Ağırlıklı SMD'nin küçülmesi gözlenmeyen özelliklerde dengeyi göstermez.

