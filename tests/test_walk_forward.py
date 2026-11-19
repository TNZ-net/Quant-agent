from quantagent.backtest.walk_forward import purged_splits


def test_no_overlap_and_gap():
    dates = list(range(1000)); gap = 11
    n = 0
    for tr, te in purged_splits(dates, 300, 50, 50, gap):
        n += 1
        assert max(tr) < min(te)
        assert min(te) - max(tr) > gap
    assert n > 5