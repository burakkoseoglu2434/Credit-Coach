# Yeniden kullanım haritası (REUSE_MAP)

**Taban: main ucu c8ec459 (etiketsiz); PR #20 (pilot revizyonu) ve ecom dalları main'de değil.**

`demo-v0.3` etiketi ne yerelde ne `origin`'de var; mevcut etiketler `demo-v0-final`, `demo-v0.1`,
`demo-v0.2`, `v1.2`. Bu belge kod değiştirmez; yalnızca envanterdir.

**Yöntem.** Importlar tahminle değil, `backend/src/credit_coach/*.py` dosyalarının AST'sinden
çıkarıldı (modül düzeyi ve fonksiyon içi "tembel" importlar ayrı ayrı). Veri, eşik ve config
bağımlılıkları dosyaların kendisinden (`*_PATH` sabitleri, `read_csv`, `os.environ`) okundu.
"Import anında dosya okuyor mu" sorusu, her modül `Path.read_text`/`open` izlenerek tek tek
içe aktarılarak ölçüldü. Ecom dalları `git show` ile okundu, checkout yapılmadı.

> **Bu belge ne demek:** c8ec459'daki kodun hangi parçasının hangi veriye, modele ve eşiğe bağlı olduğunun ve yeni bir `credit_coach/roadmap` alt paketinin neyi güvenle alabileceğinin dökümü.
>
> **Ne DEMEK DEĞİL:** Bir taşıma planı ya da karar değildir; hiçbir modülün taşınacağını veya değiştirileceğini söylemez. PR #20 ve ecom dallarındaki değişiklikler birleşince tablolar eskir.

---

## 1. Modül envanteri (`backend/src/credit_coach`)

Kısaltmalar: **LC-CSV** = `credit-coach/data/lending_club/lending_club_48_features_20251026_114053.csv`
(v1 mirası yol, `baseline.CSV`); **RAW_LC** = `CREDIT_COACH_RAW_LC` ortam değişkeniyle verilen ham
accepted CSV; **bundle** = `bundle/pd_monotone.json` + `bundle/calibration_data.npz`, hashleri
`bundle.lock.json`'da; **manifest** = `configs/features.yaml`. Main'de yalnızca **policy v1**
var (`configs/policy/v1.yaml`); policy v2 dosyası yok.

"İç importlar" sütunu yalnızca doğrudan importlardır; *italik* olanlar fonksiyon içinde (tembel)
yapılır.

| Modül | Amaç (bir satır) | Bağlı olduğu veri / model / eşik | Doğrudan iç importlar | Sınıf |
|---|---|---|---|---|
| `__init__` | Boş paket dosyası | — | — | GENEL |
| `app` | FastAPI uygulaması: `/score`, `/batch`, sağlık uçları | Dolaylı: bundle, policy v1, support, katalog (scoring_service üzerinden) | ayarlar, schemas, scoring_service | KREDİ-VEREN-ÖZEL |
| `approval_table` | Hurdle duyarlılığı, yalnızca kalibrasyon bölmesi | LC-CSV, `decision.yaml`, `cost.yaml` (hurdle), XGBoost modeli | baseline, bundle, calibration, decision, labels, modeling, train_monotone | KREDİ-VEREN-ÖZEL |
| `ayarlar` | Çalışma anı anahtarları (karar logu açık/kapalı) | `CREDIT_COACH_DECISION_LOG` | — | GENEL |
| `baseline` | LR ve kısıtsız XGBoost temel modelleri; `CSV` yolunu tanımlar | LC-CSV | features, modeling | KREDİ-VEREN-ÖZEL |
| `bundle` | Dondurulmuş dosyaların SHA-256 kilidi (`write`/`verify`) | `bundle.lock.json`; `FILES` listesi: bundle modeli, kalibratör, manifest, `split/monotone/cost/decision/support.yaml`, policy v1, `catalog/demo_v0.yaml` | features (yalnız `MANIFEST_PATH` → `ROOT`) | UYARLANABİLİR (mantık genel, `FILES` listesi kredi) |
| `calibrate` | Venn-Abers kalibrasyonunu kalibrasyon bölmesinde kurar, MLflow'a yazar | LC-CSV, XGBoost modeli | baseline, calibration, modeling, train_monotone | KREDİ-VEREN-ÖZEL |
| `calibration` | Venn-Abers PD aralıkları ve Platt karşılaştırması (saf fonksiyonlar) | — (sklearn, venn_abers) | — | GENEL |
| `canonical` | Kanonik serileştirme (ADR-005): bir nesne → tek bayt dizisi, SHA-256 | — (pydantic) | — | GENEL |
| `catalog` | Katalog birimlerini manifestteki `birim` ile doğrular | `configs/catalog/v1.yaml`, manifest | features | UYARLANABİLİR (emin değilim) |
| `contract` | Karar sözleşmesi (ADR-004): girdi, iç/dış çıktı, gerekçe kodları, kural kimlikleri | Manifest (**import anında okunur**) | features | KREDİ-VEREN-ÖZEL |
| `cost` | Eşik için maliyet varsayımları, yalnızca TRAIN penceresinden | Ham LC (duckdb, `loan_status`, `issue_d`), `split.yaml` | split | KREDİ-VEREN-ÖZEL |
| `cost_report` | `configs/cost.yaml` ve `docs/week2_cost.md` yazar | RAW_LC (`CREDIT_COACH_RAW_LC`), `cost.yaml` | cost, features, labels, split | KREDİ-VEREN-ÖZEL |
| `counteroffer_calibration_check` | Karşı teklif aday kümelerinde kalibrasyon/seçim denetimi | LC-CSV, bundle, `cost.yaml`, katalog, support | baseline, bundle, counteroffer_economics, labels, modeling, policy, recourse, recourse_gap_report, recourse_scorers, support | ÖLÇÜM-ÖZEL |
| `counteroffer_economics` | Kurum yolu karşı teklifinin beklenen fazla kârı | Bundle, `cost.yaml` (hurdle), katalog, policy v1 | baseline, bundle, contract, decision, decision_engine, labels, modeling, policy, recourse, recourse_gap_report, recourse_report, recourse_scorers, support | ÖLÇÜM-ÖZEL |
| `data_source` | Dış veri kaynağını yol + SHA-256 ile kaydeder (kopyalamaz) | `configs/data_source.yaml`, `CREDIT_COACH_REJECTED_LC` (LC reddedilen) | features | UYARLANABİLİR |
| `decision` | Analitik onay eşiği `(g−h)/(g+L)` ve aralık karar kuralı | `cost.yaml` (kazanç, kayıp, hurdle) | features | KREDİ-VEREN-ÖZEL |
| `decision_config` | Bant genişliği ve zayıf destek aralıkları; bundle verisini dışa aktarır | LC-CSV, `decision.yaml`, XGBoost, bundle | baseline, bundle, calibration, modeling, train_monotone | KREDİ-VEREN-ÖZEL |
| `decision_engine` | Saf karar fonksiyonu `decide()` (saat, rastgelelik, dosya yok) | Çağrıda policy + support nesnesi; import anında manifest (contract üzerinden) | contract, policy, support | KREDİ-VEREN-ÖZEL |
| `decision_log` | SHA-256 zincirli, yalnız eklenen karar logu | `bundle.lock.json`, policy dosyası hashi, Postgres (sqlalchemy) | bundle, canonical, contract, decision_engine, policy | UYARLANABİLİR |
| `decision_scenarios` | Testler ve kural kapsama raporu için adlandırılmış senaryolar | Policy v1, manifest | features, policy | KREDİ-VEREN-ÖZEL |
| `delta_comparison` | Eski (0,02) ve yeni varsayılan δ için etiket dağılımları | LC-CSV, bundle, katalog | baseline, bundle, labels, modeling, policy, recourse, recourse_gap_report, recourse_report, recourse_scorers, report_deltas, resilience_report, scoring_service, support, target_segment | ÖLÇÜM-ÖZEL |
| `effect_share` | Etki payı duyarlılığı (kalibrasyon + boşluk ayları) | LC-CSV, bundle, katalog, policy v1 | baseline, bundle, contract, decision_engine, labels, modeling, policy, recourse, recourse_gap_report, recourse_report, recourse_scorers, scoring_service, support | ÖLÇÜM-ÖZEL |
| `export_openapi` | OpenAPI şemasını belirlenimci biçimde JSON'a yazar | Dolaylı: app'in tüm bağımlılıkları | app | UYARLANABİLİR |
| `features` | Manifesti yükler, doğrular ve ondan Pandera şeması üretir | `MANIFEST_PATH` = manifest (sabit yol); sınıflar `PRICING`, `POST_ORIGINATION` kredi kavramı | — | UYARLANABİLİR |
| `final_test_report` | TEST bölmesini bir kez çalıştırır; rapor varsa reddeder | LC-CSV, bundle, `bundle.lock.json`, `decision.yaml` | baseline, bundle, calibration, decision, labels, modeling, split | ÖLÇÜM-ÖZEL |
| `golden` | Altın küme v1: dondurulmuş girdi + beklenen çıktı | `tests/golden/`, policy v1; üretimde *LC-CSV, model, kalibratör* | bundle, canonical, contract, decision_engine, decision_scenarios, policy; *baseline, calibration, features, modeling* | KREDİ-VEREN-ÖZEL |
| `labels` | Raporlarda ortak sabit metin ("tek fiyatlı kurgusal kredi veren") | — | — | KREDİ-VEREN-ÖZEL |
| `leakage` | İzinli sütun denetimi ve tek özellik AUC taraması | Manifest, split | features, split | UYARLANABİLİR |
| `modeling` | Model verisi hazırlığı ve temel modeller (TEST yüklenmez) | `monotone.yaml`, LC sütunları, `INNER_FIT_END = 2014-03-01` | features, leakage, split | KREDİ-VEREN-ÖZEL |
| `pilot_protocol` | Pilot v0: örneklem büyüklüğü ve maruziyet hesabı | `configs/pilot.yaml`, `cost.yaml`, bundle, katalog | baseline, bundle, counteroffer_economics, labels, modeling, policy, recourse, recourse_gap_report, recourse_scorers, support | KREDİ-VEREN-ÖZEL |
| `policy` | Sürümlü, dondurulmuş karar politikası; sürüm yoksa hata (varsayılan yok) | `configs/policy/v1.yaml`; `derive_v1` için `cost.yaml`, `decision.yaml` | bundle, decision | KREDİ-VEREN-ÖZEL |
| `portfolio_report` | Portföy raporu (demo v0) | LC-CSV, bundle, katalog | baseline, bundle, labels, modeling, policy, recourse, recourse_bucket_report, recourse_gap_report, recourse_report, recourse_scorers, recourse_worstcase, report_deltas, support | ÖLÇÜM-ÖZEL |
| `recourse` | Demo v0 recourse motoru (ADR-006): ≤ max_eylem eylemin tam taraması | `configs/catalog/demo_v0.yaml`, policy, support | contract, decision_engine, features, policy, support | KREDİ-VEREN-ÖZEL |
| `recourse_bucket_report` | Kova ve aya göre geçerli plan oranı | LC-CSV, bundle, katalog | baseline, bundle, contract, decision_engine, labels, modeling, policy, recourse, recourse_report, recourse_scorers, support | ÖLÇÜM-ÖZEL |
| `recourse_delta_diag` | δ=0,01 / 0,02 tanısı (kalibrasyon bölmesi) | LC-CSV, bundle, katalog | baseline, bundle, calibration, labels, modeling, policy, recourse, recourse_report, recourse_scorers, support | ÖLÇÜM-ÖZEL |
| `recourse_gap_report` | Boşluk aylarında recourse raporu | LC-CSV, bundle, katalog | baseline, bundle, labels, recourse, recourse_report, split | ÖLÇÜM-ÖZEL |
| `recourse_report` | Kalibrasyon bölmesinde recourse raporu | LC-CSV, bundle, `bundle.lock.json`, `tests/golden` | baseline, bundle, contract, decision_engine, features, labels, modeling, policy, recourse, recourse_scorers, support | ÖLÇÜM-ÖZEL |
| `recourse_scorers` | Recourse motoru için skorlayıcılar (`ModelScorer`) | *Bundle modeli + kalibratör, support, `monotone.yaml`* | recourse; *bundle, calibration, modeling, support* | KREDİ-VEREN-ÖZEL |
| `recourse_worstcase` | Geçerli planı olan reddedilenlerde gözlenen temerrüt oranı | LC-CSV (etiketler), bundle, katalog | baseline, bundle, contract, decision_engine, labels, modeling, policy, recourse, recourse_bucket_report, recourse_gap_report, recourse_report, recourse_scorers, support | ÖLÇÜM-ÖZEL |
| `rejected_overlap` | LC reddedilen başvuruların eğitim desteğiyle örtüşmesi | `CREDIT_COACH_REJECTED_LC`, `data_source.yaml`, `support.yaml` | data_source, rejected_scale, support | ÖLÇÜM-ÖZEL |
| `rejected_scale` | Risk_Score ile fico_range_low ölçek denetimi | LC reddedilen + accepted CSV (duckdb) | — | ÖLÇÜM-ÖZEL |
| `replay` | Loglanmış girdilerde `decide()`'ı yeniden çalıştırıp bayt bayt karşılaştırır | `CREDIT_COACH_APP_DB_URL`, policy dosyaları, bundle | bundle, canonical, contract, decision_engine, decision_log, policy | UYARLANABİLİR (emin değilim) |
| `report_deltas` | Raporlarda ortak δ kümeleri ve etiketleri | Katalogdaki varsayılan δ | recourse | KREDİ-VEREN-ÖZEL |
| `resilience_report` | Dayanıklılık etiketi dağılımı | LC-CSV, bundle, katalog | baseline, bundle, contract, decision_engine, labels, modeling, policy, recourse, recourse_gap_report, recourse_report, recourse_scorers, report_deltas, support | ÖLÇÜM-ÖZEL |
| `rule_coverage` | Her kural ve gerekçe kodunun en az bir senaryoyla tetiklendiği raporu | Policy v1, senaryolar | bundle, contract, decision_engine, decision_scenarios, labels, support | UYARLANABİLİR (emin değilim) |
| `safety_margin` | ADR-007: aylık \|kalibre PD − gözlenen oran\| | LC-CSV, bundle | baseline, bundle, modeling, recourse_gap_report, recourse_report, recourse_scorers | ÖLÇÜM-ÖZEL |
| `schemas` | API Pydantic şemaları (TS tiplerinin kaynağı) | Dolaylı: manifest, recourse | contract, recourse | KREDİ-VEREN-ÖZEL |
| `scoring_service` | `/score` ve `/batch` için tek karar yolu | Bundle, `bundle.lock.json`, policy v1, support, katalog, `configs/templates/api_v0.yaml` | bundle, contract, decision_engine, features, policy, recourse, recourse_scorers, schemas, support | KREDİ-VEREN-ÖZEL |
| `split` | Kohort, hedef ve zamana göre bölme (ADR-002) | `configs/split.yaml`, LC `term`/`issue_d` | — | UYARLANABİLİR |
| `support` | Eğitim desteği aralıkları ve karar öncesi destek denetimi | `support.yaml`; `build` için *LC-CSV* | canonical, features; *baseline, modeling, split* | UYARLANABİLİR |
| `target_segment` | Hedef segment raporu | LC-CSV, bundle, `bundle.lock.json`, katalog | baseline, bundle, contract, decision_engine, labels, modeling, policy, recourse, recourse_gap_report, recourse_report, recourse_scorers, report_deltas, resilience_report, scoring_service, support | ÖLÇÜM-ÖZEL |
| `train_monotone` | Monoton XGBoost ayarı ve ablasyonu, MLflow | LC-CSV, `monotone.yaml` | baseline, features, modeling, split | KREDİ-VEREN-ÖZEL |
| `ui_cases` | Arayüz örnek vakaları (`tests/golden` kayıtlarından) | `tests/golden`, LC-CSV (doğrulama), API | app, baseline, bundle | KREDİ-VEREN-ÖZEL |

**Sayım (54 dosya):** GENEL 4 (`__init__`, `ayarlar`, `calibration`, `canonical`) ·
UYARLANABİLİR 11 (3'ü "emin değilim") · KREDİ-VEREN-ÖZEL 23 · ÖLÇÜM-ÖZEL 16.

**Sınıf tanımları.** GENEL: kredi verisi, manifest ya da config yolu içermez, olduğu gibi alınır.
UYARLANABİLİR: mantık veriden bağımsızdır ama bir sabit yol, sabit liste ya da kredi kavramı
taşır; parametre ya da kopya ile ayrılabilir. KREDİ-VEREN-ÖZEL: LC modeli, hurdle, eşik, policy,
katalog ya da pilot üzerine kurulu. ÖLÇÜM-ÖZEL: tek bir rapor ya da ölçüm üreten betik
(`docs/*.md` yazar); hepsi ayrıca LC-CSV'ye ve bundle'a bağlıdır.

**Emin olmadıklarım.**
- `catalog`: birim doğrulaması geneldir, ama katalog eylemleri kredi başvurusu alanlarına yöneliktir.
- `replay`, `rule_coverage`: desen geneldir, ama kod doğrudan kredi `decide()`'ına ve kural kimliklerine yazılmış.
- `recourse` KREDİ-VEREN-ÖZEL sayıldı; tam tarama algoritması belki ayrılabilir, ama `contract`/`policy`/`support` ile sıkı bağlı.

> **Bu bölüm ne demek:** Her modülün gerçek importlarından ve okuduğu dosyalardan çıkarılmış amaç, bağımlılık ve sınıf.
>
> **Ne DEMEK DEĞİL:** Sınıflar kod kalitesi notu değildir. "UYARLANABİLİR" değişikliğin küçük olacağını kesin olarak söylemez, yalnızca veri bağının bir yol ya da listede toplandığını gösterir.

---

## 2. `credit_coach/roadmap` için yeniden kullanım ve geçişli sızıntı

Kritik ölçüm: aşağıdaki modüller **import anında** `configs/features.yaml` (LC manifestosu)
okur, çünkü `contract` modül düzeyinde manifestten Pydantic modeli kurar: `contract`,
`decision_engine`, `decision_log`, `replay`, `recourse`, `schemas`, `scoring_service`,
`rule_coverage`. Bunlardan herhangi birini içe aktaran roadmap modülü, hiç kullanmasa bile LC
manifestine bağlanır.

### 2a. Doğrudan alınabilir (geçişli kredi bağı yok)

| Modül | Modül düzeyi geçişli kapanış | Tembel importlarla eklenen | Not |
|---|---|---|---|
| `canonical` | — | — | Tamamen genel; dış bağımlılık yalnız pydantic |
| `ayarlar` | — | — | Ortam değişkeni adı `CREDIT_COACH_DECISION_LOG`; roadmap kendi anahtarını isteyebilir |
| `calibration` | — | — | Venn-Abers/Platt; sklearn ve `venn_abers` gerektirir |

### 2b. Alınabilir ama kredi yoluna sızar

| Modül | Modül düzeyi kapanış | Tembel importla eklenen | Sızıntı |
|---|---|---|---|
| `features` | — | — | `MANIFEST_PATH` sabit olarak LC manifesti; `load_manifest()` varsayılanı onu okur; `CLASSES` (`PRICING`, `POST_ORIGINATION`) kredi kavramı. Ayrıca `ROOT` hesabı birçok modülde buradan türetilir |
| `bundle` | features | — | `FILES` listesi kredi bundle'ı; `build_lock(files, root)` / `verify_lock(lock, root)` parametreli olduğundan mantık kopyalanmadan kullanılabilir |
| `split` | — | — | `SPLIT_CONFIG_PATH` = `configs/split.yaml`; kohort `term`/`issue_d` LC alanları |
| `leakage` | features, split | — | İzinli sütun listesi manifestten; `build_training_matrix` LC bölmesine bağlı |
| `data_source` | features | — | `lc_reddedilen` anahtarı ve `CREDIT_COACH_REJECTED_LC` sabit |
| `support` | canonical, features | baseline, modeling, split, leakage | `build` LC-CSV okur (`baseline.CSV`); `violations()` kendisi genel. `CATEGORICAL` listesi LC alanları |
| `decision` | features | — | `COST_PATH` = `cost.yaml`; `approval_threshold` saf matematik ama hurdle kavramı kredi |
| `catalog` | features | — | `CATALOG_PATH` = `catalog/v1.yaml` |
| `decision_log` | bundle, canonical, contract, decision, decision_engine, features, policy, support | baseline, leakage, modeling, split | Hash zinciri deseni genel; ama `contract`/`decide`/policy v1/`bundle.lock.json` ile bağlı ve import anında manifest okur |
| `replay` | decision_log'un tamamı | aynı | Aynı; ek olarak `CREDIT_COACH_APP_DB_URL` |
| `rule_coverage` | bundle, canonical, contract, decision, decision_engine, decision_scenarios, features, labels, policy, support | baseline, leakage, modeling, split | Kural kimlikleri `R1_…R6_` kredi |
| `export_openapi` | app'in tamamı | + calibration, modeling | Yalnızca `app`'i değiştirerek genel olur |

### 2c. Sızıntının iki geçidi

1. **`features` → manifest yolu.** `bundle`, `decision`, `support`, `catalog`, `data_source` hep
   `ROOT`'u `features.MANIFEST_PATH`'ten türetir. Roadmap'in kendi manifesti olacaksa bu
   modüller yol parametresi almadan doğrudan kullanılamaz.
2. **`support` → `baseline`/`modeling` (tembel).** `support.build` LC-CSV'yi ve `modeling.dev_frame`'i
   çağırır. `recourse_scorers` aynı yoldan bundle modeline ve kalibratöre gider. Modül düzeyinde
   görünmez, ama içe aktaran her şey bu kapanışa (`baseline`, `modeling`, `leakage`, `split`) kadar
   uzanır.

> **Bu bölüm ne demek:** Roadmap'in kredi verisine, manifestine ya da modeline dokunmadan doğrudan içe aktarabileceği modüller yalnızca `canonical`, `ayarlar` ve `calibration`. Diğerleri ya kopyalanıp parametreleştirilmeli ya da kredi bağıyla birlikte gelir.
>
> **Ne DEMEK DEĞİL:** "Sızar", çalışma anında LC verisinin okunacağı anlamına gelmez; çoğu yalnızca yol sabiti ya da tembel importtur. Bu tablo roadmap'in bu modüllere ihtiyacı olduğunu da söylemez.

---

## 3. Testler (`backend/tests`)

Kısaltmalar: **LC-CSV skip** = `CSV.exists()` yoksa `skipif` ile atlanan test (CI'de dosya
olmadığı için atlanır); **bundle** = `bundle/`, `bundle.lock.json` ya da policy v1 hashine kilitli;
**doc-kilidi** = `docs/*.md` içeriğini dondurulmuş sayılarla karşılaştırır.

| Grup | Testler | Bağlılık |
|---|---|---|
| **Genel** (sentetik ya da tmp_path; kredi verisi yok) | `test_canonical` (kısmen; sonu policy v1 kullanır), `test_bundle` (tmp_path ile `build_lock`/`verify_lock`), `test_final_report_guard` (tek seferlik koruma, tmp_path), `test_rejected_scale` (tmp_path CSV) | Genel mantık; `test_canonical` dışındakiler kredi config'i okumaz |
| **Depo geneli kural taraması** | `test_forbidden_phrases` | `configs/forbidden_phrases.json` + elle yazılmış dosya listesi (`docs/adr`, `docs/week*`, katalog, `schemas.py`, `frontend/src/texts.json`, belirli `docs/demo_*.md`). Liste kredi belgelerini sayar; `test_scan_covers_the_expected_files` beklenen adları sabitler |
| **Kredi config'i / policy v1 (veri yok)** | `test_policy`, `test_decision`, `test_decision_engine`, `test_decision_properties`, `test_cost` (`cost.yaml`), `test_units`, `test_action_evidence`, `test_resilience_label`, `test_ui_texts`, `test_api`, `test_health`, `test_support_file` (kısmen), `test_support_check` (kısmen), `test_recourse` (kısmen), `test_default_delta_label`, `test_batch_manifest`, `test_rule_coverage`, `test_effect_share` (kısmen) | Manifest, `cost.yaml`, `decision.yaml`, policy v1, `support.yaml`, katalog. Çoğu `SyntheticScorer` ile modeli atlar |
| **Dondurulmuş bundle / altın küme** | `test_golden` (`tests/golden`, policy v1 SHA), `test_ui_cases` (`tests/golden`, `frontend/src/ornekler.json`), `test_batch_manifest` (`golden._basvuru`), `test_recourse` (`bundle/calibration_data.npz`), `test_counteroffer_economics`, `test_counteroffer_calibration_check`, `test_pilot_protocol`, `test_delta_comparison`, `test_claims`, `test_target_segment`, `test_safety_margin` | Bundle hashleri, `tests/golden`, doc-kilidi (`docs/CLAIMS.md`, `docs/demo_*.md`, `docs/pilot_protocol_v0.md`) |
| **LC-CSV (ham LC türevi, v1 yolu)** | `test_features`, `test_split`, `test_leakage`, `test_modeling`, `test_support_file`, `test_support_check`, `test_recourse`, `test_effect_share`, `test_ui_cases` — her birinde en az bir `skipif(not CSV.exists())` | `credit-coach/data/lending_club/…48_features….csv`; `test_modeling` ve `test_calibration` ayrıca `backend/.models/` |
| **LC-CSV yokluğu davranışı** | `test_portfolio_report`, `test_resilience_report`, `test_target_segment`, `test_safety_margin` | `baseline.CSV`'yi var olmayan yola çevirip raporun yazılmadığını denetler; dosyayı okumaz |
| **LC reddedilen dosya** | `test_data_source`, `test_rejected_overlap` | `configs/data_source.yaml`, `CREDIT_COACH_REJECTED_LC`; büyük dosya yoksa atlanır |
| **Postgres** | `test_db_smoke`, `test_decision_log`, `test_replay` (+ `conftest.py`) | `CREDIT_COACH_TEST_DB_URL`, `CREDIT_COACH_APP_DB_URL`; CI'de zorunlu, yerelde atlanır |
| **Ham accepted CSV (`CREDIT_COACH_RAW_LC`)** | **Hiçbiri** | Bu değişkeni yalnızca `cost_report.py` okur; onu çağıran test yok |

Not: `test_calibration` LC-CSV yolunu `tests.test_features`'tan içe aktarır ve
`backend/.models/pd_monotone.json`, `venn_abers.joblib` dosyalarına bağlıdır (bundle değil).

> **Bu bölüm ne demek:** Hangi testin roadmap alt paketine örnek olabileceği (genel grup ve tek seferlik koruma), hangilerinin kredi verisi, bundle ya da Postgres olmadan anlamsız olduğu.
>
> **Ne DEMEK DEĞİL:** "Genel" testlerin roadmap için hazır olduğunu söylemez; kredi modüllerini test ederler. CI'de LC-CSV testlerinin atlanması, o kodun CI'de hiç denenmediği anlamına gelir, geçtiği anlamına değil.

---

## 4. CI (`.github/workflows/ci.yml`) ve `Makefile`

| Hedef | Ne yapar | Roadmap'e taşınmalı mı |
|---|---|---|
| CI `backend`: `uv sync --locked`, `ruff check .`, `pytest -q -rs` | Tüm backend testleri + Postgres servisi | **Paylaşılır, taşınmaz.** Roadmap testleri `backend/tests` altında ise aynı adımda koşar. Ayrı bir iş isterseniz `pytest -k roadmap` ya da ayrı dizin ile eklenebilir |
| CI `backend`: `python -m credit_coach.bundle verify` | Kredi bundle hashleri | **Hayır.** Kredi-veren-özel. Roadmap'in dondurulmuş dosyası olursa kendi `FILES` listesiyle ayrı bir adım gerekir |
| CI `types`: `make types` + `git diff --exit-code` | OpenAPI → TS tipleri senkron mu | **Paylaşılır.** Roadmap API ucu eklerse aynı adımla denetlenir; `export_openapi` tek `app` üzerinden çalışır |
| CI `e2e`: build + `scan:forbidden` + Playwright | Arayüz ve yasaklı ifade taraması | **Paylaşılır.** Roadmap arayüz metni eklerse `texts.json` taramasına girer |
| `make openapi`, `make types` | Yukarıdaki | Paylaşılır |
| `make lint`, `make test`, `make check` | ruff, pytest, tip denetimi | Paylaşılır; roadmap'e özel kopya gerekmez |
| `make demo` (`scripts/demo.sh`) | Kredi demosu | **Hayır**, kredi-veren-özel |
| `make report` (`credit_coach.portfolio_report`) | Kredi portföy raporu | **Hayır**, ölçüm-özel. Roadmap raporu olacaksa ayrı hedef (örn. `make roadmap-report`) eklenir |

Gözlem: CI'de Python için yasaklı ifade taraması `test_forbidden_phrases` ile `pytest` içinde
koşar. Yeni roadmap belgeleri taranacaksa dosya listesine elle eklenmesi gerekir; ecom dalları
bunu böyle yaptı (bkz. bölüm 5).

> **Bu bölüm ne demek:** Mevcut CI ve Makefile hedeflerinin roadmap için hangilerinin olduğu gibi işe yarayacağı, hangilerinin krediye özel kalacağı.
>
> **Ne DEMEK DEĞİL:** CI'de değişiklik önerisi değildir; hiçbir iş ya da hedef eklenmedi veya taşınmadı.

---

## 5. Ek: birleşmemiş ecom dalları (yalnızca okuma)

Dallar üst üste kurulu; dördünün de main ile ortak tabanı c8ec459.

| Dal | Uç | `credit_coach/ecom/` içeriği |
|---|---|---|
| `ecom-e0-data-check` | e54c9cd | `__init__`, `e0_data_check` |
| `ecom-e1-hillstrom` | f63e22a | + `e1_hillstrom`, `uplift` |
| `ecom-e2-criteo` | 760f9c3 | + `e2_criteo`; `uplift` ve `e1_hillstrom` güncellendi |
| `ecom-summary` | 021872f | `ecom-e2-criteo` ile aynı kod; yalnızca `docs/ecom/SUMMARY.md` ve tarama listesine 2 satır eklenmiş |

`e0_data_check.py` dört dalda aynı. `e1_hillstrom.py` e1 → e2 arasında 6 satır, `uplift.py` 42
satır değişti. Aşağıdaki envanter `ecom-summary` (en son) üzerindendir.

### 5a. Ecom modülleri

| Modül | Amaç | Veri / eşik | İç importlar | Sınıf |
|---|---|---|---|---|
| `ecom/__init__` | Paket | — | — | GENEL |
| `ecom/e0_data_check` | E0 veri doğrulaması: satır sayısı, Pandera şeması, SMD denge, lisans, durdurma kuralı; `docs/ecom/E0_data_check.md` yazar | `configs/ecom_data_source.yaml` (yol + SHA-256), Hillstrom ve Criteo CSV; sabit eşikler `HILL_ROWS`, `CRITEO_ROWS`, `CRITEO_P`, `SMD_MAX=0.05` | — (kredi modülü yok) | ÖLÇÜM-ÖZEL (içindeki `smd`, `smd_rows`, `failing_rows`, `read_csv_sql` GENEL) |
| `ecom/uplift` | Tabakalı bölme, bölme karması, iki model ailesi, Qini, desil tablosu, kalibrasyon eğimi, politika değeri, bootstrap | `SEED=20261111`, `FRACS=0.6/0.2/0.2`; sklearn | — | UYARLANABİLİR (RCT'ye özgü bölme; metrikler genel) |
| `ecom/e1_hillstrom` | Hillstrom üzerinde `split` / `select` / `test` komutları, tek seferlik test kilidi | Hillstrom CSV, `docs/ecom/test_run_hillstrom.lock`, `E1_selection.md` | ecom, ecom.e0_data_check, ecom.uplift | ÖLÇÜM-ÖZEL |
| `ecom/e2_criteo` | Criteo'da yeniden üretim; `Watchdog` (süre/bellek sınırı), ağırlıklı SMD, bootstrap | Criteo CSV, `test_run_criteo.lock`, `E2_selection.md`; `FIT_LIMIT_S`, `MEM_LIMIT=0.80` | ecom, ecom.e0_data_check, ecom.e1_hillstrom, ecom.uplift | ÖLÇÜM-ÖZEL |

Testler: `test_ecom_e0` (yalıtım + SMD + şema + durdurma kuralı), `test_ecom_e1` (bölme
belirlenimciliği, Qini, τ bit eşitliği, kilit reddi, mutasyon testi), `test_ecom_e2` (ağırlıklı
SMD, bootstrap adımı, kilit reddi). Üçü de sentetik veriyle çalışır, ham CSV gerektirmez.
Kredi tarafına dokunan tek değişiklik `test_forbidden_phrases.py`'ye eklenen `docs/ecom/*.md`
dosyaları.

### 5b. Yeniden kullanılabilir desenler

| Desen | Nerede | Yeni alt paket taşıyabilir mi | Not |
|---|---|---|---|
| **Veri doğrulama (E0)**: yol + SHA-256 kaydı, satır sayısı, Pandera şeması, sabit eşiklerle durdurma kuralı, rapor + "ne demek / ne DEMEK DEĞİL" notları | `e0_data_check` (`check_*`, `evaluate`, `decision`, `render`, `NOTES`) | **Evet, desen olarak.** `smd`, `smd_rows`, `failing_rows`, `read_csv_sql` olduğu gibi alınabilir; `check_hillstrom/criteo` ve eşikler veri setine özgü | Ana daldaki `data_source.py` ile aynı fikir (yol + SHA, kopyalama yok) ama daha eksiksiz |
| **Bölme ve karma**: tabakalı, seed'li bölme; etiket dizisinin SHA-256'sı yaml'a yazılır, her komut önce karmayı denetler | `uplift.stratified_split`, `uplift.split_hash`, `e1_hillstrom.check_split` | **Karma denetimi: evet. Rastgele bölme: yalnızca RCT verisinde.** | ADR-008 rastgele bölmeyi yalnızca `credit_coach.ecom` ve RCT için açar; roadmap için yeni bir ADR gerekir. Zamanlı veride `split.py`'nin zaman bölmesi + aynı karma denetimi birleştirilebilir |
| **Tek seferlik test kilidi**: kilit dosyası `open("x")` ile yazılır (varsa hata); temiz ağaç ve commit'lenmiş seçim belgesi şartı; kilit commit + veri SHA + bölme karması + zaman taşır | `e1_hillstrom.write_lock`/`cmd_test`, `e2_criteo.write_lock`/`cmd_test` | **Evet.** Ana daldaki `final_test_report.guard` (rapor varsa reddet) ile aynı amaç; ecom sürümü daha sıkı (git durumu + karma) | Testi var: `test_test_run_refuses_when_lock_exists` |
| **Pandera şeması** | `e0_data_check.hillstrom_schema`/`criteo_schema` (`strict=True, ordered=True`, `isin`, `ge(0)`, sonlu kontrolü) | **Evet, desen olarak.** Ana daldaki `features.build_schema` manifestten şema üretir; ecom elle yazar | Roadmap manifest YAML'ı kullanacaksa `features.build_schema` yaklaşımı CLAUDE.md'ye daha uygun; ama `features` LC manifest yoluna sabit (bölüm 2) |
| **Yalıtım testi**: alt paketteki her `.py`'de AST ile `credit_coach.*` (kendi alt paketi hariç) ve `level > 1` göreli importları yasaklar | `test_ecom_e0.test_ecom_does_not_import_credit_modules` | **Evet, neredeyse aynen.** Yalnızca paket adı değişir | Sınır: yalnızca doğrudan importları denetler; ecom hiç kredi modülü almadığı için geçişli kapanış da boş. Roadmap 2a'daki genel modülleri alacaksa izin listesi gerekir |
| **Belirlenimcilik** | `test_tau_is_bit_identical_across_runs_for_both_families`, `uplift.tie_key` | Evet | Seed'li; karar yolunda değil |
| **Kaynak/süre bekçisi** | `e2_criteo.Watchdog` | Belki (emin değilim) | Büyük veri için; macOS/Linux RSS farkını ele alıyor |

### 5c. Ecom'dan yeni alt pakete taşınabilecekler

| Parça | Olduğu gibi | Kopyalanıp uyarlanmalı | Taşınmamalı |
|---|---|---|---|
| `uplift.split_hash`, `uplift.ci`, `uplift.bootstrap_weights` | ✓ | | |
| `e0_data_check.smd`, `smd_rows`, `failing_rows`, `read_csv_sql` | ✓ | | |
| `uplift.stratified_split` | | ✓ (yalnızca RCT verisi için; aksi halde zaman bölmesi + ADR) | |
| `write_lock` / `cmd_test` kilit mantığı | | ✓ (yollar ve kaynak anahtarları sabit) | |
| Yalıtım testi | | ✓ (paket adı + izin listesi) | |
| E0 iskeleti (`evaluate` → `decision` → `render` + `NOTES`) | | ✓ | |
| `uplift` metrikleri (Qini, desil, eğim, politika değeri) | | ✓ yalnızca roadmap uplift ölçecekse | |
| `check_hillstrom`, `check_criteo`, `e1_hillstrom`, `e2_criteo` | | | ✓ (veri setine özgü deney betikleri) |

> **Bu bölüm ne demek:** Birleşmemiş ecom kodunda kredi modüllerinden bağımsız olan ve yeni bir alt pakete desen ya da kopya olarak geçebilecek parçalar.
>
> **Ne DEMEK DEĞİL:** Ecom dallarının birleşeceğini ya da sonuçlarının (E1/E2'de 2. ölçüt başarısız) roadmap için geçerli olduğunu söylemez. ADR-008'in rastgele bölme istisnası roadmap'e uzanmaz. Bir gözlem: ADR-008 atamayı "satır kimliğinin sabit karmasıyla" diye tanımlar, `uplift.stratified_split` ise seed'li permütasyon kullanır; karmayla yapılan `tie_key` yalnızca eşitlik bozmada kullanılıyor (emin değilim, ayrıca bakılmalı).
