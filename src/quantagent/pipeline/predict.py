import json
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import text
from ..config import load_config
from ..db import get_engine, load_prices
from ..features.build import FEATURE_COLS, build_features
from ..ledger.commit import build_payload, commit_hash
from ..models.learners import fit_predict
from ..models.registry import get_or_create_version, model_hash
from .sessions import last_completed_session

INSERT = text("""INSERT INTO predictions (ticker, signal_date, horizon_days, score, model_version_id, config_hash,
  features, created_at, commit_hash) VALUES (:ticker,:signal_date,:horizon_days,:score,:mv,:ch,
  CAST(:features AS jsonb),:created_at,:commit_hash)
  ON CONFLICT (ticker, signal_date, horizon_days, model_version_id) DO NOTHING""")


def run_predict(engine=None, cfg=None, models=None) -> dict:
    engine, cfg = engine or get_engine(), cfg or load_config()
    h, wf = cfg["horizon_days"], cfg["walk_forward"]
    gap = h + 1 + cfg["embargo_days"]
    prices = load_prices(engine)
    prices = prices[prices["date"] <= last_completed_session()]       # never score a partial bar
    df = build_features(prices, h)
    dates = df.index.get_level_values("date").unique().sort_values()
    last = dates[-1]
    age = (pd.Timestamp.today().normalize() - last).days
    if age > cfg["ledger"]["max_stale_days"]:
        raise RuntimeError(f"latest bar is {last.date()} ({age} days old). Ingest first; "
                           "never log predictions retroactively.")
    d = df.index.get_level_values("date")
    train_dates = dates[:-(gap + 1)]                  # same gap the purged backtest leaves
    if not wf.get("expanding", False):
        train_dates = train_dates[-wf["train_days"]:]
    train = df[d.isin(train_dates)]; train = train[train["target"].notna()]
    test = df[d == last]
    created = datetime.now(timezone.utc).replace(microsecond=0)
    seed, mh, rows, per_model = int(last.strftime("%Y%m%d")), model_hash(cfg), [], {}
    for name in (models or cfg["live_models"]):
        scores = fit_predict(name, train, test, cfg, seed).dropna()
        mv = get_or_create_version(engine, name, cfg)
        for (dt, tk), sc in scores.items():
            feats = {c: (None if pd.isna(v) else round(float(v), 6))
                     for c, v in test.loc[(dt, tk), FEATURE_COLS].items()}
            payload = build_payload(tk, dt.date(), h, sc, mv, mh, feats, created)
            rows.append(dict(ticker=tk, signal_date=dt.date(), horizon_days=h, score=float(sc), mv=mv, ch=mh,
                             features=json.dumps(feats), created_at=created, commit_hash=commit_hash(payload)))
        per_model[name] = len(scores)
    with engine.begin() as c:                         # all models in one transaction
        c.execute(INSERT, rows)
    return dict(signal_date=str(last.date()), rows=len(rows), per_model=per_model)