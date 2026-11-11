"""Delta sets and labels shared by the reports: the demo's default delta comes from the catalog
(configs/catalog/demo_v0.yaml, delta.deger) and is always one of the report columns."""

from __future__ import annotations

from credit_coach.recourse import Katalog

BAND_ETIKETI = "δ = 0 (band içi: etkin kesim eşik − band)"
EK_DELTA = 0.03  # the other fixed column besides 0 and the default


def fmt(d: float) -> str:
    """0.02 -> '0,02' (Turkish decimal comma)."""
    return f"{d:g}".replace(".", ",")


def report_deltas(kat: Katalog) -> tuple[float, ...]:
    """Band-inside (0), the catalog default and 0.03, sorted and unique."""
    return tuple(sorted({0.0, float(kat.delta), EK_DELTA}))


def delta_etiketi(d: float, kat: Katalog) -> str:
    """Column label; the demo default is marked."""
    taban = BAND_ETIKETI if d == 0.0 else f"δ = {fmt(d)}"
    return taban + (" (demo varsayılanı)" if d == float(kat.delta) else "")


def varsayilan_delta(kat: Katalog) -> str:
    """Text for report titles: 'demo varsayılan δ = 0,02'."""
    return f"demo varsayılan δ = {fmt(float(kat.delta))}"


def delta_notu(kat: Katalog) -> str:
    return (
        f"Demo varsayılan δ = {fmt(float(kat.delta))} "
        "(`configs/catalog/demo_v0.yaml`, `delta.deger`, varsayım); "
        "API ve arayüz bu değerle plan arar. Rapor sütunları: "
        + ", ".join(delta_etiketi(d, kat) for d in report_deltas(kat))
        + "."
    )
