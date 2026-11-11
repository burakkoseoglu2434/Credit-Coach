"""Risk_Score scale check: monthly score distribution in the rejected file vs fico_range_low in
the accepted file. Observation only: no mapping is changed and nothing is inferred.

Rejected months are the month of 'Application Date'. The accepted file has no application date;
its month is the month of 'issue_d' (the loan issue month), which is a different event.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

FICO_UPPER = 850.0  # upper end of the fico_range_high support (configs/support.yaml)
NULL_SHARE = 50.0  # percent, for the "mostly empty" observation


@dataclass(frozen=True)
class MonthStat:
    ay: str
    n: int
    bos_yuzde: float
    min: float | None
    medyan: float | None
    maks: float | None


_AGG = (
    "count(*) as n, round(100.0 * count(*) filter (where s is null) / count(*), 1) as nul, "
    "min(s), median(s), max(s)"
)


def _rows(con, view: str) -> list[MonthStat]:
    cur = con.execute(f"select m, {_AGG} from {view} group by m order by m")
    return [MonthStat(*r) for r in cur.fetchall()]


def monthly(rejected: Path, accepted: Path) -> dict[str, list[MonthStat]]:
    con = duckdb.connect()
    con.execute(
        'create view rj as select substr("Application Date", 1, 7) as m, '
        f"try_cast(Risk_Score as double) as s from read_csv('{rejected}', header=true, "
        "all_varchar=true)"
    )
    con.execute(
        "create view ac as select strftime(strptime(issue_d, '%b-%Y'), '%Y-%m') as m, "
        f"try_cast(fico_range_low as double) as s from read_csv('{accepted}', header=true, "
        "all_varchar=true, ignore_errors=true) where issue_d is not null"
    )
    return {"reddedilen": _rows(con, "rj"), "kabul": _rows(con, "ac")}


def observations(rows: list[MonthStat]) -> dict:
    """Plain facts about the monthly series (thresholds are stated in the report)."""
    above = [r.ay for r in rows if r.maks is not None and r.maks > FICO_UPPER]
    zero = [r.ay for r in rows if r.min is not None and r.min == 0]
    empty = [r.ay for r in rows if r.bos_yuzde > NULL_SHARE]
    out = {
        "ay_sayisi": len(rows),
        "maks_850_ustu": (above[0], above[-1], len(above)) if above else None,
        "min_sifir": (zero[0], zero[-1], len(zero)) if zero else None,
        "bos_50_ustu": (empty[0], empty[-1], len(empty)) if empty else None,
        "genel_min": min((r.min for r in rows if r.min is not None), default=None),
        "genel_maks": max((r.maks for r in rows if r.maks is not None), default=None),
    }
    return out


def archive_documents(folder: Path) -> list[str]:
    """Entries of the archive folder that are not one of the data files."""
    return sorted(
        p.name
        for p in folder.iterdir()
        if not p.name.startswith(".")
        and not p.name.lower().startswith(("rejected_2007", "accepted_2007"))
    )
