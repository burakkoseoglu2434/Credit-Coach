# E0 — Veri ve lisans doğrulaması

Üretildi: `python -m credit_coach.ecom.e0_data_check` (dal `ecom-e0-data-check`). Yalnızca veri doğrulaması: model eğitilmedi, bölme dosyası üretilmedi, test kilidi oluşturulmadı. Criteo gz açılmadı, DuckDB ile doğrudan okundu.

Disiplin: sonuç değişkenlerinin (visit, conversion, spend) tedavi/kontrol kırılımı **hesaplanmadı**; yalnızca genel ortalama, eksik değer ve aralık verildi (E1/E2'nin sorusu önceden etkilenmesin diye).

Toplam çalışma süresi: 27,3 s (Criteo SQL geçişleri 17,0 s, Criteo Pandera 9,5 s).

## Ölçüt tablosu (PLAN bölüm 6, E0; eşikler DONDURULDU)

| Ölçüt | Tanım | Ölçülen | Sonuç |
|---|---|---|---|
| 1a | Hillstrom satır = 64.000 | 64.000 | geçti |
| 1b | Her segment payı 1/3 ± 0,01 | Mens E-Mail: 0,3329, Womens E-Mail: 0,3342, No E-Mail: 0,3329 | geçti |
| 2a | Criteo satır = 13.979.592 | 13.979.592 | geçti |
| 2b | Criteo tedavi oranı 0,846 ± 0,005 | 0,85000 | geçti |
| 3a | Hillstrom Pandera: satırların %100'ü geçer | kalan satır 0 | geçti |
| 3b | Criteo Pandera: satırların %100'ü geçer | kalan satır 0 | geçti |
| 4a | Hillstrom \|SMD\| < 0,05 (birleşik iki kol vs e-posta yok) | en büyük 0,0153 (history_segment=2) $100 - $200) | geçti |
| 4b | Criteo \|SMD\| < 0,05 (treatment 1 vs 0) | en büyük 0,0488 (f3) | geçti |
| 5 | Lisans notu kullanıcı onayı | kullanıcı onayı bekliyor | kullanıcı onayı bekliyor |

**Karar (durdurma kuralı):** 1–4 geçti; ölçüt 5 (lisans) kullanıcı onayı bekliyor. E1 başlamaz, onay beklenir.


> **Bu tablo ne demek:** Her E0 ölçütünün, sonuç görülmeden dondurulmuş eşiğe göre geçip geçmediği.
>
> **Ne DEMEK DEĞİL:** Verinin uplift modellemeye uygun olduğunu ya da E1/E2'nin geçeceğini göstermez; yalnızca dosyanın belgelenen kaynakla tutarlı olduğunu ve atamanın özelliklerde dengeli göründüğünü söyler.

## Dosyalar

| Set | Dosya | Bayt | SHA-256 |
|---|---|---|---|
| Hillstrom | `Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv` | 3964977 | `0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece` |
| Criteo | `criteo-research-uplift-v2.1.csv.gz` | 311422618 | `2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc` (gz) |

> **Bu tablo ne demek:** Doğrulanan dosyaların kimliği; değerler `configs/ecom_data_source.yaml` ile aynıdır.
>
> **Ne DEMEK DEĞİL:** Dosyaların içeriğinin doğru ya da eksiksiz olduğunu göstermez; yalnızca aynı dosyanın kullanıldığını sabitler.

## Satır sayıları ve tedavi payları

| Set | Satır | Grup | Sayı | Pay |
|---|---|---|---|---|
| Hillstrom | 64000 | Mens E-Mail | 21307 | 0,3329 |
| Hillstrom | 64000 | Womens E-Mail | 21387 | 0,3342 |
| Hillstrom | 64000 | No E-Mail | 21306 | 0,3329 |
| Hillstrom | 64000 | birleşik e-posta (T=1, Karar Q2) | 42694 | 0,6671 |
| Criteo | 13979592 | treatment = 1 | 11882655 | 0,85000 |
| Criteo | 13979592 | treatment = 0 | 2096937 | 0,15000 |

**25M çelişkisi:** İndirilen dosya (`criteo-research-uplift-v2.1.csv.gz`, gz SHA-256 Hugging Face LFS kaydıyla aynı) 13979592 veri satırı içeriyor. Kaynak kartında geçen "25M" (TFDS: 25.309.483) bu dosyanın satır sayısı değildir; hangi sürüme ait olduğu bu dosyadan **doğrulanamadı**.

Not: Plan bölüm 2.1 ve Q2 notu $p$'nin eğitim kümesinde sabitleneceğini söyler; E0'da bölme yapılmadığı için burada tüm dosyadaki oran verilir, eğitim kümesindeki değer E1/E2'de bölmeden sonra sabitlenir.


> **Bu tablo ne demek:** Dosyadaki satır sayısı ve tedavi gruplarının payları; Hillstrom'da birincil karşılaştırmanın tedavi payı $p$.
>
> **Ne DEMEK DEĞİL:** Payların tasarımla uyumlu olması atamanın rastgele yapıldığını tek başına kanıtlamaz; SMD tablosu ayrı bir kontroldür.

## Sütunlar — Hillstrom

| Sütun | DuckDB türü | Eksik | Min | Maks |
|---|---|---|---|---|
| `recency` | BIGINT | 0 | 1 | 12 |
| `history_segment` | VARCHAR | 0 | 1) $0 - $100 | 7) $1,000 + |
| `history` | DOUBLE | 0 | 29.99 | 3345.93 |
| `mens` | BIGINT | 0 | 0 | 1 |
| `womens` | BIGINT | 0 | 0 | 1 |
| `zip_code` | VARCHAR | 0 | Rural | Urban |
| `newbie` | BIGINT | 0 | 0 | 1 |
| `channel` | VARCHAR | 0 | Multichannel | Web |
| `segment` | VARCHAR | 0 | Mens E-Mail | Womens E-Mail |
| `visit` | BIGINT | 0 | 0 | 1 |
| `conversion` | BIGINT | 0 | 0 | 1 |
| `spend` | DOUBLE | 0 | 0.0 | 499.0 |

> **Bu tablo ne demek:** Okuma şemasında beklenen sütunlar, türleri, eksik değer sayısı ve genel aralık (tedavi kırılımı yok).
>
> **Ne DEMEK DEĞİL:** Aralık değerleri bir sonuç ölçümü değildir; sonuç sütunlarının en küçük/en büyük değeri yalnızca kodlama kontrolüdür.

## Sütunlar — Criteo

| Sütun | DuckDB türü | Eksik | Min | Maks |
|---|---|---|---|---|
| `f0` | DOUBLE | 0 | 12.616364906986497 | 26.74525510669564 |
| `f1` | DOUBLE | 0 | 10.059654474774547 | 16.34418683323554 |
| `f2` | DOUBLE | 0 | 8.214382844395335 | 9.051961945804948 |
| `f3` | DOUBLE | 0 | -8.39838674285089 | 4.679881620097284 |
| `f4` | DOUBLE | 0 | 10.280525225748212 | 21.123507734315055 |
| `f5` | DOUBLE | 0 | -9.011891520498516 | 4.115453421277861 |
| `f6` | DOUBLE | 0 | -31.429783775633886 | 0.29444271125560606 |
| `f7` | DOUBLE | 0 | 4.833814577796811 | 11.998400591725755 |
| `f8` | DOUBLE | 0 | 3.63510661177053 | 3.971857989350875 |
| `f9` | DOUBLE | 0 | 13.190055934673358 | 75.29501735734412 |
| `f10` | DOUBLE | 0 | 5.300374864042156 | 6.473917229316857 |
| `f11` | DOUBLE | 0 | -1.383940669255639 | -0.16867922100056124 |
| `treatment` | BIGINT | 0 | 0 | 1 |
| `conversion` | BIGINT | 0 | 0 | 1 |
| `visit` | BIGINT | 0 | 0 | 1 |
| `exposure` | BIGINT | 0 | 0 | 1 |

> **Bu tablo ne demek:** Okuma şemasında beklenen sütunlar, türleri, eksik değer sayısı ve genel aralık (tedavi kırılımı yok).
>
> **Ne DEMEK DEĞİL:** Aralık değerleri bir sonuç ölçümü değildir; sonuç sütunlarının en küçük/en büyük değeri yalnızca kodlama kontrolüdür.

## Pandera şeması

| Set | Satır | Şemayı geçemeyen satır | Yöntem |
|---|---|---|---|
| Hillstrom | 64000 | 0 | tüm tablo tek seferde (`strict`, `ordered`) |
| Criteo | 13979592 | 0 | DuckDB'den 14 parça (~1 M satır), her parça ayrı doğrulandı; tamamı belleğe alınmadı |

> **Bu tablo ne demek:** Tür, eksik değer, ikili (0/1) kodlama, kategori listesi, negatif olmama ve (Criteo) sonlu değer kurallarını geçemeyen satır sayısı.
>
> **Ne DEMEK DEĞİL:** Değerlerin anlamca doğru olduğunu göstermez; Criteo özellikleri anonim olduğu için yalnızca sonlu sayı oldukları denetlenebilir.

## Denge (SMD)

Tanım: $\text{SMD} = (\bar x_T - \bar x_C) / \sqrt{(s_T^2 + s_C^2)/2}$, örneklem varyansı; kategorikler (`zip_code`, `channel`, `history_segment`) one-hot. Hesap DuckDB SQL'de yapıldı. Hillstrom'da kapıya giren çift: birleşik iki e-posta kolu vs e-posta yok (Kararlar Q2); Womens–yok ve Mens–yok yalnızca bilgi.

### Hillstrom

| Özellik | Ort. T (birleşik) | Ort. C | SMD birleşik (kapı) | SMD Womens–yok (bilgi) | SMD Mens–yok (bilgi) |
|---|---|---|---|---|---|
| `recency` | 5,7707 | 5,7497 | 0,0060 | 0,0052 | 0,0068 |
| `history` | 242,6860 | 240,8827 | 0,0071 | 0,0065 | 0,0076 |
| `mens` | 0,5499 | 0,5532 | -0,0066 | -0,0086 | -0,0046 |
| `womens` | 0,5508 | 0,5476 | 0,0063 | 0,0049 | 0,0076 |
| `newbie` | 0,5024 | 0,5020 | 0,0008 | 0,0026 | -0,0009 |
| `zip_code=Rural` | 0,1505 | 0,1473 | 0,0088 | 0,0040 | 0,0137 |
| `zip_code=Surburban` | 0,4486 | 0,4518 | -0,0064 | -0,0011 | -0,0117 |
| `zip_code=Urban` | 0,4010 | 0,4009 | 0,0001 | -0,0018 | 0,0020 |
| `channel=Multichannel` | 0,1208 | 0,1223 | -0,0047 | -0,0053 | -0,0042 |
| `channel=Phone` | 0,4379 | 0,4378 | 0,0002 | 0,0086 | -0,0083 |
| `channel=Web` | 0,4414 | 0,4399 | 0,0029 | -0,0051 | 0,0110 |
| `history_segment=1) $0 - $100` | 0,3597 | 0,3573 | 0,0051 | -0,0007 | 0,0109 |
| `history_segment=2) $100 - $200` | 0,2206 | 0,2270 | -0,0153 | -0,0143 | -0,0164 |
| `history_segment=3) $200 - $350` | 0,1931 | 0,1898 | 0,0084 | 0,0114 | 0,0055 |
| `history_segment=4) $350 - $500` | 0,1004 | 0,0997 | 0,0023 | 0,0087 | -0,0043 |
| `history_segment=5) $500 - $750` | 0,0763 | 0,0775 | -0,0045 | 0,0006 | -0,0097 |
| `history_segment=6) $750 - $1,000` | 0,0290 | 0,0292 | -0,0013 | -0,0088 | 0,0061 |
| `history_segment=7) $1,000 +` | 0,0209 | 0,0195 | 0,0097 | 0,0035 | 0,0158 |

> **Bu tablo ne demek:** Her özelliğin e-posta alan ve almayan gruplarda ortalama farkı, ortak standart sapma biriminde; kapı yalnızca birleşik sütuna bakar.
>
> **Ne DEMEK DEĞİL:** Küçük SMD gözlenmeyen özelliklerde de denge olduğunu göstermez; bilgi sütunları kapı kararına girmez.

### Criteo

| Özellik | Ort. T | Ort. C | SMD |
|---|---|---|---|
| `f0` | 19,6148 | 19,6517 | -0,0069 |
| `f1` | 10,0703 | 10,0679 | 0,0240 |
| `f2` | 8,4463 | 8,4482 | -0,0062 |
| `f3` | 4,1694 | 4,2328 | -0,0488 |
| `f4` | 10,3392 | 10,3365 | 0,0080 |
| `f5` | 4,0266 | 4,0393 | -0,0306 |
| `f6` | -4,1828 | -3,9999 | -0,0404 |
| `f7` | 5,1056 | 5,0803 | 0,0213 |
| `f8` | 3,9334 | 3,9347 | -0,0224 |
| `f9` | 16,0526 | 15,8863 | 0,0240 |
| `f10` | 5,3337 | 5,3319 | 0,0106 |
| `f11` | -0,1710 | -0,1709 | -0,0052 |

`exposure` atamadan sonra oluştuğu için özellik değildir; SMD'ye girmez.

**Gözlem (karar değişmez):** En büyük \|SMD\| 0,0488 (`f3`) eşiğe (0,05) yakın. Bu örneklem büyüklüğünde SMD'nin rastgele atama altındaki yaklaşık standart hatası $\sqrt{1/n_T + 1/n_C} \approx$ 0,0007; birkaç özellikteki fark bunun çok üstünde. Nedeni (ör. birden çok testin birleşimi ya da eşit olmayan alt örnekleme) bu dosyadan **doğrulanamadı**. Kapı ölçütü dondurulmuş eşiktir; bu gözlem E2 raporunda sınır olarak yazılır.


> **Bu tablo ne demek:** Anonim özelliklerin tedavi ve kontrol gruplarında ortalama farkı, ortak standart sapma biriminde.
>
> **Ne DEMEK DEĞİL:** Criteo birden çok testin birleşimi olduğu için genel denge, testlerin her birinde denge olduğunu göstermez (test kimliği yok).

## Sonuç değişkenleri — yalnızca genel

| Set | Değişken | Genel ortalama | Eksik | Min | Maks |
|---|---|---|---|---|---|
| Hillstrom | `visit` | 0,1468 | 0 | 0.0 | 1.0 |
| Hillstrom | `conversion` | 0,0090 | 0 | 0.0 | 1.0 |
| Hillstrom | `spend` | 1,0509 | 0 | 0.0 | 499.0 |
| Criteo | `visit` | 0,04699 | 0 | 0 | 1 |
| Criteo | `conversion` | 0,00292 | 0 | 0 | 1 |
| Criteo | `exposure` | 0,03063 | 0 | 0 | 1 |

> **Bu tablo ne demek:** Sonuç değişkenlerinin tüm dosyadaki ortalaması ve kodlama kontrolü.
>
> **Ne DEMEK DEĞİL:** Tedavi ile kontrol arasındaki fark burada bilerek hesaplanmadı; bu tablo hamlenin etkisi hakkında hiçbir şey söylemez.

## Lisans (ölçüt 5)

| Set | Not | Durum |
|---|---|---|
| Hillstrom | doğrulanamadı (kaynak sayfada şart yok); kullanım: ticari olmayan iç doğrulama (PLAN Karar Q5) | kullanıcı onayı bekliyor |
| Criteo | CC-BY-NC-SA-4.0 (HF etiketi; birincil kaynakta doğrulanamadı); kullanım: ticari olmayan iç doğrulama (PLAN Karar Q5); atıf: Diemert, Betlei, Renaudin, Amini (2018), A Large Scale Benchmark for Uplift Modeling, AdKDD & TargetAd @ KDD | kullanıcı onayı bekliyor |

> **Bu tablo ne demek:** Lisans bilgisinin bulunduğu kaynak ve bu çalışmanın ticari olmayan iç doğrulama olarak sınırlandığı.
>
> **Ne DEMEK DEĞİL:** Hukuki değerlendirme değildir; HF etiketi birincil kaynakta doğrulanmadı.

