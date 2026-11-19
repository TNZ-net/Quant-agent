import hashlib, json
from datetime import timezone


def canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def commit_hash(payload: dict) -> str:
    return hashlib.sha256(canonical(payload).encode()).hexdigest()


def iso(ts) -> str:
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_payload(ticker, signal_date, horizon_days, score, model_version_id, config_hash, features, created_at) -> dict:
    return dict(ticker=ticker, signal_date=str(signal_date), horizon_days=int(horizon_days),
                score=float(score), model_version_id=int(model_version_id), config_hash=config_hash,
                features=features, created_at=iso(created_at))


def verify_row(row: dict) -> bool:
    p = build_payload(row["ticker"], row["signal_date"], row["horizon_days"], row["score"],
                      row["model_version_id"], row["config_hash"], row["features"], row["created_at"])
    return commit_hash(p) == row["commit_hash"]