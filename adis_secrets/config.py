import os
from pathlib import Path

_config_cache: dict = {}
_config_mtime: float = 0.0


def _find_config_file() -> Path | None:
    """Search cwd and parent dirs for deploy.config.yml."""
    current = Path(os.getcwd())
    for directory in [current, *current.parents]:
        candidate = directory / "deploy.config.yml"
        if candidate.exists():
            return candidate
    return None


def _load_config() -> dict:
    global _config_cache, _config_mtime
    config_file = _find_config_file()
    if not config_file:
        return {}
    mtime = config_file.stat().st_mtime
    if mtime != _config_mtime:
        import yaml

        with open(config_file) as f:
            raw = yaml.safe_load(f) or {}
        _config_cache = raw.get("config", {})
        _config_mtime = mtime
    return _config_cache


def get_config(key: str, default=None):
    """
    Read a config value from deploy.config.yml under the config: key.
    Values are non-sensitive and loggable.
    Returns default if key not found. Never raises.
    """
    try:
        cfg = _load_config()
        return cfg.get(key, default)
    except Exception:
        return default
