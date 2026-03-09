"""
tests/conftest.py
=================
Pytest fixtures — testlerde ortak kullanılan nesneler.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import yaml


@pytest.fixture(scope="session")
def feature_list_48() -> list[str]:
    """configs/features_48.yaml'daki 48 feature listesini döndürür."""
    yaml_path = Path(__file__).parents[1] / "configs" / "features_48.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["features"]


@pytest.fixture(scope="session")
def features_config() -> dict:
    """features_48.yaml'ın tamamını döndürür."""
    yaml_path = Path(__file__).parents[1] / "configs" / "features_48.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture()
def temp_db_url(tmp_path: Path) -> str:
    """Test için geçici SQLite DB URL'i döndürür."""
    db_file = tmp_path / "test_credit_coach.db"
    return f"sqlite:///{db_file}"


@pytest.fixture()
def sample_features(feature_list_48: list[str]) -> dict:
    """
    48 feature için örnek değerler içeren dict.
    Tüm değerler 0.0 (placeholder); testlerde override edilebilir.
    """
    return {f: 0.0 for f in feature_list_48}
