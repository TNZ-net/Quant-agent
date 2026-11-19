"""Needs the OpenD gateway running and `pip install futu-api`.
I couldn't test this against OpenD, so verify against your version and account quota."""
import os, time
import pandas as pd

COLUMNS = ["ticker", "date", "open", "high", "low", "close", "volume"]


class MoomooSource:
    def __init__(self, host=None, port=None):
        from moomoo import OpenQuoteContext
        self.ctx = OpenQuoteContext(host=host or os.getenv("MOOMOO_HOST", "127.0.0.1"),
                                    port=int(port or os.getenv("MOOMOO_PORT", 11111)))

    def daily_bars(self, tickers, start=None, end=None):
        from moomoo import KLType, AuType, RET_OK
        frames = []
        for code in tickers:
            page_key = None
            while True:
                ret, df, page_key = self.ctx.request_history_kline(
                    code, start=start, end=end, ktype=KLType.K_DAY, autype=AuType.QFQ,
                    max_count=1000, page_req_key=page_key)
                if ret != RET_OK:
                    raise RuntimeError(f"Moomoo error for {code}: {df}")
                frames.append(df.assign(ticker=code))
                if page_key is None:
                    break
            time.sleep(0.6)   # stay under the rate limit
        raw = pd.concat(frames, ignore_index=True)
        raw["date"] = pd.to_datetime(raw["time_key"]).dt.normalize()
        return raw[COLUMNS].drop_duplicates(["ticker", "date"])

    def close(self):
        self.ctx.close()
