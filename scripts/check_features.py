from quantagent.config import load_config
from quantagent.data.synthetic import SyntheticSource
from quantagent.features.build import build_features

cfg = load_config()
prices = SyntheticSource().daily_bars(cfg["universe"])
df = build_features(prices, 5)
print(df.shape)
print(df.tail(3))