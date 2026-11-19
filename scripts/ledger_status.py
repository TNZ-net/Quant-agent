import pandas as pd
from sqlalchemy import text
from quantagent.db import get_engine
from quantagent.metrics.prediction import ic_by_date

e = get_engine()
with e.connect() as c:
    counts = c.execute(text("""SELECT mv.name, count(*), count(o.prediction_id), count(DISTINCT p.signal_date)
        FROM predictions p JOIN model_versions mv ON mv.id = p.model_version_id
        LEFT JOIN outcomes o ON o.prediction_id = p.id GROUP BY mv.name ORDER BY mv.name""")).all()
print(f"{'model':<10}{'predictions':>12}{'scored':>8}{'dates':>7}")
for r in counts:
    print(f"{r[0]:<10}{r[1]:>12}{r[2]:>8}{r[3]:>7}")

d = pd.read_sql(text("""SELECT mv.name AS model, p.signal_date AS date, p.ticker, p.score, o.realized_rank
    FROM predictions p JOIN model_versions mv ON mv.id = p.model_version_id
    JOIN outcomes o ON o.prediction_id = p.id"""), e, parse_dates=["date"])
if d.empty:
    print("no scored predictions yet (first outcomes appear ~6 trading days after the first log)")
else:
    for name, g in d.groupby("model"):
        g = g.set_index(["date", "ticker"])
        ic = ic_by_date(g["score"], g["realized_rank"]).dropna()
        note = "   (too few dates to conclude anything)" if len(ic) < 30 else ""
        print(f"{name:<10} IC {ic.mean():+.4f} over {len(ic)} dates{note}")