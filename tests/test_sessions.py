import pandas as pd
from datetime import datetime
from quantagent.pipeline.sessions import ET, last_completed_session


def test_before_close_uses_previous_day():
    assert last_completed_session(datetime(2026, 11, 10, 15, 0, tzinfo=ET)) == pd.Timestamp("2026-11-09")


def test_after_close_uses_today():
    assert last_completed_session(datetime(2026, 11, 10, 17, 0, tzinfo=ET)) == pd.Timestamp("2026-11-10")