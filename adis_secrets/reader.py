import logging
import os
import re
import time
from pathlib import Path
from fnmatch import fnmatch

from adis_secrets.client import _assert_ready, clear_tenant_context, set_tenant_context
from adis_secrets.manifest import get_manifest

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


def _get_env_unchecked(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def resolve_bootstrap_secrets_file(project_name: str | None = None) -> str:
    explicit_path = _get_env_unchecked("VAULT_CFG_KEY_SECRETS_PATH")
    if explicit_path:
        resolved_path = Path(explicit_path).expanduser()
    else:
        project_name = project_name or _get_env_unchecked("APP_PROJECT_NAME")
        if not project_name:
            raise EnvironmentError(
                "Cannot resolve secrets file: set VAULT_CFG_KEY_SECRETS_PATH or APP_PROJECT_NAME"
            )
        resolved_path = Path(f"~/.secrets/{project_name}-secrets.env").expanduser()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Secrets file not found at {resolved_path}")

    return str(resolved_path)


def _check_key_access(section: str, key: str):
    manifest = get_manifest()
    entries = manifest.get(section, [])
    if not isinstance(entries, list):
        entries = []
    
    for entry in entries:
        if "key" in entry and entry["key"] == key:
            return
            
    for entry in entries:
        if "pattern" in entry and fnmatch(key, entry["pattern"]):
            return
            
    proj = manifest.get("project", "unknown")
    raise PermissionError(f"Access denied: '{key}' is not declared in manifest.yml (project: {proj})")


def _check_file_access(path: Path):
    manifest = get_manifest()
    files = manifest.get("files", [])
    if not isinstance(files, list):
        files = []
        
    resolved_path = str(path.expanduser().resolve())
    
    for entry in files:
        entry_path = entry.get("path")
        if not entry_path:
            continue
            
        def replace_var(m):
            return _get_env_unchecked(m.group(1), "") or ""
            
        entry_path_subbed = re.sub(r"\{\{([^}]+)\}\}", replace_var, entry_path)
        entry_path_resolved = str(Path(entry_path_subbed).expanduser().resolve())
        if entry_path.endswith("/") and not entry_path_resolved.endswith("/"):
            entry_path_resolved += "/"
            
        entry_type = entry.get("type")
        if entry_type == "exact":
            if resolved_path == entry_path_resolved:
                return
        elif entry_type == "directory_prefix":
            if resolved_path.startswith(entry_path_resolved) or resolved_path == entry_path_resolved.rstrip("/"):
                return
                
    proj = manifest.get("project", "unknown")
    raise PermissionError(f"Access denied: file '{str(path)}' is not declared in manifest.yml (project: {proj})")



def get_secret(key: str) -> str:
    """
    Read a secret by key.
    Resolves secrets file via VAULT_CFG_KEY_SECRETS_PATH or APP_PROJECT_NAME.
    Caches with TTL of 300 seconds.
    NEVER logs or prints secret values - only key names.
    """
    _assert_ready("get_secret")
    _check_key_access("secrets", key)
    backend = _get_env_unchecked("VAULT_CFG_KEY_BACKEND")
    if not backend:
        raise EnvironmentError(
            "VAULT_CFG_KEY_BACKEND is not set. "
            "Set it to 'infisical' (recommended) or 'file' (local dev only)."
        )
    if backend == "infisical":
        from adis_secrets.backends.infisical import get_secret as _get

        return _get(key)

    if _cache.is_stale():
        secrets_file = resolve_bootstrap_secrets_file()
        data = load_env_file(secrets_file)
        _cache.load(data)
        logger.debug(
            f"[adis_secrets] loaded {len(data)} keys: "
            f"{sorted(data.keys())}"
        )
    return _cache.get(key)




def get_env(key: str, default: str | None = None) -> str | None:
    """Read an environment variable."""
    _assert_ready("get_env")
    _check_key_access("env", key)
    return os.environ.get(key, default)


def get_all_env() -> dict[str, str]:
    """Return a copy of the entire environment."""
    return dict(os.environ)


def read_file(path: str | Path) -> str:
    """Read the contents of a file as a string."""
    _assert_ready("read_file")
    if isinstance(path, str):
        path = Path(path)
    _check_file_access(path)
    return path.expanduser().read_text()
