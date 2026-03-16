import logging
import os

from adis_secrets.reader import _cache

logger = logging.getLogger(__name__)


def write_tenant_token(team_id: str, token_data: dict) -> None:
    """
    Write a tenant token to the configured secrets backend.
    Invalidates the secrets cache after writing.
    """
    backend = os.environ.get("VAULT_CFG_KEY_BACKEND")
    if not backend:
        raise EnvironmentError(
            "VAULT_CFG_KEY_BACKEND is not set. "
            "Set it to 'infisical' (recommended) or 'file' (local dev only)."
        )
    if backend == "file":
        from adis_secrets.backends.file import write_tenant_token as _write

        _write(team_id, token_data)
        _cache.invalidate()
        logger.info(
            f"[adis_secrets] wrote token for team_id={team_id} "
            f"backend=file"
        )
    elif backend == "aws":
        from adis_secrets.backends.aws import write_tenant_token as _write

        _write(team_id, token_data)
    elif backend == "gcp":
        from adis_secrets.backends.gcp import write_tenant_token as _write

        _write(team_id, token_data)
    elif backend == "infisical":
        from adis_secrets.backends.infisical import write_tenant_token as _write

        _write(team_id, token_data)
    else:
        raise ValueError(
            f"Unknown VAULT_CFG_KEY_BACKEND='{backend}'. "
            f"Supported: file, aws, gcp, infisical"
        )


def get_tenant_token(team_id: str) -> dict | None:
    """
    Retrieve a tenant token from the configured secrets backend.
    Returns None if team_id not found.
    """
    backend = os.environ.get("VAULT_CFG_KEY_BACKEND")
    if not backend:
        raise EnvironmentError(
            "VAULT_CFG_KEY_BACKEND is not set. "
            "Set it to 'infisical' (recommended) or 'file' (local dev only)."
        )
    if backend == "file":
        from adis_secrets.backends.file import get_tenant_token as _get

        return _get(team_id)
    elif backend == "aws":
        from adis_secrets.backends.aws import get_tenant_token as _get

        return _get(team_id)
    elif backend == "gcp":
        from adis_secrets.backends.gcp import get_tenant_token as _get

        return _get(team_id)
    elif backend == "infisical":
        from adis_secrets.backends.infisical import get_tenant_token as _get

        return _get(team_id)
    else:
        raise ValueError(
            f"Unknown VAULT_CFG_KEY_BACKEND='{backend}'. "
            f"Supported: file, aws, gcp, infisical"
        )


def get_tenant_slug(team_id: str) -> str:
    backend = os.environ.get("VAULT_CFG_KEY_BACKEND")
    if not backend:
        raise EnvironmentError(
            "VAULT_CFG_KEY_BACKEND is not set. "
            "Set it to 'infisical' (recommended) or 'file' (local dev only)."
        )
    if backend == "infisical":
        from adis_secrets.backends.infisical import get_tenant_slug as _get

        return _get(team_id)
    return team_id
