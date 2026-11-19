import numpy as np
import pandas as pd

FEATURE_COLS = ["mom_12_1", "rev_5", "rev_21", "vol_21", "volchg", "dist_ma50", "rsi_14"]


def _rsi(close, n=14):
    d = close.diff()
    up = d.clip(lower=0).rolling(n).mean()
    dn = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def _long(wide: pd.DataFrame, name: str) -> pd.Series:
    w = wide.copy(); w.index.name = "date"; w.columns.name = "ticker"
    return w.reset_index().melt(id_vars="date", value_name=name).set_index(["date", "ticker"])[name]


def build_features(prices: pd.DataFrame, horizon: int) -> pd.DataFrame:
    p = prices.copy(); p["date"] = pd.to_datetime(p["date"])
    piv = lambda col: p.pivot(index="date", columns="ticker", values=col).sort_index()
    close, opn, vol = piv("close"), piv("open"), piv("volume")
    ret1 = close.pct_change(fill_method=None)
    raw = {
        "mom_12_1": close.shift(21) / close.shift(252) - 1,   # 12-month momentum, skipping last month
        "rev_5": close / close.shift(5) - 1,
        "rev_21": close / close.shift(21) - 1,
        "vol_21": ret1.rolling(21).std(),
        "volchg": vol.rolling(5).mean() / vol.rolling(60).mean() - 1,
        "dist_ma50": close / close.rolling(50).mean() - 1,
        "rsi_14": _rsi(close),
    }
    X = pd.concat([_long(v, k) for k, v in raw.items()], axis=1)
    X = X.replace([np.inf, -np.inf], np.nan).dropna(subset=["mom_12_1"])
    X[FEATURE_COLS] = X.groupby(level="date")[FEATURE_COLS].rank(pct=True) - 0.5
    fwd = opn.shift(-(horizon + 1)) / opn.shift(-1) - 1
    X["fwd_ret"] = _long(fwd, "fwd_ret").reindex(X.index)
    X["target"] = X.groupby(level="date")["fwd_ret"].rank(pct=True) - 0.5
    return X.sort_index()