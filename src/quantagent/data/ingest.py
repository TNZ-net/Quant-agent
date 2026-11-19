import pandas as pd
from sqlalchemy import text

UPSERT = text("""
INSERT INTO prices (ticker, date, open, high, low, close, volume)
VALUES (:ticker, :date, :open, :high, :low, :close, :volume)
ON CONFLICT (ticker, date) DO UPDATE SET open=EXCLUDED.open, high=EXCLUDED.high,
  low=EXCLUDED.low, close=EXCLUDED.close, volume=EXCLUDED.volume""")


def report_gaps(prices: pd.DataFrame) -> pd.DataFrame:
    counts = prices.groupby("ticker")["date"].nunique()
    return (prices["date"].nunique() - counts).rename("missing_days").loc[lambda s: s > 0].to_frame()


def run_ingest(engine, cfg, source, lookback_days=10) -> int:
    """Idempotent: re-running never duplicates; recent bars are refreshed to pick up adjustments."""
    with engine.connect() as c:
        last = c.execute(text("SELECT max(date) FROM prices")).scalar()
    start = (pd.Timestamp(last) - pd.Timedelta(days=lookback_days)) if last else \
        (pd.Timestamp.today() - pd.DateOffset(years=cfg["history_years"]))
    df = source.daily_bars(cfg["universe"], start.strftime("%Y-%m-%d"), pd.Timestamp.today().strftime("%Y-%m-%d"))
    df["date"] = pd.to_datetime(df["date"]).dt.date
    with engine.begin() as c:
        c.execute(UPSERT, df.to_dict("records"))
    gaps = report_gaps(df.assign(date=pd.to_datetime(df["date"])))
    if len(gaps):
        print("WARNING gaps:\n", gaps)
    return len(df)
