# Hafta 1 İlerleme Raporu (WEEK1_PROGRESS.md)

Bu doküman, Credit Coach projesinin 1. haftasında (Temel İskelet ve Konfigürasyon) yapılan çalışmaları mimari gerekçeleriyle açıklar. Amaç; repo incelenirken *hangi dosyanın neden oluşturulduğunu*, *hangi sırayla çalıştığını* ve *hangi fonksiyonun ne işe yaradığını* kolayca takip edebilmektir.

---

## 1. Mimari Kararlar ve Dosya Sorumlulukları

Hafta 1 hedefleri doğrultusunda sistemin belkemiği olan **Veri Kontratları**, **Veritabanı Katmanı** ve **Aksiyon Uzayı** tasarlandı.

### A. Konfigürasyon Katmanı (`configs/`)
Her şeyin koda (hard-code) gömülmek yerine dışarıdan (YAML) yönetilebilmesi kuralı uygulandı.

- **`features_48.yaml` (⭐⭐⭐⭐⭐ Kritik)**: Mimarinin "tek gerçeği". LendingClub verisinden hangi 48 kolonun model eğitimine / tahminine gireceğini kilitler. Testler ve pipeline, fazladan kolon gelirse atar, eksik kolon gelirse hata verir.
- **`default.yaml` - `model.yaml` - `macros.yaml` vb.**: Sonraki haftalardaki modüllerin (XGBoost parametreleri, şok senaryoları, webhook url'leri vs.) parametrelerini içerir.

### B. Şema ve Veri Kontratları Katmanı (`src/credit_coach/data/schema.py`)
Python'ın Pydantic v2 kütüphanesi ile sistemden akan verinin *neye benzemesi* gerektiği tanımlandı.
- `CustomerSnapshot`: Müşterinin belirli bir T anındaki 48 değişkeni ve risk değerini tutar ($x_t$).
- `MacroSnapshot`: Makroekonomik değişkenleri ($z_t$) tutar.
- `PlanRecord`: Üretilecek olan reçeteyi/planı (actions, score, risk_margin, CI değerleri) tutar.
- *Neden Pydantic?*: Bir modülden diğerine veri gönderirken tip hatalarını derhal (çalışma anında) yakalamak için.

### C. Depolama Katmanı (`storage/`)
Tez verisi "dosyada" kalırken, ürünün "durumu" (state) bir veritabanında tutulur. Bu nedenle SQLite (ileride PostgreSQL) için SQLAlchemy kuruldu.
- **`db.py`**: DB bağlantısını (engine) ve session_maker'ı yönetir. `init_db()` tablolara şekil verir.
- **`models.py`**: `schema.py`'daki nesnelerin *veritabanında nasıl saklanacağını* anlatır (`CustomerSnapshotORM`, `PlanRecordORM`). Listeler veya Pydantic objeleri JSON serialize edilerek `Text` kolonlarına gömülür.
- **`repository.py`**: Diğer modüller SQLAlchemy veya SQL sorgusu yazmasın (*Separation of Concerns*) diye, sadece fonksiyonları çağırarak (`save_plan`, `get_plans_for_customer`) veritabanına erişebilmeleri için aracı (CRUD) katmanıdır.

### D. Aksiyon Uzayı (`recourse/action_space.py`)
Kredi planlaması (recourse) yaparken, sistem müşteriye "hangilerini değiştirebileceğini", "ne sürede", "ne kadara" değiştirebileceğini bilmelidir.
- `ACTION_SPACE` sözlüğü: Bütün 48 kolon tek tek etiketlenmiştir (`actionable=True/False`). "Kredi vadesi" gibi özellikler güncellenemez (immutable), ama "DTI" düşürülebilir "Yıllık Gelir" yükseltilebilir şekilde ayarlanmıştır. Algoritma (ilerleyen haftalarda "Beam Search") bu haritaya basarak ilerleyecektir.

### E. Araç Kutusu ve Çalışma Bağlamı (`utils/`)
- **`run_context.py`**: Her eğitim/inference başladığında bir `run_id` (örn. `20260305_130421_a3f2b1`) üretir ve `artifacts/runs/` altına özel bir log/çıktı klasörü açar. Sonuçların sonradan bulunmasını (Traceability) sağlar.

---

## 2. Sistemin Çalışma Akışı (CLI)

Hafta 1'in görünür çıktısı `run_train.py --dry_run` komutudur. Akış şöyledir:

1. CLI çalıştırılır: `python -m credit_coach.cli.run_train --dry_run`
2. **`check_imports()`**: Projedeki bütün kritik modülleri yüklemeye çalışır, sözdizimi / import hatası olup olmadığını denetler.
3. **`check_config()`**: `load_config` ile tanımlanan tüm YAML içeriklerinin sağlıklı ayrıştırılabildiğini dogrular.
4. `RunContext` oluşturulur, `artifacts/` klasörüne zaman damgalı ilk işlem (run) dosyaları açılır.
5. **`check_db()`**: SQLite oluşturulur ve veri okuma-yazma operasyon testi yapılır.
6. **`check_feature_lock()`**: `features_48.yaml` okunur, tam 48 sütun olduğu ve kilit mekanizmasının devrede olabildiği doğrulanır.
7. **`check_action_space()`**: 48 özelliğin hangilerinin eyleme dönüştürülebilir olduğuna dair rapor üretilir.

*(Terminalde `DRY RUN OK — Hafta 1 tüm kontroller başarılı!` yazısı görülmelidir.)*

---

## 3. Test Odaklı Tasarım (`tests/`)

Projenin çökmemesi kritik öneme sahip kısımlar teste bağlanmıştır:
- `test_feature_lock.py`: YAML ve "fazla kolonu at, eksiğinde çök" kurallarını dener (fail-fast mimarisi).
- `test_action_space.py`: Aksiyon uzayındaki tüm kolonların string yapıda olup olmadığını, sınırlarışı dener (toplam 24 pytest case'i).

Test etmek için terminalden doğrudan `pytest` komutu koşturulur.

---

## 4. Hafta 2'ye Neler Bırakıldı?

1. Ham (*raw*) LendingClub verisinin indirilip sisteme tanıtılması (ingest).
2. Verideki boşlukların doldurulması, encode işlemleri (`preprocess`).
3. Temizlenen verinin `processed/` klasörüne `train.parquet` ve `test.parquet` olarak kilitli 48 kolon yapısıyla kaydedilmesi.