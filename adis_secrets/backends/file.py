# /.secrets/ is bind-mounted by deploy_runner.py.
# Writes here land on the host automatically.
# CONTAINER_ENV_FILE_APP_SECRETS is the authoritative path source.

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _token_file_path() -> Path:
    """
    Derives path from CONTAINER_ENV_FILE_APP_SECRETS.
    tenant_tokens.json sits alongside the secrets file.
    """
    secrets_file = os.environ.get("CONTAINER_ENV_FILE_APP_SECRETS")
    if not secrets_file:
        raise EnvironmentError(
            "CONTAINER_ENV_FILE_APP_SECRETS is not set. "
            "Cannot derive VAULT_SEC_FILE_TENANT_TOKENS path."
        )
    return Path(os.path.dirname(secrets_file)) / "tenant_tokens.json"


def write_tenant_token(team_id: str, token_data: dict) -> None:
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
    path = _token_file_path()
    if not path.exists():
        return None
    with open(path) as f:
        tokens = json.load(f)
    return tokens.get(team_id)
