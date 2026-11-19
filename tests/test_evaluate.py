import numpy as np
import pandas as pd
from quantagent.pipeline.evaluate import ic_wide, rolling_ic, summarize


def _scored(n_dates, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2026-01-01", periods=n_dates)
    rows = []
    for dt in dates:
        y = rng.permutation(30) / 29 - 0.5
        for i in range(30):
            rows.append(("good", dt, f"T{i}", 0.3 * y[i] + rng.normal(0, 0.3), y[i]))
            rows.append(("random", dt, f"T{i}", rng.normal(), y[i]))
    return pd.DataFrame(rows, columns=["model", "date", "ticker", "score", "realized_rank"])


def test_too_few_dates_concludes_nothing():
    s = summarize(ic_wide(_scored(10)), min_dates=30)
    assert (s["status"] == "insufficient_sample").all()


def test_signal_is_detected_and_noise_is_not():
    s = summarize(ic_wide(_scored(150)), min_dates=30, n_boot=500)
    assert s.loc["good", "status"] == "positive_signal"
    assert s.loc["random", "status"] == "no_detectable_edge"
    assert s.loc["good", "ic_mean"] > 0.1


def test_rolling_ic_needs_full_window():
    r = rolling_ic(ic_wide(_scored(80)), window=60)
    assert len(r) == 80 - 60 + 1