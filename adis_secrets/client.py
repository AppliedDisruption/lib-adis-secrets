"""
client.py — Backend-agnostic vault infrastructure.

Owns: VaultBackend Protocol, VaultClient, startup phase state machine,
      client registry, ContextVars for per-request tenant isolation,
      secret cache operations, and the _assert_ready() gate.

Dependency rule: this module has zero imports from any backend module.
Backend modules (infisical.py, future hashicorp.py) import from here —
never the reverse.
"""

import contextvars
import time
from enum import Enum
from typing import Protocol


# ---------------------------------------------------------------------------
# Startup phase state machine
# ---------------------------------------------------------------------------

class StartupPhase(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING  = "initializing"
    READY         = "ready"


_startup_phase: StartupPhase = StartupPhase.UNINITIALIZED


def _assert_ready(operation: str) -> None:
    if _startup_phase != StartupPhase.READY:
        raise RuntimeError(
            f"adis_secrets is not initialised. "
            f"Call init_client(project_name, manifest_path) before calling {operation}(). "
            f"Current phase: {_startup_phase.value}"
        )


# ---------------------------------------------------------------------------
# VaultBackend Protocol — contract any backend must satisfy
# ---------------------------------------------------------------------------

class VaultBackend(Protocol):
    def get_secret(self, key: str, environment: str, folder: str) -> str:
        """Fetch a secret by key. Raises KeyError if not found."""
        ...

    def get_env_var(self, key: str, environment: str, folder: str) -> str:
        """Fetch a non-secret env var. Raises KeyError if not found."""
        ...

    def write_secret(self, key: str, value: str, environment: str, folder: str) -> None:
        """Write or update a secret."""
        ...


# ---------------------------------------------------------------------------
# VaultClient — holds a VaultBackend instance and per-client caches
# ---------------------------------------------------------------------------

class VaultClient:
    def __init__(self, project_name: str, manifest_path: str):
        self.project_name = project_name
        self.manifest_path = manifest_path
        self._client: VaultBackend | None = None
        self._secret_cache: dict = {}

    @property
    def client(self) -> VaultBackend:
        if self._client is None:
            raise RuntimeError("VaultClient not initialized with credentials")
        return self._client


# ---------------------------------------------------------------------------
# Client registry and ContextVars
# ---------------------------------------------------------------------------

_client_registry: dict[str, VaultClient] = {}
_active_client_var: contextvars.ContextVar[VaultClient | None] = contextvars.ContextVar(
    "vault_client", default=None
)
_current_tenant_slug_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_slug", default=None
)


def _get_active_vault_client() -> VaultClient:
    active = _active_client_var.get()
    if active is not None:
        return active
    if len(_client_registry) == 1:
        return next(iter(_client_registry.values()))
    raise RuntimeError(
        "No VaultClient is active. Call init_client(project_name, manifest_path) "
        "before accessing secrets."
    )


def set_tenant_context(slug: str) -> None:
    _current_tenant_slug_var.set(slug)


def clear_tenant_context() -> None:
    _current_tenant_slug_var.set(None)


def get_tenant_context() -> str | None:
    return _current_tenant_slug_var.get()


# ---------------------------------------------------------------------------
# Secret cache operations (backend-agnostic, operate on VaultClient state)
# ---------------------------------------------------------------------------

SECRET_CACHE_TTL = 300


def _cache_get(key: str, folder: str, project_id: str) -> str | None:
    vc = _get_active_vault_client()
    entry = vc._secret_cache.get((key, folder, project_id))
    if not entry:
        return None
    value, loaded_at = entry
    if (time.time() - loaded_at) > SECRET_CACHE_TTL:
        vc._secret_cache.pop((key, folder, project_id), None)
        return None
    return value


def _cache_set(key: str, folder: str, project_id: str, value: str) -> None:
    vc = _get_active_vault_client()
    vc._secret_cache[(key, folder, project_id)] = (value, time.time())


# ---------------------------------------------------------------------------
# Test-only reset — must never be called from production code
# ---------------------------------------------------------------------------

def _reset_client_registry() -> None:
    """
    TEST-ONLY. Reset registry, active client ContextVar, tenant slug ContextVar,
    and startup phase to UNINITIALIZED.

    Every test that calls init_client() must call this in setUp/tearDown
    to prevent state leaking between tests.
    """
    global _client_registry, _startup_phase
    _client_registry = {}
    _active_client_var.set(None)
    _current_tenant_slug_var.set(None)
    _startup_phase = StartupPhase.UNINITIALIZED
