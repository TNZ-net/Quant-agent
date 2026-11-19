from sqlalchemy import text
from quantagent.db import get_engine
from quantagent.ledger.commit import verify_row

with get_engine().connect() as c:
    rows = c.execute(text("SELECT * FROM predictions")).mappings().all()
bad = [r["id"] for r in rows if not verify_row(dict(r))]
print(f"{len(rows)} predictions checked, {len(bad)} mismatches", bad[:10])