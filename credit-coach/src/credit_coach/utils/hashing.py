"""
utils/hashing.py
================
Dataset ve config değişimini tespit etmek için SHA-256 hash yardımcıları.

Neden var?
----------
- Pipeline'ın herhangi bir adımında "bu veri daha önce işlendi mi?"
  sorusunu cevaplamak için dosya hash'i kullanılır.
- Config değişti mi? → config hash farklıysa run yeniden yapılmalı.
- Bu mekanizma ileride kenar case'lere karşı ingest/train'i
  otomatik skip etmeyi sağlar.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# SHA-256 blok boyutu — büyük dosyalar için chunk okuma
_CHUNK_SIZE = 65_536  # 64 KB


def hash_file(path: str | Path, algorithm: str = "sha256") -> str:
    """
    Bir dosyanın SHA-256 (veya başka algoritma) hash'ini döndürür.

    Büyük CSV/Parquet dosyalarını chunk'lar halinde okuyarak
    bellek taşmasını önler.

    Parameters
    ----------
    path : str | Path
        Hash'lenecek dosya yolu.
    algorithm : str
        hashlib algoritma adı ("sha256", "md5", vb.)

    Returns
    -------
    str
        Hex-encoded hash string. Örnek: "a3b4c5d6..."

    Raises
    ------
    FileNotFoundError
        Dosya bulunamazsa.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Hash hesaplanamadı — dosya yok: {path}")

    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def hash_config(cfg: dict[str, Any], algorithm: str = "sha256") -> str:
    """
    Python dict (config) nesnesinin deterministik hash'ini hesaplar.

    `sort_keys=True` ile her çalışmada aynı dict aynı hash'i verir.

    Parameters
    ----------
    cfg : dict
        Hash'lenecek konfigürasyon sözlüğü.
    algorithm : str
        hashlib algoritma adı.

    Returns
    -------
    str
        Hex-encoded hash string.
    """
    serialized = json.dumps(cfg, sort_keys=True, ensure_ascii=False)
    h = hashlib.new(algorithm)
    h.update(serialized.encode("utf-8"))
    return h.hexdigest()


def short_hash(value: str, length: int = 8) -> str:
    """
    Herhangi bir string için kısa (truncated) SHA-256 hash.

    Örnek kullanım: run_id suffix üretimi.

    Parameters
    ----------
    value : str
        Hash'lenecek string.
    length : int
        Hash'in kaç karakteri kullanılacak (default 8).

    Returns
    -------
    str
        `length` uzunluğunda hex string.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def canonical_json(value: Any) -> str:
    """
    Deterministik JSON string (audit/hash zinciri icin).
    """
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def hash_chain_event(
    payload: dict[str, Any],
    prev_hash: str | None,
    algorithm: str = "sha256",
) -> str:
    """
    Hash zinciri icin event hash uretir.

    Hash girdisi:
        <prev_hash_or_genesis>|<canonical_payload_json>
    """
    h = hashlib.new(algorithm)
    prev = prev_hash if prev_hash else "GENESIS"
    h.update(prev.encode("utf-8"))
    h.update(b"|")
    h.update(canonical_json(payload).encode("utf-8"))
    return h.hexdigest()
