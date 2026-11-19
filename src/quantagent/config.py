import hashlib, json, os
from pathlib import Path
import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def load_config(path=None) -> dict:
    p = Path(path or os.getenv("QA_CONFIG", ROOT / "config" / "settings.yaml"))
    return yaml.safe_load(p.read_text())


def config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]