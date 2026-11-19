import copy
import numpy as np
from quantagent.backtest.costs import net_trade_return, per_side_cost
from quantagent.backtest.portfolio import backtest
from quantagent.backtest.walk_forward import walk_forward_predict


def test_random_model_pays_costs(df, prices, cfg):
    bt = backtest(walk_forward_predict(df, "random", cfg), prices, cfg)
    assert np.allclose(bt["gross"] - bt["net"], per_side_cost(cfg) * bt["turnover"])
    assert bt["net"].mean() < bt["gross"].mean()


def test_zero_cost_net_equals_gross(df, prices, cfg):
    c0 = copy.deepcopy(cfg); c0["costs"] = {"fee_bps": 0, "slippage_bps": 0}
    bt = backtest(walk_forward_predict(df, "random", c0), prices, c0)
    assert np.allclose(bt["gross"], bt["net"])


def test_net_trade_return_flat_price_loses_costs():
    r = net_trade_return(100, 100, fee_bps=5, slippage_bps=5)
    assert -0.0025 < r < -0.0019