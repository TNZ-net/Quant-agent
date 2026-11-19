import pandas as pd
from .costs import per_side_cost


def backtest(scores: pd.Series, prices: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    h, k = cfg["horizon_days"], cfg["portfolio"]["top_k"]
    weighting, c = cfg["portfolio"]["weighting"], per_side_cost(cfg)
    p = prices.copy(); p["date"] = pd.to_datetime(p["date"])
    opn = p.pivot(index="date", columns="ticker", values="open").sort_index()
    close = p.pivot(index="date", columns="ticker", values="close").sort_index()
    vol = close.pct_change(fill_method=None).rolling(21).std()
    dates = opn.index
    score_dates = scores.index.get_level_values("date").unique().sort_values()
    prev_w, rows = pd.Series(dtype=float), []
    for t in score_dates[::cfg["portfolio"]["rebalance_every"]]:
        i = dates.get_loc(t)
        if i + 1 + h >= len(dates):
            break
        entry, exit_ = opn.iloc[i + 1], opn.iloc[i + 1 + h]
        ok = entry.notna() & exit_.notna()
        s = scores.xs(t, level="date").dropna()
        s = s[s.index.isin(ok[ok].index)]
        if len(s) < k:
            continue
        top = s.nlargest(k).index
        w = pd.Series(1.0, index=top)
        if weighting == "inverse_vol":
            v = vol.loc[t, top]
            if v.notna().all() and (v > 0).all():
                w = 1 / v
        w = w / w.sum()
        gross = float((w * (exit_ / entry - 1)[top]).sum())
        idx = w.index.union(prev_w.index)
        turnover = float((w.reindex(idx, fill_value=0) - prev_w.reindex(idx, fill_value=0)).abs().sum())
        bench = float((exit_ / entry - 1)[ok[ok].index].mean())
        rows.append(dict(date=t, gross=gross, turnover=turnover, cost=turnover * c,
                         net=gross - turnover * c, benchmark=bench))
        prev_w = w
    return pd.DataFrame(rows).set_index("date")