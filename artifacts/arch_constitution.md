# Architectural Constitution
## AppliedDisruption Agent Platform

*This document describes the intended architecture of the system. It is prescriptive, not descriptive — it defines what the system must be, not just what it currently is. All implementation decisions must be consistent with it. Where current code conflicts with this document, the document wins.*

---

## 1. System Layers

The system has three layers. Dependencies flow downward only. No layer imports from or calls into a layer above it.

```
┌─────────────────────────────────────────────┐
│           Target Workloads                  │
│  (slackbot, future agents)                  │
│  — deployed by dev-agent                    │
│  — each has its own identity and VaultClient│
├─────────────────────────────────────────────┤
│           Dev-Agent Platform                │
│  (CLI, deploy runner, provisioner)          │
│  — runs on operator machine or cloud VM     │
│  — orchestrates workload lifecycle          │
├─────────────────────────────────────────────┤
│           adis_secrets Library              │
│  (vault client, manifest enforcement,       │
│   bootstrap, startup phase gate)            │
│  — used by all layers above                 │
│  — has no knowledge of any workload         │
└─────────────────────────────────────────────┘
```

**adis_secrets** owns: vault backend abstraction, manifest enforcement, bootstrap file resolution, startup phase state, secret cache, tenant context isolation.

**Dev-agent platform** owns: CLI surface (`da`), container lifecycle (build, deploy, teardown), provisioning, cross-project operations (`da verify`). Uses `adis_secrets` as a library — never bypasses it.

**Target workloads** own: their application logic. Each workload uses `adis_secrets` independently. The dev-agent deploys them but shares no process, no `VaultClient`, and no secrets context with them.

---

## 2. Identity Model

Every process has exactly one project identity. Identity is fixed at startup and never changes.

| Process | How identity is set | Who sets it |
|---|---|---|
| Dev-agent | Hardcoded in `main.py` | The codebase itself |
| Target container | `APP_PROJECT_NAME` injected at container start | `deploy_runner` |
| CLI (`da` commands) | Derived from `__file__` path or explicit argument | `agent.py` startup |

**Rules:**
- No process reads its own identity from a user-supplied env var at runtime.
- `APP_PROJECT_NAME` is workload identity. It must never appear in `docker-compose.yml`, `.env`, or any file controlled by the operator. It is injected by the deployer into target containers only.
- A process may operate on behalf of another project (e.g. `da verify <project>`) only by explicitly changing context — never by inheriting ambient state.

---

## 3. Storage Topology

Four storage locations. Each has a defined owner, a defined lifecycle, and defined contents.

### 3.1 Vault (Infisical, or any conforming backend)
- **Owns:** All secret values. All tenant tokens.
- **Lifecycle:** Persistent. Managed by operators via Infisical dashboard or `da` tooling.
- **Access:** Via `get_secret()` only. Never read directly. Never written to disk or `os.environ`.
- **Structure:** One Infisical project per workload. Secrets organised by environment and folder. Folder structure is defined per-project and must match the manifest.

### 3.2 Manifest (`manifest.yml`, one per repo)
- **Owns:** The access policy — which secrets, env vars, and file paths a project is permitted to access.
- **Lifecycle:** Baked into Docker images at build time (`COPY manifest.yml ./manifest.yml`). Never copied to `~/.secrets/` at runtime.
- **Access:** Read once at `init_client()` time, cached in memory. Never re-read from disk after startup.
- **Enforcement:** Every `get_secret()`, `get_env()`, and `read_file()` call is checked against the manifest before forwarding to the backend. A key not declared in the manifest raises `PermissionError`. A missing manifest raises `EnvironmentError` at startup.

### 3.3 Bootstrap file (`~/.secrets/<project>-secrets.env`)
- **Owns:** The three credentials needed to authenticate with the vault: `VAULT_CFG_KEY_BACKEND`, `VAULT_SEC_KEY_<BACKEND>_CLIENT_ID`, `VAULT_SEC_KEY_<BACKEND>_CLIENT_SECRET`.
- **Lifecycle:** Written once by the operator. Never created or modified by tooling. Never more than 3 lines.
- **Access:** Read once by `init_client()` via `_load_bootstrap_credentials()`. Never re-read. Content never written to `os.environ` or disk.
- **Scope:** Local and dev/test environments only. Production uses machine identity (no bootstrap file).
- **Path:** Always injected explicitly via `VAULT_CFG_KEY_SECRETS_PATH`. Never derived from `~` inside a container.

### 3.4 Host config (`.env`)
- **Owns:** Non-secret runtime configuration for the dev-agent host: paths, ports, region, backend selector.
- **Lifecycle:** Written by `da install`. Never contains secret values. Read by `load_env()` using `Path.read_text()` — never `adis_secrets.read_file()`.
- **Keys:** Must follow `{LOCATION}_{TYPE}_{KIND}_{NAME}` convention. Only `VAULT_CFG_*` keys from this file are written to `os.environ`. All others are consumed internally.

---

## 4. Secret Lifecycle

A secret has exactly one permitted path through the system:

```
Infisical vault
  → get_secret() call
  → in-memory cache (TTL 300s, never persisted)
  → consumed by caller in memory
  → never written to: os.environ, disk, logs, API responses, build args
```

**Permitted destinations for secret values:**
- A subprocess environment constructed explicitly for that subprocess (e.g. `ANTHROPIC_API_KEY` passed to `claude_runner.py` via a minimal dict — not the full `os.environ`).
- A BuildKit `--secret` mount (never `--build-arg`).
- A tmpfile with `0600` permissions that is unlinked immediately after use (SSH deploy key only, future item).

**Forbidden destinations (hard rules):**
- `os.environ` — only `VAULT_CFG_*` config keys may be written here.
- Any file on disk except the operator-written bootstrap file.
- Any log output, print statement, or API response.
- Docker build args.

---

## 5. Startup Phase Contract

Every process using `adis_secrets` must pass through these phases in order before any secret or env access:

```
UNINITIALIZED
  → load_env() / Path.read_text()     # read host config — no adis_secrets involvement
  → set VAULT_CFG_* in os.environ     # VAULT_CFG_* only
  → init_client(project_name,         # reads bootstrap, connects to vault,
                manifest_path)        # loads manifest, transitions to READY
READY
  → get_secret() / get_env() /        # all calls validated against manifest
    read_file()
```

Any call to `get_secret()`, `get_env()`, or `read_file()` before `READY` raises `RuntimeError("adis_secrets not initialised. Call init_client(project_name, manifest_path) before accessing secrets.")`.

`init_client()` must raise — never skip, never warn — if `project_name` or `manifest_path` is missing or if the bootstrap file cannot be found.

---

## 6. Access Control Model

The manifest is the sole access policy. There are no other gates.

**Manifest structure:**
```yaml
secrets:        # keys fetchable via get_secret()
env:            # keys fetchable via get_env()
files:          # paths fetchable via read_file()
  - path: /explicit/path          # exact match
  - directory_prefix: /dir/       # startswith match only — no globs
    note: "reason this dir is needed"
```

**Rules:**
- No `*` or glob patterns in `secrets` or `env` entries.
- No `*` in `files` path entries. `directory_prefix` uses `startswith` only.
- Pattern entries (if used) must have a `note` field.
- Test manifests must be as restrictive as production manifests. `pattern: "*"` or `pattern: "?*"` in a test manifest is a bug.

**Legitimate escape hatch:**
`_get_env_unchecked()` reads directly from `os.environ` without manifest enforcement. It exists solely for the bootstrap reads that must happen before the manifest is loaded (`VAULT_CFG_KEY_MANIFEST_PATH`, `VAULT_CFG_KEY_BACKEND`, `VAULT_CFG_KEY_SECRETS_PATH`, `APP_PROJECT_NAME`, vault credentials). It must never be used outside `reader.py` and `manifest.py`.

---

## 7. Vault Backend Interface

The vault layer is pluggable. Any backend must implement the following interface. The registry, `ContextVar`, and startup phase gate are backend-agnostic and live in `client.py` — never in a backend module.

```python
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
```

**Module structure:**
```
adis_secrets/
  client.py          ← VaultClient, _client_registry, _active_client_var,
                       _get_active_vault_client(), startup phase state
  backends/
    infisical.py     ← InfisicalClient, _load_bootstrap_credentials()
    hashicorp.py     ← future
  reader.py          ← get_secret(), get_env(), read_file() — public API
  manifest.py        ← manifest loading, enforcement
  writer.py          ← write_secret(), write_tenant_token()
```

**Dependency rule:** backend modules import from `client.py`. `client.py` does not import from any backend module. `reader.py` and `writer.py` call `_get_active_vault_client()` from `client.py` — they do not import backend modules directly.

---

## 8. Deploy Target Portability

A workload must be deployable to any target environment without code changes. Environment-specific values are injected at deploy time — never hardcoded.

**What varies by target:**
- `VAULT_CFG_KEY_SECRETS_PATH` — absolute path to bootstrap file on the target
- `VAULT_CFG_KEY_MANIFEST_PATH` — absolute path to manifest in the container (always `/app/manifest.yml`)
- `VAULT_CFG_KEY_BACKEND` — vault backend selector
- `APP_PROJECT_NAME` — workload identity

**What must not vary:** The workload image. The same image is deployed to local, staging, and production. Environment differences are entirely in injected config, not in the image.

**Deploy target contract:** Any deploy target (local Docker, DigitalOcean, future Kubernetes) is supported if `deploy_runner` can:
1. Build the image (or pull it from a registry).
2. Inject the four `VAULT_CFG_*` + `APP_PROJECT_NAME` env vars at container start.
3. Bind-mount or otherwise provide the bootstrap file at `VAULT_CFG_KEY_SECRETS_PATH`.

**Machine identity (production):** On supported cloud targets (DigitalOcean, future), `_load_bootstrap_credentials()` detects the cloud environment via the instance metadata API and authenticates via machine identity instead of the bootstrap file. The bootstrap file is not present in production. No other change to the startup phase or access control model.

---

## 9. Naming Convention

All environment variable keys must follow:

```
{LOCATION}_{TYPE}_{KIND}_{NAME}
```

| Segment | Values | Meaning |
|---|---|---|
| LOCATION | `HOST`, `CONTAINER`, `VAULT` | Where this var lives or is owned |
| TYPE | `CFG`, `SEC`, `ENV` | Config (non-secret), Secret, Env integration |
| KIND | `KEY`, `DIR`, `FILE` | Scalar, directory path, file path |
| NAME | Uppercase descriptive | What it is |

**Exempt:** `HOME`, `PATH` (OS-provided), `APP_PROJECT_NAME` (workload identity — fixed format by convention).

**Enforcement:** Any new env var that does not follow this convention is a bug. Renames must be completed atomically across code, manifest, and vault in a single session.

---

## 10. Invariants

These must hold at all times. A change that violates any of these is not permitted regardless of other justification.

| # | Invariant |
|---|---|
| I1 | No secret value ever appears in `os.environ`, on disk, in logs, in API responses, or in build args |
| I2 | `init_client()` is called exactly once per process before any secret or env access |
| I3 | `APP_PROJECT_NAME` never appears in `docker-compose.yml`, `.env`, or any operator-controlled file |
| I4 | The same workload image runs in all environments — no environment-specific images |
| I5 | Every `get_secret()` / `get_env()` / `read_file()` call names its key as a string literal at the call site |
| I6 | `_get_env_unchecked()` is called only from `reader.py` and `manifest.py` |
| I7 | No `--build-arg` for secrets — BuildKit `--secret` only |
| I8 | Manifests are baked into images — no runtime manifest copy in `~/.secrets/` |
| I9 | `client.py` does not import from any backend module |
| I10 | Bootstrap file is exactly 3 lines — never created or modified by tooling |
