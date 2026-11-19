import numpy as np
import pandas as pd


def ic_by_date(pred: pd.Series, realized: pd.Series) -> pd.Series:
    d = pd.DataFrame({"p": pred, "y": realized}).dropna()
    d["p"] = d.groupby(level="date")["p"].rank()
    d["y"] = d.groupby(level="date")["y"].rank()
    return d.groupby(level="date").apply(lambda g: g["p"].corr(g["y"]))


def brier(p, y) -> float:
    p, y = np.asarray(p, float), np.asarray(y, float)
    return float(np.mean((p - y) ** 2))


def log_loss(p, y, eps=1e-12) -> float:
    p, y = np.clip(np.asarray(p, float), eps, 1 - eps), np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def calibration_table(p, y, bins=10) -> pd.DataFrame:
    d = pd.DataFrame({"p": p, "y": y})
    d["bucket"] = pd.cut(d["p"], np.linspace(0, 1, bins + 1), include_lowest=True)
    return d.groupby("bucket", observed=True).agg(n=("y", "size"), mean_pred=("p", "mean"), hit_rate=("y", "mean"))