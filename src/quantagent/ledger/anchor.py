import hashlib
from pathlib import Path


def merkle_root(hashes: list[str]) -> str:
    level = sorted(hashes)
    if not level:
        return hashlib.sha256(b"").hexdigest()
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256((a + b).encode()).hexdigest() for a, b in zip(level[::2], level[1::2])]
    return level[0]


def anchor_day(engine, day, out_dir="anchors") -> str:
    from sqlalchemy import text
    with engine.begin() as c:
        hs = [r[0] for r in c.execute(text("SELECT commit_hash FROM predictions WHERE signal_date=:d"), {"d": day})]
        root = merkle_root(hs)
        c.execute(text("INSERT INTO anchors (day, merkle_root, n_leaves) VALUES (:d,:r,:n) ON CONFLICT DO NOTHING"),
                  {"d": day, "r": root, "n": len(hs)})
        stored = c.execute(text("SELECT merkle_root, n_leaves FROM anchors WHERE day=:d"), {"d": day}).first()
    Path(out_dir).mkdir(exist_ok=True)
    Path(out_dir, f"{day}.txt").write_text(f"{day} {stored[0]} {stored[1]}\n")
    return stored[0]