import numpy as np
import pandas as pd


def momentum(test: pd.DataFrame) -> pd.Series:
    return test["mom_12_1"].copy()


def random_scores(test: pd.DataFrame, seed=0) -> pd.Series:
    return pd.Series(np.random.default_rng(seed).normal(size=len(test)), index=test.index)