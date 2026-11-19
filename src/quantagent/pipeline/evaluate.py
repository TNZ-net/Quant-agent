import numpy as np
import pandas as pd
from ..metrics.bootstrap import block_bootstrap_ci
from ..metrics.prediction import ic_by_date

SCORED_SQL = """SELECT mv.name AS model, p.signal_date AS date, p.ticker, p.score, o.realized_rank, o.fwd_ret
  FROM predictions p JOIN model_versions mv ON mv.id = p.model_version_id
  JOIN outcomes o ON o.prediction_id = p.id"""

COUNTS_SQL = """SELECT mv.name AS model, count(*) AS predictions, count(o.prediction_id) AS scored,
  count(DISTINCT p.signal_date) AS dates FROM predictions p
  JOIN model_versions mv ON mv.id = p.model_version_id
  LEFT JOIN outcomes o ON o.prediction_id = p.id GROUP BY mv.name ORDER BY mv.name"""


def load_scored(engine=None) -> pd.DataFrame:
    from sqlalchemy import text
    from ..db import get_engine
    return pd.read_sql(text(SCORED_SQL), engine or get_engine(), parse_dates=["date"])


def ledger_counts(engine=None) -> pd.DataFrame:
    from sqlalchemy import text
    from ..db import get_engine
    return pd.read_sql(text(COUNTS_SQL), engine or get_engine())


def recent_anchors(engine=None, n=10) -> pd.DataFrame:
    from sqlalchemy import text
    from ..db import get_engine
    return pd.read_sql(text("SELECT day, n_leaves, merkle_root FROM anchors ORDER BY day DESC LIMIT :n"),
                       engine or get_engine(), params={"n": n})


def ledger_integrity(engine=None) -> tuple[int, int]:
    """Recompute every stored hash. Returns (rows checked, mismatches)."""
    from sqlalchemy import text
    from ..db import get_engine
    from ..ledger.commit import verify_row
    with (engine or get_engine()).connect() as c:
        rows = c.execute(text("SELECT * FROM predictions")).mappings().all()
    return len(rows), sum(not verify_row(dict(r)) for r in rows)


def ic_wide(d: pd.DataFrame) -> pd.DataFrame:
    """Daily IC per model: one row per signal date, one column per model."""
    cols = {}
    for name, g in d.groupby("model"):
        g = g.set_index(["date", "ticker"])
        cols[name] = ic_by_date(g["score"], g["realized_rank"])
    return pd.DataFrame(cols).sort_index()


def summarize(wide: pd.DataFrame, min_dates=30, block=10, n_boot=2000, window=60) -> pd.DataFrame:
    rows = {}
    for m in wide.columns:
        s = wide[m].dropna(); n = len(s)
        lo, hi = block_bootstrap_ci(s.values, np.mean, block, n_boot)
        status = ("insufficient_sample" if n < min_dates
                  else "positive_signal" if lo > 0 else "no_detectable_edge")
        rows[m] = dict(n_dates=n, ic_mean=float(s.mean()) if n else np.nan, ci_low=lo, ci_high=hi,
                       recent_ic=float(s.tail(window).mean()) if n else np.nan, status=status)
    return pd.DataFrame(rows).T


def rolling_ic(wide: pd.DataFrame, window=60) -> pd.DataFrame:
    return wide.rolling(window, min_periods=window).mean().dropna(how="all")