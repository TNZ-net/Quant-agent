import numpy as np
import pandas as pd


def sharpe(r, periods_per_year) -> float:
    r = pd.Series(r).dropna(); sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(periods_per_year)) if sd and sd > 0 else float("nan")


def max_drawdown(r) -> float:
    eq = (1 + pd.Series(r).dropna()).cumprod()
    return float((eq / eq.cummax() - 1).min())


def summary(r, periods_per_year) -> dict:
    r = pd.Series(r).dropna()
    eq = (1 + r).cumprod(); years = len(r) / periods_per_year
    return dict(n_periods=int(len(r)), total_return=float(eq.iloc[-1] - 1),
                ann_return=float(eq.iloc[-1] ** (1 / years) - 1) if years > 0 else float("nan"),
                ann_vol=float(r.std(ddof=1) * np.sqrt(periods_per_year)),
                sharpe=sharpe(r, periods_per_year), max_drawdown=max_drawdown(r))