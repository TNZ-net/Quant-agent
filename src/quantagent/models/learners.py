import pandas as pd
from sklearn.linear_model import Ridge
from ..features.build import FEATURE_COLS
from . import baselines


def _by_date_rank(s: pd.Series) -> pd.Series:
    return s.groupby(level="date").rank(pct=True)


def fit_predict(name: str, train: pd.DataFrame, test: pd.DataFrame, cfg: dict, seed=0) -> pd.Series:
    if name == "momentum":
        return baselines.momentum(test)
    if name == "random":
        return baselines.random_scores(test, seed)
    if name == "ensemble":
        r = _by_date_rank(fit_predict("ridge", train, test, cfg, seed))
        g = _by_date_rank(fit_predict("lgbm", train, test, cfg, seed))
        return (r + g) / 2
    Xtr, ytr = train[FEATURE_COLS].fillna(0).to_numpy(), train["target"].to_numpy()
    Xte = test[FEATURE_COLS].fillna(0).to_numpy()
    if name == "ridge":
        model = Ridge(alpha=cfg["model"]["ridge_alpha"])
    elif name == "lgbm":
        import lightgbm as lgb
        model = lgb.LGBMRegressor(**cfg["model"]["lgbm"], random_state=seed, verbose=-1)
    else:
        raise ValueError(name)
    return pd.Series(model.fit(Xtr, ytr).predict(Xte), index=test.index)