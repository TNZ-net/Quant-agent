import json, re
from typing import Callable, TypedDict
import pandas as pd

DISCLAIMER = ("Hypotheses to test, not findings. Many slices were possible, so apparent patterns may be "
              "noise. Not trading advice.")
SYSTEM = ("You are a cautious quantitative analyst. Use ONLY numbers that appear in FACTS, copied exactly. "
          "Write at most 3 numbered hypotheses. Each has one sentence of observation and one sentence naming "
          "a check that could be run. No trading advice. Do not state causes as facts.")
ADVICE = re.compile(r"\b(buy|sell|short|invest|you should)\b", re.I)
FORWARD = re.compile(r"\b(in the future|going forward|will (?:outperform|perform|beat|continue))\b", re.I)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
NUM = re.compile(r"-?\d+(?:\.\d+)?")


class State(TypedDict, total=False):
    facts: dict
    min_dates: int
    max_attempts: int
    skip: bool
    draft: str
    issues: list
    attempts: int
    final: str
    llm_used: bool


def worst_misses(d: pd.DataFrame, model: str, n=5) -> list[dict]:
    g = d[d["model"] == model].copy()
    if g.empty:
        return []
    g["pred_rank"] = g.groupby("date")["score"].rank(pct=True) - 0.5
    g["error"] = (g["pred_rank"] - g["realized_rank"]).abs()
    w = g.nlargest(n, "error")
    return [dict(date=str(r.date.date()), ticker=r.ticker, predicted_rank=round(float(r.pred_rank), 3),
                 realized_rank=round(float(r.realized_rank), 3)) for r in w.itertuples()]


def build_facts(summary: pd.DataFrame, misses: list[dict]) -> dict:
    models = {}
    for name, r in summary.iterrows():
        models[name] = dict(ic_mean=round(float(r["ic_mean"]), 4), ci_low=round(float(r["ci_low"]), 4),
                            ci_high=round(float(r["ci_high"]), 4), status=r["status"])
    n = int(summary["n_dates"].max()) if len(summary) else 0
    return dict(n_dates=n, models=models, worst_misses=misses)


def facts_text(facts: dict) -> str:
    lines = [f"Scored dates: {facts['n_dates']}."]
    for m, v in facts["models"].items():
        lines.append(f"{m}: IC {v['ic_mean']:+.4f}, 95% CI [{v['ci_low']:+.4f}, {v['ci_high']:+.4f}], {v['status']}.")
    return "\n".join(lines)


def check_draft(text: str, facts: dict) -> list[str]:
    issues = []
    ft = json.dumps(facts)
    for d in DATE.findall(text):
        if d not in ft:
            issues.append(f"date not in FACTS: {d}")
    body = re.sub(r"(?m)^\s*\d+[.)]\s", " ", DATE.sub(" ", text))
    date_parts = [float(x) for d in DATE.findall(ft) for x in d.split("-")]   # "December 1, 2026" is fine
    allowed = [float(x) for x in NUM.findall(DATE.sub(" ", ft))] + date_parts + [0.0, 1.0, 2.0, 3.0]
    for x in NUM.findall(body):
        if not any(abs(float(x) - a) <= 5e-4 for a in allowed):
            issues.append(f"number not in FACTS: {x}")
    if ADVICE.search(text):
        issues.append("contains trading advice wording")
    if FORWARD.search(text):
        issues.append("contains a forecast the data cannot support")
    if len(text.strip()) < 40:
        issues.append("draft is empty or too short")
    return sorted(set(issues))

 
def n_gate(s: State) -> State:
    return {"skip": s["facts"]["n_dates"] < s["min_dates"], "attempts": 0, "llm_used": False}


def n_draft(s: State, llm: Callable[[str, str], str]) -> State:
    p = f"FACTS:\n{json.dumps(s['facts'], indent=1)}\n\nWrite the hypotheses."
    return {"draft": llm(p, SYSTEM), "attempts": s.get("attempts", 0) + 1, "llm_used": True}


def n_check(s: State) -> State:
    return {"issues": check_draft(s["draft"], s["facts"])}


def n_revise(s: State, llm: Callable[[str, str], str]) -> State:
    p = (f"Your draft had these problems: {s['issues']}.\nRewrite it fixing them. Use only numbers from FACTS.\n\n"
         f"FACTS:\n{json.dumps(s['facts'], indent=1)}\n\nDRAFT:\n{s['draft']}")
    return {"draft": llm(p, SYSTEM), "attempts": s["attempts"] + 1}


def route_gate(s: State) -> str:
    return "finalize" if s["skip"] else "draft"


def route_check(s: State) -> str:
    return "finalize" if not s["issues"] or s["attempts"] >= s["max_attempts"] else "revise"


def n_finalize(s: State) -> State:
    facts = s["facts"]
    if s.get("skip"):
        text = (f"Only {facts['n_dates']} scored dates (minimum {s['min_dates']}). No analysis performed.\n"
                + facts_text(facts))
    elif s.get("issues"):
        kinds = sorted({i.split(":")[0] for i in s["issues"]})
        text = ("LLM draft rejected after checks (" + "; ".join(kinds) + "). Facts only:\n"
                + facts_text(facts))
    else:
        text = s["draft"].strip()
    return {"final": f"{text}\n\n{DISCLAIMER}"}


def reflect(facts: dict, llm, min_dates=30, max_attempts=2) -> State:
    s: State = {"facts": facts, "min_dates": min_dates, "max_attempts": max_attempts}
    s.update(n_gate(s))
    if route_gate(s) == "draft":
        s.update(n_draft(s, llm)); s.update(n_check(s))
        while route_check(s) == "revise":
            s.update(n_revise(s, llm)); s.update(n_check(s))
    s.update(n_finalize(s))
    return s