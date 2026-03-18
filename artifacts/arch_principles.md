# Architectural Principles
*Derived from issues encountered across sessions 1–5. Each principle exists because its violation caused a real bug.*

---

## P1 — Fail loudly at the earliest possible moment

If a required precondition is not met, raise immediately with a message that names the precondition and where to fix it. Never proceed in a degraded state. Never silently fall back to a default.

**Violated by:** `init_client()` silently skipping when vars missing (issue 5-6), `_main_project_client()` legacy fallback masking missing init (issues log2-5, log2-6), `VAULT_CFG_KEY_BACKEND` defaulting to `"file"` silently.

**Corollary:** Startup failures must surface at process start, not inside the first request handler.

---

## P2 — Explicit initialization, no implicit state

Every process that uses `adis_secrets` must call `init_client(project_name, manifest_path)` explicitly before any secret access. There is no lazy init, no auto-detect, no fallback client. The library has a formal startup phase; calls made before `READY` raise with a clear message.

**Violated by:** Module-level `get_env()` calls before `init_client()` (issue 5-3, 5-5), `ContextVar` fallback silently using registry without the caller knowing (issue 5-8).

**Corollary:** The startup sequence is a contract, not a convention. It must be documented in code (state machine), not just in the handover doc.

---

## P3 — Use the right tool for each file type

`adis_secrets.read_file()` is for secret-adjacent files that need access control. Plain config files (`.env`, `deploy.config.yml`, `manifest.yml`) must use `Path.read_text()`. Using `read_file()` for config creates circular dependencies and is architecturally wrong.

**Violated by:** `load_env()` using `read_file()` (issue 5-3), `load_deploy_config()` using `read_file()` (issue 5-10).

---

## P4 — No implicit environment inheritance

Every env var a process needs must be injected explicitly. Never assume a var is present because it was set in a parent process, a prior session, or a sibling container. Never rely on `~` expansion inside containers — always inject absolute paths.

**Violated by:** Bootstrap path resolving to `/root/.secrets/` (issue 5-11), `VAULT_CFG_KEY_MANIFEST_PATH` not in `os.environ` (issue 5-5), `VAULT_CFG_KEY_BACKEND` not propagated (issue 5-6).

**Corollary:** `VAULT_CFG_*` config keys are the only keys legitimately written to `os.environ`. All others are either injected at container start or fetched from the vault at runtime.

---

## P5 — Cross-system changes are atomic

Any rename or removal that spans code, manifest, and vault must be completed in full before the session ends. A partial rename is worse than no rename — it causes silent failures that are hard to attribute. Use `da verify` after every rename to confirm end-to-end consistency.

**Violated by:** `DO_TOKEN` rename incomplete across three systems (issue 5-16), tag existing without `pyproject.toml` bump (issue 5-2), `docker-compose.yml` pointing to old manifest path (issue 5-14).

---

## P6 — Module boundaries encode architectural rules

If a rule says "X must not call Y directly", the module structure should make that call impossible or obviously wrong — not just documented. Dependencies flow in one direction. The `adis_secrets` library's internals are not a public API for application code.

**Violated by:** `VaultClient` registry living in `infisical.py` (a backend-specific module), making it easy for agents to put registry logic in the wrong place. `_SecretsFacade` bypassing `ContextVar` and calling legacy fallback directly (issues log2-5).

**Corollary:** `client.py` owns the registry, `ContextVar`, and `_get_active_vault_client()`. Backend modules (`infisical.py`, future `hashicorp.py`) import from `client.py`, never the reverse.

---

## P7 — Workload identity is fixed per process, not configurable

The dev-agent's project name is hardcoded as `"agent-devagent-platform"` in `main.py`. It is never read from the environment. `APP_PROJECT_NAME` is injected by `deploy_runner` into target containers only — it must never appear in `docker-compose.yml`, `.env`, or the dev-agent's environment.

**Violated by:** Cursor agent adding `APP_PROJECT_NAME` to `docker-compose.yml` (issue 5-7).

**Corollary:** Any env var that identifies *which project a process is* is workload identity, not config. Workload identity is set at deploy time by the deployer, not by the process itself.

---

## P8 — Tests must validate the invariants that matter

Test manifests must be as restrictive as production manifests. A `pattern: "*"` in a test manifest disables enforcement and makes the test meaningless. Every test that patches `os.environ` must clean up after itself. Tests must not pass via the wrong code path (e.g. legacy fallback).

**Violated by:** `pattern: "?*"` in test fixtures (issues log2-2), stale key in DO driver test passing silently (issues log2-3), env mutations with no cleanup (issues log2-8).

**Corollary:** One invariant test per repo: call `get_secret()` before `init_client()` → `RuntimeError` with message containing `"init_client"`. This is the canary for startup phase enforcement.

---

## P9 — Every env lookup names its key explicitly at the call site

No generic accessor helpers that accept a key as an argument. Every `get_env()`, `get_secret()`, `os.environ[]` call must have a string literal key visible at the call site. This makes the manifest auditable by grep.

**Violated by:** `_get(key)` dynamic helper in `cli/agent.py` (issue audit-4).

---

## P10 — Validation happens at the read site, not the use site

Path vars are validated as absolute (and container paths as relative to their expected mount point) at the point they are read, not where they are used. URL vars are sanitised for embedded credentials at the read site. This bounds the blast radius of a misconfigured value to one place.

**Violated by:** No `is_absolute()` checks on directory env vars (issue audit-11), path traversal risk in `.pub` derivation (audit-12), `DEV_AGENT_URL` with embedded credentials reaching log output (audit-14).

**Corollary:** Validation is lazy (at call time, not import time) to avoid breaking test imports — but it fires on first use, not silently.
