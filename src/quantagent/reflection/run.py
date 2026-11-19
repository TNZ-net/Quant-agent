import argparse, json
from ..config import load_config
from ..pipeline.evaluate import ic_wide, load_scored, summarize
from . import core


def _stub(prompt: str, system: str) -> str:
    return "1. Placeholder hypothesis for a dry run. Check: re-run with real data and compare intervals."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="stub LLM, do not store")
    ap.add_argument("--plain", action="store_true", help="use the plain driver instead of LangGraph")
    a = ap.parse_args()
    cfg = load_config(); mon = cfg["monitor"]
    scored = load_scored()
    if scored.empty:
        facts = dict(n_dates=0, models={}, worst_misses=[])
    else:
        summ = summarize(ic_wide(scored), mon["min_dates"], cfg["bootstrap"]["block_size"], cfg["bootstrap"]["n_boot"])
        facts = core.build_facts(summ, core.worst_misses(scored, cfg["model"]["live"]))
    if a.dry_run:
        llm, model_name = _stub, "stub"
    else:
        from .ollama_client import chat, pick_model
        model_name = pick_model()
        llm = lambda p, s: chat(p, s, model=model_name)
    if a.plain:
        state = core.reflect(facts, llm, mon["min_dates"])
    else:
        from .graph import build_graph
        state = build_graph(llm).invoke({"facts": facts, "min_dates": mon["min_dates"], "max_attempts": 2})
    print(state["final"])
    if not a.dry_run:
        from sqlalchemy import text
        from ..db import get_engine
        with get_engine().begin() as c:
            c.execute(text("INSERT INTO reflections (stats, content, llm_model) VALUES (CAST(:s AS jsonb), :c, :m)"),
                      {"s": json.dumps(facts), "c": state["final"], "m": model_name if state.get("llm_used") else None})
        print("stored in reflections")


if __name__ == "__main__":
    main()