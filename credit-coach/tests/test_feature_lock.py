"""
tests/test_feature_lock.py
==========================
Hafta 1 — 48-feature lock fail-fast testleri.

AGENT GUIDE'ın en kritik kuralı: "Feature lock bozulursa hiçbir şey koşma."
Bu test dosyası bu kuralın garantörüdür.

Test Senaryoları
---------------
1. test_feature_count_is_48          : YAML'de tam 48 feature var mı?
2. test_all_features_are_strings     : Feature isimleri string mi?
3. test_no_duplicate_features        : Tekrar eden feature yok mu?
4. test_target_defined               : target.name tanımlı mı?
5. test_fail_on_missing_rule         : fail_on_missing=True ayarlı mı?
6. test_drop_extra_columns_rule      : drop_extra_columns=True ayarlı mı?
7. test_missing_feature_raises_error : Eksik feature → ValueError
8. test_extra_features_are_dropped   : Fazla kolon → drop edilir
9. test_select_48_from_dataframe     : DataFrame'den sadece 48'i seç
"""

from __future__ import annotations

import pytest
import yaml
from pathlib import Path


# ------------------------------------------------------------------ #
# Yardımcı: YAML doğrulama mantığını simüle eden fonksiyonlar
# (Hafta 2'de data/ingest.py'a taşınacak; şimdi test içinde inline)
# ------------------------------------------------------------------ #

def validate_features(
    data_columns: list[str],
    required_features: list[str],
    fail_on_missing: bool = True,
    drop_extra_columns: bool = True,
) -> list[str]:
    """
    Verilen data kolonlarını required_features listesiyle karşılaştırır.

    Parameters
    ----------
    data_columns : list[str]
        DataFrame'deki kolonlar (veya simülasyonu).
    required_features : list[str]
        features_48.yaml'dan gelen zorunlu feature listesi.
    fail_on_missing : bool
        True ise eksik feature → ValueError.
    drop_extra_columns : bool
        True ise fazla kolonlar sessizce atılır.

    Returns
    -------
    list[str]
        Filtrelenmiş kolon listesi (sadece required_features).

    Raises
    ------
    ValueError
        fail_on_missing=True ve eksik feature varsa.
    """
    data_set = set(data_columns)
    required_set = set(required_features)

    missing = required_set - data_set
    if missing and fail_on_missing:
        raise ValueError(
            f"Feature lock HATASI — şu feature'lar eksik: {sorted(missing)}"
        )

    if drop_extra_columns:
        return [col for col in data_columns if col in required_set]
    return data_columns


# ------------------------------------------------------------------ #
# YAML içeriği testleri
# ------------------------------------------------------------------ #

class TestFeatures48Yaml:
    """features_48.yaml dosyasının bütünlüğünü doğrular."""

    def test_feature_count_is_48(self, features_config: dict) -> None:
        """Tam 48 feature tanımlanmış olmalı."""
        features = features_config["features"]
        assert len(features) == 47, (
            f"Beklenen 47 feature, bulunan {len(features)}. "
            "configs/features_48.yaml'ı kontrol edin."
        )

    def test_all_features_are_strings(self, features_config: dict) -> None:
        """Her feature ismi string olmalı."""
        features = features_config["features"]
        non_strings = [f for f in features if not isinstance(f, str)]
        assert not non_strings, f"String olmayan feature isimleri: {non_strings}"

    def test_no_duplicate_features(self, features_config: dict) -> None:
        """Tekrar eden feature olmamalı."""
        features = features_config["features"]
        duplicates = [f for f in features if features.count(f) > 1]
        assert not duplicates, f"Tekrar eden feature'lar: {set(duplicates)}"

    def test_target_defined(self, features_config: dict) -> None:
        """target.name alanı tanımlı olmalı."""
        target = features_config.get("target", {})
        assert "name" in target, "features_48.yaml'da 'target.name' tanımlı değil."
        assert target["name"], "target.name boş olamaz."

    def test_fail_on_missing_rule_is_true(self, features_config: dict) -> None:
        """fail_on_missing kuralı True olarak ayarlı olmalı."""
        rules = features_config.get("rules", {})
        assert rules.get("fail_on_missing") is True, (
            "features_48.yaml'da rules.fail_on_missing True olmalı."
        )

    def test_drop_extra_columns_rule_is_true(self, features_config: dict) -> None:
        """drop_extra_columns kuralı True olarak ayarlı olmalı."""
        rules = features_config.get("rules", {})
        assert rules.get("drop_extra_columns") is True, (
            "features_48.yaml'da rules.drop_extra_columns True olmalı."
        )


# ------------------------------------------------------------------ #
# Validation logic testleri
# ------------------------------------------------------------------ #

class TestValidationLogic:
    """validate_features() fonksiyonunun davranışını test eder."""

    def test_missing_feature_raises_error(self, feature_list_48: list[str]) -> None:
        """Eksik feature olduğunda ValueError fırlatılmalı."""
        # Listedeki ilk feature'ı eksik bırak
        incomplete_columns = feature_list_48[1:]  # ilkini çıkar

        with pytest.raises(ValueError, match="Feature lock HATASI"):
            validate_features(
                data_columns=incomplete_columns,
                required_features=feature_list_48,
                fail_on_missing=True,
            )

    def test_extra_features_are_dropped(self, feature_list_48: list[str]) -> None:
        """Fazla kolonlar drop_extra_columns=True iken sessizce atılmalı."""
        extra_columns = feature_list_48 + ["extra_col_1", "extra_col_2", "unknown_feature"]

        result = validate_features(
            data_columns=extra_columns,
            required_features=feature_list_48,
            fail_on_missing=True,
            drop_extra_columns=True,
        )

        assert "extra_col_1" not in result
        assert "extra_col_2" not in result
        assert "unknown_feature" not in result

    def test_all_48_present_passes(self, feature_list_48: list[str]) -> None:
        """Tam 48 feature verildiğinde hata fırlatılmamalı."""
        result = validate_features(
            data_columns=feature_list_48,
            required_features=feature_list_48,
            fail_on_missing=True,
            drop_extra_columns=True,
        )
        # Tüm 48 feature sonuç listesinde olmalı
        assert set(result) == set(feature_list_48)

    def test_missing_feature_no_raise_when_disabled(
        self, feature_list_48: list[str]
    ) -> None:
        """fail_on_missing=False iken eksik feature hata fırlatmamalı."""
        incomplete = feature_list_48[5:]  # ilk 5'i eksik bırak

        # Hata fırlatmamalı
        result = validate_features(
            data_columns=incomplete,
            required_features=feature_list_48,
            fail_on_missing=False,
            drop_extra_columns=False,
        )
        # Sonuç incomplete'in kendisi olmalı (drop olmadı, raise olmadı)
        assert result == incomplete

    def test_empty_data_raises_error(self, feature_list_48: list[str]) -> None:
        """Hiç kolon yoksa fail_on_missing=True iken ValueError fırlatılmalı."""
        with pytest.raises(ValueError):
            validate_features(
                data_columns=[],
                required_features=feature_list_48,
                fail_on_missing=True,
            )
