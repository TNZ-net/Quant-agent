import pandas as pd
from quantagent.reflection import core

FACTS = dict(n_dates=45, models={"ensemble": dict(ic_mean=0.0123, ci_low=-0.0210, ci_high=0.0451,
                                                  status="no_detectable_edge")},
             worst_misses=[dict(date="2026-12-01", ticker="US.NVDA", predicted_rank=0.4, realized_rank=-0.45)])
GOOD = ("1. Ensemble IC is 0.0123 with an interval from -0.0210 to 0.0451, so no edge is detectable. "
        "Check: re-run the bootstrap with a larger block.")


def _llm(*replies):
    it = iter(replies); calls = []
    def f(p, s):
        calls.append(p); return next(it)
    f.calls = calls
    return f


def test_insufficient_sample_never_calls_llm():
    def boom(p, s): raise AssertionError("LLM must not be called")
    out = core.reflect(dict(FACTS, n_dates=5), boom, min_dates=30)
    assert "No analysis performed" in out["final"] and not out["llm_used"]


def test_valid_draft_accepted_and_disclaimer_added():
    out = core.reflect(FACTS, _llm(GOOD))
    assert out["issues"] == [] and out["final"].startswith("1. Ensemble IC") and core.DISCLAIMER in out["final"]


def test_hallucinated_number_triggers_revision():
    bad = "1. Ensemble IC is 0.0999, a strong edge. Check: wait for more data."
    llm = _llm(bad, GOOD)
    out = core.reflect(FACTS, llm)
    assert len(llm.calls) == 2 and out["attempts"] == 2 and out["issues"] == []
    assert "0.0999" not in out["final"]


def test_persistent_hallucination_falls_back_to_facts():
    bad = "1. Ensemble IC is 0.0999, a strong edge. Check: wait for more data."
    out = core.reflect(FACTS, _llm(bad, bad))
    assert "rejected" in out["final"] and "0.0999" not in out["final"]


def test_trading_advice_is_flagged():
    assert any("advice" in i for i in core.check_draft("1. You should buy the ensemble picks now, okay.", FACTS))


def test_dates_must_come_from_facts():
    assert core.check_draft("1. Misses cluster on 2026-12-05 for NVDA. Check: inspect that day.", FACTS)


def test_worst_misses_ranks_by_error():
    d = pd.DataFrame(dict(model=["m"] * 3, date=pd.to_datetime(["2026-01-01"] * 3), ticker=list("abc"),
                          score=[3.0, 2.0, 1.0], realized_rank=[-0.5, 0.0, 0.5]))
    top = core.worst_misses(d, "m", n=1)[0]
    assert top["ticker"] in ("a", "c")

def test_dates_written_in_prose_are_accepted_but_other_years_are_not():
    ok = "1. The largest miss was NVDA on December 1, 2026. Check: inspect that day's features."
    assert core.check_draft(ok, FACTS) == []
    assert core.check_draft(ok.replace("2026", "2027"), FACTS)

def test_forecast_claims_are_flagged():
    assert any("forecast" in i for i in core.check_draft(
        "1. The momentum model is likely to perform better in the future. Check: wait.", FACTS))
