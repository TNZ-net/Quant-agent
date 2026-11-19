import numpy as np
import pandas as pd

COLUMNS = ["ticker", "date", "open", "high", "low", "close", "volume"]


class SyntheticSource:
    """edge=0: pure random walk. edge>0: slowly varying stock-specific drift (the only learnable signal)."""
    def __init__(self, n_days=1500, seed=7, edge=0.0, end="2026-11-06"):
        self.n_days, self.seed, self.edge, self.end = n_days, seed, edge, end

    def daily_bars(self, tickers, start=None, end=None):
        rng = np.random.default_rng(self.seed)
        n, k = self.n_days, len(tickers)
        dates = pd.bdate_range(end=self.end, periods=n)
        mkt = rng.normal(0.0003, 0.01, n)
        alpha = np.zeros((n, k)); sd = self.edge * 0.0005
        for t in range(1, n):
            alpha[t] = 0.98 * alpha[t - 1] + rng.normal(0, sd * np.sqrt(1 - 0.98 ** 2), k)
        ret = mkt[:, None] * rng.uniform(0.7, 1.3, k) + alpha + rng.normal(0, 0.012, (n, k))
        close = 100 * np.exp(np.cumsum(ret, axis=0))
        opn = np.vstack([close[:1], close[:-1]]) * (1 + rng.normal(0, 0.002, (n, k)))
        high, low = np.maximum(opn, close) * 1.005, np.minimum(opn, close) * 0.995
        vol = rng.lognormal(15, 0.3, (n, k))
        out = [pd.DataFrame({"ticker": tk, "date": dates, "open": opn[:, j], "high": high[:, j],
                             "low": low[:, j], "close": close[:, j], "volume": vol[:, j]})
               for j, tk in enumerate(tickers)]
        return pd.concat(out, ignore_index=True)[COLUMNS]