import logging
import os
import time

logger = logging.getLogger(__name__)


class SecretsCache:
    TTL_SECONDS: int = 300

    def __init__(self):
        self._cache: dict = {}
        self._loaded_at: float = 0.0

    def is_stale(self) -> bool:
        return (time.time() - self._loaded_at) > self.TTL_SECONDS

    def load(self, data: dict):
        self._cache = data
        self._loaded_at = time.time()

    def get(self, key: str) -> str:
        if key not in self._cache:
            raise KeyError(
                f"Secret '{key}' not found. "
                f"Available keys: {sorted(self._cache.keys())}"
            )
        return self._cache[key]

    def invalidate(self):
        self._cache = {}
        self._loaded_at = 0.0


_cache = SecretsCache()


def load_env_file(path: str) -> dict:
    """Load KEY=VALUE pairs. Ignores # comments and blank lines."""
    result = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def get_secret(key: str) -> str:
    """
    Read a secret by key.
    Uses CONTAINER_ENV_FILE_APP_SECRETS env var to find secrets file.
    Caches with TTL of 300 seconds.
    NEVER logs or prints secret values - only key names.
    """
    backend = os.environ.get("VAULT_CFG_KEY_BACKEND", "file")
    if backend == "infisical":
        from adis_secrets.backends.infisical import get_secret as _get

        return _get(key)

    if _cache.is_stale():
        secrets_file = os.environ.get("CONTAINER_ENV_FILE_APP_SECRETS")
        if not secrets_file:
            raise EnvironmentError(
                "CONTAINER_ENV_FILE_APP_SECRETS is not set. "
                "This must be injected by deploy_runner.py "
                "at container startup."
            )
        data = load_env_file(secrets_file)
        _cache.load(data)
        logger.debug(
            f"[adis_secrets] loaded {len(data)} keys: "
            f"{sorted(data.keys())}"
        )
    return _cache.get(key)


def set_tenant_context(slug: str):
    backend = os.environ.get("VAULT_CFG_KEY_BACKEND", "file")
    if backend == "infisical":
        from adis_secrets.backends.infisical import set_tenant_context as _set

        _set(slug)


def clear_tenant_context():
    backend = os.environ.get("VAULT_CFG_KEY_BACKEND", "file")
    if backend == "infisical":
        from adis_secrets.backends.infisical import clear_tenant_context as _clear

        _clear()
