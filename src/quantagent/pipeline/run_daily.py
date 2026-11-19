import argparse
from datetime import date
from ..config import load_config
from ..db import get_engine
from ..ledger.anchor import anchor_day
from .predict import run_predict
from .score import run_score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ingest", action="store_true", help="skip the Moomoo download")
    a = ap.parse_args()
    cfg, engine = load_config(), get_engine()
    if not a.no_ingest:
        from ..data.ingest import run_ingest
        from ..data.moomoo_source import MoomooSource
        src = MoomooSource()
        try:
            print("ingested rows:", run_ingest(engine, cfg, src))
        finally:
            src.close()
    print("scored:", run_score(engine, cfg))
    res = run_predict(engine, cfg)
    print("logged:", res)
    print("anchor:", anchor_day(engine, date.fromisoformat(res["signal_date"])))


if __name__ == "__main__":
    main()