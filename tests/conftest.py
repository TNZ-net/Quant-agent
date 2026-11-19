import pytest
from quantagent.config import load_config
from quantagent.data.synthetic import SyntheticSource
from quantagent.features.build import build_features


@pytest.fixture(scope="session")
def cfg():
    return load_config()


@pytest.fixture(scope="session")
def prices(cfg):
    return SyntheticSource(n_days=1100, seed=1).daily_bars(cfg["universe"])


@pytest.fixture(scope="session")
def df(prices, cfg):
    return build_features(prices, cfg["horizon_days"])