from datetime import datetime, timezone
from quantagent.ledger.anchor import merkle_root
from quantagent.ledger.commit import build_payload, commit_hash, verify_row

NOW = datetime(2026, 11, 9, 22, 30, tzinfo=timezone.utc)


def _payload(score=0.12):
    return build_payload("US.AAPL", "2026-11-06", 5, score, 1, "abc123", {"mom_12_1": 0.3}, NOW)


def test_hash_deterministic_and_tamper_evident():
    assert commit_hash(_payload()) == commit_hash(_payload())
    assert commit_hash(_payload()) != commit_hash(_payload(score=0.13))


def test_verify_row_roundtrip():
    row = dict(ticker="US.AAPL", signal_date="2026-11-06", horizon_days=5, score=0.12, model_version_id=1,
               config_hash="abc123", features={"mom_12_1": 0.3}, created_at=NOW,
               commit_hash=commit_hash(_payload()))
    assert verify_row(row)
    row["score"] = 0.99
    assert not verify_row(row)


def test_merkle_order_independent_and_sensitive():
    h = ["a" * 64, "b" * 64, "c" * 64]
    assert merkle_root(h) == merkle_root(h[::-1])
    assert merkle_root(h) != merkle_root(h[:2])