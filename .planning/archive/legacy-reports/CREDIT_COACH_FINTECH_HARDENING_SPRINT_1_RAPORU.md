# CREDIT COACH FINTECH HARDENING - SPRINT 1 RAPORU

## 0) Kapsam
Sprint: `Sprint-1 (Hafta 1-2)`  
Backlog maddeleri: `A1, A2, A3`  
Tarih: `2026-03-07`

Hedefler:
1. API rate-limit (A1)
2. Hash-chain audit event altyapisi (A2)
3. Token rotation/expiry/grace policy (A3)

---

## 1) Yapilan Degisiklikler (Dosya Bazli)

### 1.1 API auth ve rate limit
- `credit-coach/src/credit_coach/api/auth.py`
  - `TokenPolicyEntry` eklendi (status/expires_at/grace_until)
  - `CREDIT_COACH_API_KEYS_JSON` destegi eklendi
  - `configs/security.yaml` tabanli auth/rate-limit config okuma eklendi
  - `FixedWindowRateLimiter` eklendi
  - `check_rate_limit()` ve `reset_rate_limiters()` eklendi

- `credit-coach/src/credit_coach/api/main.py`
  - Auth sonrasi endpoint bazli rate-limit kontrolu eklendi
  - Limit asiminda `429` + `Retry-After` header davranisi eklendi

- `credit-coach/configs/security.yaml` (yeni)
  - Auth policy ve endpoint bazli rate-limit varsayilanlari tanimlandi

### 1.2 Audit hash chain
- `credit-coach/src/credit_coach/storage/models.py`
  - Yeni tablo: `AuditEventORM` (`event_hash`, `prev_hash`, `payload_json`)

- `credit-coach/src/credit_coach/utils/hashing.py`
  - `canonical_json()` eklendi
  - `hash_chain_event()` eklendi

- `credit-coach/src/credit_coach/storage/repository.py`
  - `save_plan` ve `save_model_run` icine otomatik audit event yazimi eklendi
  - `save_customer_snapshot`, `save_macro_snapshot` icin de audit event eklendi
  - `save_audit_event()`, `get_audit_events()`, `verify_audit_chain()` eklendi

- `credit-coach/src/credit_coach/cli/run_audit_verify.py` (yeni)
  - Zincir dogrulama CLI komutu eklendi

### 1.3 Test ve dokumantasyon
- `credit-coach/tests/test_api_rate_limit.py` (yeni)
- `credit-coach/tests/test_auth_rotation.py` (yeni)
- `credit-coach/tests/test_audit_chain.py` (yeni)
- `credit-coach/README.md`
  - Security komut ve guvenlik notlari guncellendi

---

## 2) Calistirilan Komutlar ve Sonuclar

1. Hedefli sprint testleri:
```bash
cd credit-coach && pytest -q tests/test_auth.py tests/test_api_rate_limit.py tests/test_auth_rotation.py tests/test_audit_chain.py tests/test_model_pipeline.py tests/test_dice_baseline.py
```
Sonuc: `11 passed`

2. Tam regresyon:
```bash
cd credit-coach && pytest -q
```
Sonuc: `51 passed, 7 warnings`

3. Audit verify CLI:
```bash
cd credit-coach && python -m credit_coach.cli.run_audit_verify
```
Sonuc: `Audit chain verification PASSED. events=0`

Not:
- `events=0` sonucu, mevcut varsayilan DB'de bu komut calistirilana kadar audit event olusmamis olmasindan kaynaklidir.
- `test_audit_chain.py` testinde event olusturulup zincir dogrulamasi ve tamper tespiti dogrulanmistir.

---

## 3) Test Sonuclari

Yeni testler:
1. `test_api_rate_limit.py`
   - Fixed-window limiter limit asiminda blokluyor.
   - Endpoint override config dogru calisiyor.
2. `test_auth_rotation.py`
   - Active/next/retired+grace policy dogrulandi.
   - Expired ve grace disi token reddedildi.
3. `test_audit_chain.py`
   - Zincir saglikli durumda PASS.
   - Payload tampering sonrasinda verify FAIL.

Regresyon:
1. Mevcut test seti bozulmadi.
2. Toplam su an: `51 passed`.

---

## 4) KPI ve Backlog Durumu

Sprint-1 backlog:
1. `A1 - API rate limiting`: Tamamlandi
2. `A2 - Audit event hash chain`: Tamamlandi
3. `A3 - Secret rotation/token policy`: Tamamlandi

Sprint gate:
1. Kritik guvenlik testleri PASS.
2. Zincir dogrulama mekanizmasi testle kanitlandi.

---

## 5) Acilan Riskler ve Teknik Borc
1. `datetime.utcnow()` kullanimlari Python 3.13 deprecation warning uretiyor.
2. Rate-limit state memory-ici tutuluyor; multi-instance dagitim icin Redis tabanli limiter gerekir.
3. Audit verify CLI varsayilan DB uzerinde calistiginda event olmayabilir; operasyonel calisma icin uretim pipeline event akisi surekli olmalidir.

---

## 6) Sonraki Sprint Giris Kosullari (Sprint-2)
1. `A1/A2/A3` kodu ana akisa merge edilmeye hazir.
2. Sprint-2 icin hedef: `B1, B2, B3` (XGBoost primary profile + SHAP stability + DiCE adapter hardening).

