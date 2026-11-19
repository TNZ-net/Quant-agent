from quantagent.reflection import core
from quantagent.reflection.ollama_client import chat, pick_model

FACTS = dict(n_dates=45, models={
    "ensemble": dict(ic_mean=0.0123, ci_low=-0.0210, ci_high=0.0451, status="no_detectable_edge"),
    "momentum": dict(ic_mean=0.0404, ci_low=0.0002, ci_high=0.0806, status="positive_signal")},
    worst_misses=[dict(date="2026-12-01", ticker="US.NVDA", predicted_rank=0.4, realized_rank=-0.45)])

m = pick_model()
print("model:", m, "(test data, not real results)")
out = core.reflect(FACTS, lambda p, s: chat(p, s, model=m), min_dates=30)
print("attempts:", out["attempts"], "| issues left:", out["issues"])
print(out["final"])

print("--- last rejected draft ---")
print(out["draft"])