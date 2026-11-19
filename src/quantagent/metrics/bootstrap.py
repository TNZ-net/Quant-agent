import numpy as np


def block_bootstrap_ci(x, stat=np.mean, block=10, n_boot=2000, alpha=0.05, seed=0):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x)
    if n < 2 * block:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n, size=(n_boot, int(np.ceil(n / block))))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % n
    samples = x[idx.reshape(n_boot, -1)[:, :n]]
    stats = np.apply_along_axis(stat, 1, samples)
    lo, hi = np.quantile(stats, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)