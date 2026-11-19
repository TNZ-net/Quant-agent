import numpy as np
import pandas as pd
from ..models.learners import fit_predict


def purged_splits(dates, train_days, test_days, step_days, gap, expanding=False):
    dates = list(dates); n = len(dates)
    start = train_days + gap
    while start < n:
        train_end = start - gap
        train_start = 0 if expanding else max(0, train_end - train_days)
        yield dates[train_start:train_end], dates[start:min(start + test_days, n)]
        start += step_days


def walk_forward_predict(df: pd.DataFrame, name: str, cfg: dict, shuffle_labels=False, seed=0) -> pd.Series:
    wf, h = cfg["walk_forward"], cfg["horizon_days"]
    gap = h + 1 + cfg["embargo_days"]
    d = df.index.get_level_values("date")
    dates = d.unique().sort_values()
    rng = np.random.default_rng(seed)
    out = []
    for tr, te in purged_splits(dates, wf["train_days"], wf["test_days"], wf["step_days"], gap, wf.get("expanding", False)):
        train = df[d.isin(tr)]; train = train[train["target"].notna()].copy()
        test = df[d.isin(te)]; test = test[test["target"].notna()]
        if shuffle_labels:
            train["target"] = train.groupby(level="date")["target"].transform(lambda s: rng.permutation(s.to_numpy()))
        if len(test):
            out.append(fit_predict(name, train, test, cfg, seed))
    s = pd.concat(out)
    return s[~s.index.duplicated(keep="last")]