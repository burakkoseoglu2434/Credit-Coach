# Credit Coach v2

Bu depo Credit Coach v2'nin temelidir. Aşağıdaki kurallar tüm işlerde geçerlidir.

## Kurallar

- Karar yolundaki her bileşen deterministiktir. Rastgelelik, LLM, DiCE, LIME, KernelSHAP karar yoluna girmez.
- Model yalnızca başvuru anında bilinen özellikleri kullanır. `int_rate`, `grade`, `sub_grade`, `debt_settlement_flag` ve kredi sonrası alanlar yasaktır.
- Veri: DuckDB + Parquet, doğrulama Pandera, özellik tanımı YAML manifesto.
- Backend: tek FastAPI servisi, Pydantic şemaları tek doğruluk kaynağı, TypeScript tipleri OpenAPI'dan üretilir.
- Bölme `issue_d` ile zamana göredir, rastgele bölme yasaktır.
- Her adım testle biter. Test geçmeden "bitti" deme.
- Küçük commit'ler at, her commit tek bir iş yapsın.

## Yerleşim

- `/backend` FastAPI, Pydantic, pytest, ruff
- `/frontend` React + TypeScript + Vite
- `/data` raw ve parquet (git'e girmez)
- `/configs`, `/tests`, `/docs/adr`
- `/credit-coach`, `/credit-coach-website`, `/.planning` v1 mirasıdır; v2 kodu bunlara bağımlı olmaz.
