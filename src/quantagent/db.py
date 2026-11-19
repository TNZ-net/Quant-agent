import os
import pandas as pd
from sqlalchemy import create_engine, text
from . import config  # noqa: F401  (importing config loads .env)


def get_engine():
    url = os.getenv("DATABASE_URL", "postgresql+psycopg://quant:quant@localhost:5432/quant")
    return create_engine(url, future=True)


def load_prices(engine) -> pd.DataFrame:
    return pd.read_sql(
        text("SELECT ticker, date, open, high, low, close, volume FROM prices ORDER BY date"),
        engine, parse_dates=["date"])