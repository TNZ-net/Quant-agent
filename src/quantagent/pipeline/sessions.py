from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import pandas as pd

ET = ZoneInfo("America/New_York")


def last_completed_session(now: datetime | None = None) -> pd.Timestamp:
    now = now or datetime.now(ET)
    d = now.date() if now.time() >= time(16, 30) else now.date() - timedelta(days=1)
    return pd.Timestamp(d)