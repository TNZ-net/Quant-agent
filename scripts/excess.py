import numpy as np
import pandas as pd
from quantagent.metrics.bootstrap import block_bootstrap_ci

eq = pd.read_csv("reports/equity_live.csv", index_col=0)
prev = eq.shift(1); prev.iloc[0] = 1.0
r = eq / prev - 1
bench = r["buy_and_hold_equal_weight"]
for m in r.columns.drop("buy_and_hold_equal_weight"):
    active = (r[m] - bench).dropna()
    lo, hi = block_bootstrap_ci(active.values, np.mean, block=2, n_boot=2000)
    ppy = 252 / 5
    print(f"{m:<10} excess/yr {active.mean()*ppy:>7.1%}   95% CI [{lo*ppy:.1%}, {hi*ppy:.1%}]")