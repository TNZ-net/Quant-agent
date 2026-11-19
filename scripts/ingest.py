from quantagent.config import load_config
from quantagent.db import get_engine
from quantagent.data.moomoo_source import MoomooSource
from quantagent.data.ingest import run_ingest

src = MoomooSource()
try:
    print(run_ingest(get_engine(), load_config(), src), "rows upserted")
finally:
    src.close()