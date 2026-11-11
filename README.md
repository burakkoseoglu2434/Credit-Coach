# Credit Coach v2 (demo v0)

> Kredi veren: tek fiyatlı kurgusal kredi veren. Model 2012-15 ABD (LendingClub) verisiyle eğitildi; ayrıntı için `docs/CLAIMS.md`.

1. Gerekenler: `uv`, Node 20+, `make`. Ham veri, Postgres, MLflow gerekmez.
2. `git clone https://github.com/burakkoseoglu2434/Credit-Coach.git && cd Credit-Coach`
3. `make demo` bağımlılıkları kurar, arayüzü derler, backend ve arayüzü başlatır (servis `bundle/` klasöründen çalışır).
4. Tarayıcıda `http://127.0.0.1:4173` adresini açın (örnek vakalar ve toplu mod orada).
5. Durdurmak için `Ctrl+C`. Testler: `make check`. Portföy raporu (ham veri gerekir): `make report`.
