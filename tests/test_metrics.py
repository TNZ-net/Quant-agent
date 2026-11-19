import numpy as np
import pandas as pd
from quantagent.metrics.bootstrap import block_bootstrap_ci
from quantagent.metrics.prediction import brier, ic_by_date
from quantagent.metrics.trading import max_drawdown, sharpe


def test_brier_constant_half():
    assert brier([0.5] * 10, [1, 0] * 5) == 0.25


def test_sharpe_hand_calc():
    r = [0.02, 0.0, 0.02, 0.0]
    assert abs(sharpe(r, 252) - 0.01 / np.std(r, ddof=1) * np.sqrt(252)) < 1e-9


def test_max_drawdown():
    assert abs(max_drawdown([0.1, -0.5, 0.2]) - (-0.5)) < 1e-9


def test_perfect_ic():
    idx = pd.MultiIndex.from_product([pd.date_range("2024-01-01", periods=3), list("abcde")], names=["date", "ticker"])
    y = pd.Series(np.tile(np.arange(5), 3), index=idx, dtype=float)
    assert np.allclose(ic_by_date(y, y), 1.0)


def test_bootstrap_ci_contains_mean_of_noise():
    x = np.random.default_rng(0).normal(0, 1, 500)
    lo, hi = block_bootstrap_ci(x, np.mean, block=5, n_boot=500)
    assert lo < 0.0 < hi