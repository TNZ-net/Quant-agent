import json
from pathlib import Path
import pandas as pd
import streamlit as st
from quantagent.config import load_config
from quantagent.pipeline.evaluate import (ic_wide, ledger_counts, ledger_integrity, load_scored,
                                          recent_anchors, rolling_ic, summarize)

st.set_page_config(page_title="quantagent", layout="wide")
st.title("quantagent: live track record")
st.caption("Daily cross-sectional ranking of 30 US stocks. Every prediction is hash-committed before the "
           "outcome exists. Skill is judged by rank IC, not by portfolio return.")
cfg = load_config()

# 1. Ledger -----------------------------------------------------------------
st.header("1. Ledger")
try:
    counts = ledger_counts()
    checked, bad = ledger_integrity()
    c1, c2, c3 = st.columns(3)
    c1.metric("Predictions logged", int(counts["predictions"].sum()))
    c2.metric("Scored", int(counts["scored"].sum()))
    c3.metric("Hash mismatches", bad, help=f"{checked} rows recomputed from stored columns")
    st.dataframe(counts, hide_index=True)
    st.subheader("Daily anchors")
    st.caption("Merkle root of each day's hashes. Compare against the copies published in the public repo.")
    st.dataframe(recent_anchors(), hide_index=True)
except Exception as e:
    st.info(f"Database not available: {e}")
    st.stop()

# 2. Live skill -------------------------------------------------------------
st.header("2. Live skill (rank IC)")
scored = load_scored()
if scored.empty:
    st.warning("No scored predictions yet. The first outcomes appear about 6 trading days after the first log.")
else:
    wide = ic_wide(scored)
    mon = cfg["monitor"]
    tbl = summarize(wide, mon["min_dates"], cfg["bootstrap"]["block_size"], cfg["bootstrap"]["n_boot"],
                    mon["window_dates"])
    n = int(tbl["n_dates"].max())
    if n < mon["min_dates"]:
        st.warning(f"Only {n} scored dates. Nothing here is a conclusion yet; "
                   f"statuses stay 'insufficient_sample' below {mon['min_dates']}.")
    st.dataframe(tbl.style.format({"ic_mean": "{:+.4f}", "ci_low": "{:+.4f}", "ci_high": "{:+.4f}",
                                   "recent_ic": "{:+.4f}"}))
    st.caption("95% block-bootstrap interval. The 'random' model is a sanity check: if it ever shows "
               "positive_signal, suspect the measurement, not the market.")
    window = st.slider("Rolling window (dates)", 10, 120, mon["window_dates"])
    roll = rolling_ic(wide, window)
    if roll.empty:
        st.info(f"Need at least {window} scored dates for a rolling chart.")
    else:
        st.line_chart(roll)

# 3. Backtest ---------------------------------------------------------------
st.header("3. Walk-forward backtest (real data)")
f = Path("reports/backtest_live.json")
if not f.exists():
    st.info("Run `python -m quantagent.backtest.run` to create reports/backtest_live.json.")
else:
    res = json.loads(f.read_text())
    rows = {}
    for k, v in res.items():
        net = v.get("net") or v["gross"]
        rows[k] = {"IC": v.get("ic_mean"),
                   "IC low": v["ic_ci95"][0] if "ic_ci95" in v else None,
                   "IC high": v["ic_ci95"][1] if "ic_ci95" in v else None,
                   "net Sharpe": net["sharpe"], "net return": net["total_return"],
                   "max drawdown": net["max_drawdown"]}
    st.dataframe(pd.DataFrame(rows).T)
    eq = Path("reports/equity_live.csv")
    if eq.exists():
        st.line_chart(pd.read_csv(eq, index_col=0, parse_dates=True))
    st.caption("Result: no model showed a detectable edge over buy-and-hold (all excess-return intervals span "
               "zero). The universe is today's large caps, so returns carry survivorship bias. "
               "The random model earning about the benchmark shows how much of the return is just the market.")