import hashlib, json
from sqlalchemy import text
from ..features.build import FEATURE_COLS


def model_hash(cfg: dict) -> str:
    spec = dict(horizon_days=cfg["horizon_days"], embargo_days=cfg["embargo_days"], features=FEATURE_COLS,
                model=cfg["model"], walk_forward=cfg["walk_forward"])
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:12]


def get_or_create_version(engine, name: str, cfg: dict) -> int:
    h = model_hash(cfg)
    with engine.begin() as c:
        row = c.execute(text("SELECT id FROM model_versions WHERE name=:n AND config_hash=:h"),
                        {"n": name, "h": h}).first()
        if row:
            return row[0]
        return c.execute(text("INSERT INTO model_versions (name, config_hash) VALUES (:n,:h) RETURNING id"),
                         {"n": name, "h": h}).scalar()