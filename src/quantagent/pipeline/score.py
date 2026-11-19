import pandas as pd
from sqlalchemy import text
from ..config import load_config
from ..db import get_engine, load_prices
from ..features.build import build_features


def run_score(engine=None, cfg=None) -> int:
    engine, cfg = engine or get_engine(), cfg or load_config()
    df = build_features(load_prices(engine), cfg["horizon_days"])
    known = df[["fwd_ret", "target"]].dropna().reset_index()
    pend = pd.read_sql(text("""SELECT p.id, p.ticker, p.signal_date FROM predictions p
        LEFT JOIN outcomes o ON o.prediction_id = p.id WHERE o.prediction_id IS NULL"""),
        engine, parse_dates=["signal_date"])
    m = pend.merge(known, left_on=["signal_date", "ticker"], right_on=["date", "ticker"])
    if m.empty:
        return 0
    with engine.begin() as c:
        c.execute(text("""INSERT INTO outcomes (prediction_id, fwd_ret, realized_rank) VALUES (:i,:f,:r)
                          ON CONFLICT DO NOTHING"""),
                  [dict(i=int(r.id), f=float(r.fwd_ret), r=float(r.target)) for r in m.itertuples()])
    return len(m)