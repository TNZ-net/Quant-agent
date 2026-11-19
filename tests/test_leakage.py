import pandas as pd
from quantagent.backtest.walk_forward import walk_forward_predict
from quantagent.features.build import FEATURE_COLS, build_features
from quantagent.metrics.prediction import ic_by_date


def test_features_ignore_future_prices(prices, df, cfg):
    cut = sorted(prices["date"].unique())[600]
    mut = prices.copy()
    m = mut["date"] > cut
    mut.loc[m, ["open", "high", "low", "close"]] *= 1.7
    mut.loc[m, "volume"] *= 5
    d2 = build_features(mut, cfg["horizon_days"])
    pick = lambda x: x[x.index.get_level_values("date") <= cut][FEATURE_COLS]
    pd.testing.assert_frame_equal(pick(df), pick(d2))


def test_shuffled_labels_give_zero_ic(df, cfg):
    preds = walk_forward_predict(df, "ridge", cfg, shuffle_labels=True)
    ic = ic_by_date(preds, df["target"]).dropna()
    assert abs(ic.mean()) < 0.03