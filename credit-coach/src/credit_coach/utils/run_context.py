"""
utils/run_context.py
====================
Her pipeline çalışmasına benzersiz bir `run_id` atar ve bu çalışmaya ait
artifact klasör yapısını (`artifacts/runs/<run_id>/`) oluşturur.

Neden var?
----------
- Traceability: Hangi config ile hangi sonuçların üretildiği her zaman
  takip edilebilir olmalı (AGENT GUIDE kural #3).
- Reproducibility: Config snapshot run klasörüne kopyalanır, böylece
  aylarca sonra bile aynı sonuç yeniden üretilebilir.
- Separation of concerns: Her run kendi sandbox'ında; önceki sonuçlar
  bozulmaz.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class RunContext:
    """
    Tek bir pipeline çalışmasının bağlamını tutar.

    Attributes
    ----------
    run_id : str
        Zaman damgası + config hash'inden türetilmiş benzersiz id.
        Örnek: "20260305_130421_a3f2b1"
    artifact_dir : Path
        Bu çalışmaya ait çıktı klasörü: artifacts/runs/<run_id>/
    config : dict
        Çalışma için yüklenen tam konfigürasyon.
    """

    run_id: str
    artifact_dir: Path
    config: dict[str, Any] = field(default_factory=dict)

    # Alt klasörler — run başlayınca otomatik oluşturulur
    _tables_dir: Path = field(init=False)
    _figures_dir: Path = field(init=False)
    _logs_file: Path = field(init=False)

    def __post_init__(self) -> None:
        self._tables_dir = self.artifact_dir / "tables"
        self._figures_dir = self.artifact_dir / "figures"
        self._logs_file = self.artifact_dir / "logs.txt"
        self._ensure_dirs()

    # ------------------------------------------------------------------ #
    # Klasör yönetimi
    # ------------------------------------------------------------------ #
    def _ensure_dirs(self) -> None:
        """Gerekli tüm alt klasörleri oluşturur."""
        for d in [self.artifact_dir, self._tables_dir, self._figures_dir]:
            d.mkdir(parents=True, exist_ok=True)
        logger.info("RunContext artifact dir ready: %s", self.artifact_dir)

    @property
    def tables_dir(self) -> Path:
        return self._tables_dir

    @property
    def figures_dir(self) -> Path:
        return self._figures_dir

    @property
    def logs_file(self) -> Path:
        return self._logs_file

    # ------------------------------------------------------------------ #
    # Config snapshot kaydetme
    # ------------------------------------------------------------------ #
    def save_config_snapshot(self) -> Path:
        """
        Mevcut config'i `config_snapshot.yaml` olarak run klasörüne yazar.

        Bu dosya sayesinde ileride "hangi parametrelerle çalıştırıldı?"
        sorusu doğrudan klasörden yanıtlanabilir.
        """
        snapshot_path = self.artifact_dir / "config_snapshot.yaml"
        with open(snapshot_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
        logger.info("Config snapshot saved: %s", snapshot_path)
        return snapshot_path

    # ------------------------------------------------------------------ #
    # Metrics kaydetme
    # ------------------------------------------------------------------ #
    def save_metrics(self, metrics: dict[str, Any]) -> Path:
        """
        Sözlük formatındaki metrikleri `metrics.json` olarak kaydeder.

        Parameters
        ----------
        metrics : dict
            Örnek: {"auc": 0.82, "f1": 0.71, "brier": 0.12}
        """
        metrics_path = self.artifact_dir / "metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        logger.info("Metrics saved: %s", metrics_path)
        return metrics_path

    def __repr__(self) -> str:
        return f"RunContext(run_id={self.run_id!r}, artifact_dir={self.artifact_dir})"


# ------------------------------------------------------------------ #
# Factory fonksiyonu
# ------------------------------------------------------------------ #
def create_run_context(
    config: dict[str, Any],
    base_artifact_dir: str | Path = "artifacts/runs",
) -> RunContext:
    """
    Yeni bir RunContext oluşturur.

    run_id uretim mantigi
    ---------------------
    1) Geçerli timestamp (saniye hassasiyetinde) alınır.
    2) Config dict'in SHA-256 hash'inin ilk 6 karakteri eklenir.
    3) Son olarak 6 haneli nonce eklenir.
    4) Sonuc: "YYYYMMDD_HHMMSS_<hash6>_<nonce6>"

    Bu sayede ayni saniyede ayni config ile birden fazla run baslasa bile
    run_id cakismaz.

    Parameters
    ----------
    config : dict
        Çalışma için kullanılan tüm konfigürasyon.
    base_artifact_dir : str | Path
        Çalışma klasörlerinin oluşturulacağı ana dizin.

    Returns
    -------
    RunContext
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    config_bytes = json.dumps(config, sort_keys=True, ensure_ascii=False).encode()
    config_hash = hashlib.sha256(config_bytes).hexdigest()[:6]
    nonce = uuid.uuid4().hex[:6]
    run_id = f"{timestamp}_{config_hash}_{nonce}"

    artifact_dir = Path(base_artifact_dir) / run_id

    ctx = RunContext(run_id=run_id, artifact_dir=artifact_dir, config=config)
    ctx.save_config_snapshot()
    return ctx


def load_config(config_path: str | Path) -> dict[str, Any]:
    """
    YAML config dosyasını yükler.

    Parameters
    ----------
    config_path : str | Path
        Yüklenecek YAML dosyasının yolu.

    Returns
    -------
    dict
        YAML içeriği.

    Raises
    ------
    FileNotFoundError
        Dosya bulunamazsa.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config dosyası bulunamadı: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logger.debug("Config loaded: %s", config_path)
    return cfg or {}
