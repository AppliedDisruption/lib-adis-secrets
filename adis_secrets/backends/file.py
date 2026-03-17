# ~/.secrets/ is bind-mounted by deploy_runner.py.
# Writes here land on the host automatically.

import json
import logging
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_LOCAL_ENVS = {"local", "dev", "test"}


def _check_local_only():
    """File backend is only allowed for local development."""
    deploy_env = os.environ.get("APP_DEPLOY_ENV", "local").lower()
    if deploy_env not in _LOCAL_ENVS:
        raise RuntimeError(
            f"File backend is not allowed in '{deploy_env}' environment. "
            "Use VAULT_CFG_KEY_BACKEND=infisical for cloud/SSH deployments."
        )
    warnings.warn(
        "File backend is deprecated and will be removed in a future version. "
        "Migrate to VAULT_CFG_KEY_BACKEND=infisical.",
        DeprecationWarning,
        stacklevel=3,
    )


def _token_file_path() -> Path:
    """
    Derives path from the resolved bootstrap secrets file path.
    tenant_tokens.json sits alongside the secrets file.
    """
    from adis_secrets.reader import resolve_bootstrap_secrets_file

    secrets_file = resolve_bootstrap_secrets_file()
    return Path(os.path.dirname(secrets_file)) / "tenant_tokens.json"


def write_tenant_token(team_id: str, token_data: dict) -> None:
    _check_local_only()
    path = _token_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if path.exists():
        with open(path) as f:
            existing = json.load(f)

    existing[team_id] = {
        **token_data,
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }

    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(existing, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp_path, path)
    logger.debug(
        f"[file_backend] wrote token for team_id={team_id} "
        f"path={path}"
    )


def get_tenant_token(team_id: str) -> dict | None:
    _check_local_only()
    path = _token_file_path()
    if not path.exists():
        return None
    with open(path) as f:
        tokens = json.load(f)
    return tokens.get(team_id)
