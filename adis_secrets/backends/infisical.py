import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from types import SimpleNamespace

from adis_secrets.backends.infisical_rest import InfisicalClient
from adis_secrets.config import get_config

logger = logging.getLogger(__name__)

_client = None
_tenant_slug: str | None = None
_secret_cache: dict = {}
_slug_cache: dict | None = None
_slug_cache_loaded_at: float = 0.0

SECRET_CACHE_TTL = 300
SLUG_CACHE_TTL = 86400


def _load_bootstrap_credentials() -> dict:
    """
    Returns the raw credential dict needed to initialise the Infisical client.
    Currently file-based via VAULT_CFG_KEY_SECRETS_PATH or APP_PROJECT_NAME.
    Replace ONLY this function to switch bootstrap mechanism
    (e.g. DO droplet machine identity, IMDS, Infisical agent).
    Nothing else in this file or any other file should change.
    """
    from adis_secrets.reader import load_env_file, resolve_bootstrap_secrets_file

    secrets_file = resolve_bootstrap_secrets_file()
    return load_env_file(secrets_file)


def _required_config(key: str) -> str:
    value = get_config(key)
    if value is None or value == "":
        raise RuntimeError(f"Missing required config key: {key}")
    return str(value)


def _main_project_client() -> InfisicalClient:
    global _client
    if _client is None:
        creds = _load_bootstrap_credentials()
        client_id = creds.get("VAULT_SEC_KEY_INFISICAL_CLIENT_ID")
        client_secret = creds.get("VAULT_SEC_KEY_INFISICAL_CLIENT_SECRET")
        if not client_id:
            raise RuntimeError(
                "Missing required bootstrap credential: "
                "VAULT_SEC_KEY_INFISICAL_CLIENT_ID"
            )
        if not client_secret:
            raise RuntimeError(
                "Missing required bootstrap credential: "
                "VAULT_SEC_KEY_INFISICAL_CLIENT_SECRET"
            )
        _client = InfisicalClient(
            project_id=_required_config("infisical_project_id"),
            client_id=client_id,
            client_secret=client_secret,
        )
    return _client


class _SecretsFacade:
    def get_secret_by_name(
        self,
        *,
        secret_name: str,
        project_id: str,
        environment_slug: str,
        secret_path: str,
        type: str = "shared",
    ):
        client = _main_project_client()
        value = client.get_secret(
            name=secret_name,
            environment=environment_slug,
            secret_path=secret_path,
        )
        if value is None:
            raise KeyError(f"Secret with name '{secret_name}' not found.")
        return SimpleNamespace(
            secret=SimpleNamespace(secret_value=value),
            secret_value=value,
        )

    def create_secret(
        self,
        *,
        secret_name: str,
        secret_value: str,
        project_id: str,
        environment_slug: str,
        secret_path: str,
        type: str = "shared",
    ):
        client = _main_project_client()
        client.set_secret(
            name=secret_name,
            value=secret_value,
            environment=environment_slug,
            secret_path=secret_path,
        )

    def update_secret(self, **kwargs):
        self.create_secret(**kwargs)

    def create_secret_by_name(self, **kwargs):
        self.create_secret(**kwargs)

    def update_secret_by_name(self, **kwargs):
        self.update_secret(**kwargs)


def _get_client():
    _main_project_client()
    return SimpleNamespace(secrets=_SecretsFacade())


def _cache_get(key: str, folder: str, project_id: str) -> str | None:
    entry = _secret_cache.get((key, folder, project_id))
    if not entry:
        return None
    value, loaded_at = entry
    if (time.time() - loaded_at) > SECRET_CACHE_TTL:
        _secret_cache.pop((key, folder, project_id), None)
        return None
    return value


def _cache_set(key: str, folder: str, project_id: str, value: str):
    _secret_cache[(key, folder, project_id)] = (value, time.time())


def set_tenant_context(slug: str):
    global _tenant_slug
    _tenant_slug = slug


def clear_tenant_context():
    global _tenant_slug
    _tenant_slug = None


def get_tenant_context() -> str | None:
    return _tenant_slug


def get_secret(key: str) -> str:
    infisical_project_id = _required_config("infisical_project_id")
    infisical_environment = _required_config("infisical_environment")

    folders = [f"/{_tenant_slug}", "/app"] if _tenant_slug else ["/app"]
    folders_searched: list[str] = []

    for folder in folders:
        folders_searched.append(folder)
        cached = _cache_get(key, folder, infisical_project_id)
        if cached is not None:
            return cached
        try:
            value = _main_project_client().get_secret(
                name=key,
                environment=infisical_environment,
                secret_path=folder,
            )
            if value is not None:
                _cache_set(key, folder, infisical_project_id, value)
                return value
        except Exception as exc:
            logger.info(
                "[infisical_backend] lookup failed key=%s folder=%s error_type=%s",
                key,
                folder,
                type(exc).__name__,
            )

    raise KeyError(f"Secret '{key}' not found in folders: {folders_searched}")


def invalidate_slug_cache():
    global _slug_cache, _slug_cache_loaded_at
    _slug_cache = None
    _slug_cache_loaded_at = 0.0


def get_tenant_slug(team_id: str) -> str:
    global _slug_cache, _slug_cache_loaded_at

    infisical_environment = _required_config("infisical_environment")

    if _slug_cache is None or (time.time() - _slug_cache_loaded_at) > SLUG_CACHE_TTL:
        try:
            value = _main_project_client().get_secret(
                name="TENANT_SLUGS",
                environment=infisical_environment,
                secret_path="/app",
            )
            _slug_cache = json.loads(value) if value else {}
            if not isinstance(_slug_cache, dict):
                _slug_cache = {}
        except Exception as exc:
            logger.info(
                "[infisical_backend] TENANT_SLUGS load failed folder=/app error_type=%s",
                type(exc).__name__,
            )
            _slug_cache = {}
        _slug_cache_loaded_at = time.time()

    return str(_slug_cache.get(team_id, team_id))


def _slugify(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "tenant"


def write_tenant_token(team_id: str, token_data: dict):
    infisical_environment = _required_config("infisical_environment")
    client = _main_project_client()

    slug = _slugify(str(token_data.get("team_name", team_id)))
    payload = json.dumps(
        {
            **token_data,
            "slug": slug,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        },
        sort_keys=True,
    )
    client.set_secret(
        name=team_id,
        value=payload,
        environment=infisical_environment,
        secret_path="/tenants",
    )

    current_slugs: dict = {}
    existing = client.get_secret(
        name="TENANT_SLUGS",
        environment=infisical_environment,
        secret_path="/app",
    )
    if existing:
        try:
            current_slugs = json.loads(existing)
            if not isinstance(current_slugs, dict):
                current_slugs = {}
        except Exception:
            current_slugs = {}

    current_slugs[team_id] = slug
    slugs_payload = json.dumps(current_slugs, sort_keys=True)
    client.set_secret(
        name="TENANT_SLUGS",
        value=slugs_payload,
        environment=infisical_environment,
        secret_path="/app",
    )
    invalidate_slug_cache()
    logger.info("[infisical_backend] wrote tenant token team_id=%s slug=%s", team_id, slug)


def get_tenant_token(team_id: str) -> dict | None:
    infisical_environment = _required_config("infisical_environment")
    try:
        value = _main_project_client().get_secret(
            name=team_id,
            environment=infisical_environment,
            secret_path="/tenants",
        )
        data = json.loads(value) if value else {}
        return data if isinstance(data, dict) else None
    except Exception:
        return None
