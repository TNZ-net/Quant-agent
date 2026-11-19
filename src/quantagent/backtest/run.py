import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from ..config import load_config
from ..features.build import build_features
from ..metrics.bootstrap import block_bootstrap_ci
from ..metrics.prediction import ic_by_date
from ..metrics.trading import sharpe, summary
from .portfolio import backtest
from .walk_forward import walk_forward_predict


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--edge", type=float, default=0.0)
    ap.add_argument("--shuffle-labels", action="store_true")
    ap.add_argument("--models", nargs="+", default=["random", "momentum", "ridge", "lgbm", "ensemble"])
    ap.add_argument("--out", default="reports")
    a = ap.parse_args(argv)
    cfg = load_config(); h = cfg["horizon_days"]
    if a.synthetic:
        from ..data.synthetic import SyntheticSource
        prices = SyntheticSource(n_days=1500, edge=a.edge).daily_bars(cfg["universe"])
    else:
        from ..db import get_engine, load_prices
        prices = load_prices(get_engine())
    df = build_features(prices, h)
    ppy = 252 / cfg["portfolio"]["rebalance_every"]
    bs = cfg["bootstrap"]; res, curves, bench = {}, {}, None
    for name in a.models:
        preds = walk_forward_predict(df, name, cfg, shuffle_labels=a.shuffle_labels)
        ic = ic_by_date(preds, df["target"]).dropna()
        bt = backtest(preds, prices, cfg)
        ic_lo, ic_hi = block_bootstrap_ci(ic.values, np.mean, bs["block_size"], bs["n_boot"])
        sh_lo, sh_hi = block_bootstrap_ci(bt["net"].values, lambda x: sharpe(x, ppy), 2, bs["n_boot"])
        res[name] = dict(ic_mean=float(ic.mean()), ic_ci95=[ic_lo, ic_hi], icir=float(ic.mean() / ic.std()),
                         n_ic_dates=int(len(ic)), avg_turnover=float(bt["turnover"].mean()),
                         gross=summary(bt["gross"], ppy), net=summary(bt["net"], ppy),
                         sharpe_net_ci95=[sh_lo, sh_hi])
        curves[name] = (1 + bt["net"]).cumprod()
        bench = bt["benchmark"] if bench is None else bench
    res["buy_and_hold_equal_weight"] = dict(gross=summary(bench, ppy))
    curves["buy_and_hold_equal_weight"] = (1 + bench).cumprod()
    out = Path(a.out); out.mkdir(exist_ok=True)
    tag = "synthetic" if a.synthetic else "live"
    (out / f"backtest_{tag}.json").write_text(json.dumps(res, indent=2, default=float))
    pd.DataFrame(curves).to_csv(out / f"equity_{tag}.csv")
    print(f"{'model':<12}{'IC':>8}{'IC 95% CI':>20}{'net Sharpe':>12}{'net total':>11}{'turnover':>10}")
    for n, r in res.items():
        if "ic_mean" in r:
            print(f"{n:<12}{r['ic_mean']:>8.4f}{str([round(x, 4) for x in r['ic_ci95']]):>20}"
                  f"{r['net']['sharpe']:>12.2f}{r['net']['total_return']:>11.1%}{r['avg_turnover']:>10.2f}")
        else:
            g = r["gross"]; print(f"{n:<12}{'':>8}{'':>20}{g['sharpe']:>12.2f}{g['total_return']:>11.1%}")


if __name__ == "__main__":
    main()