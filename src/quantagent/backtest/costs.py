def per_side_cost(cfg) -> float:
    return (cfg["costs"]["fee_bps"] + cfg["costs"]["slippage_bps"]) / 1e4


def net_trade_return(open_in, open_out, fee_bps, slippage_bps) -> float:
    s = slippage_bps / 1e4
    entry, exit_ = open_in * (1 + s), open_out * (1 - s)
    return exit_ / entry - 1 - 2 * fee_bps / 1e4