# AGENTS.md
## Required reading before any code change in this repo

Read this file in full before touching anything. Then read:
- `artifacts/ARCHITECTURE.md` — what the system is and must remain
- `artifacts/PRINCIPLES.md` — why the rules exist (derived from real bugs)

---

## Session start checklist

Before writing any code:

- [ ] Confirm test baselines (see commands below)
- [ ] Re-read invariants I1–I10 in `artifacts/ARCHITECTURE.md`
- [ ] Identify which invariants your change touches
- [ ] If you cannot reconcile a proposed change with an invariant, stop and flag it — do not work around it

---

## The three things you must never do

### 1. Write a secret value anywhere except memory

```python
# WRONG — any of these
os.environ["VAULT_SEC_KEY_ANYTHING"] = value
path.write_text(value)
print(f"token: {value}")
subprocess.run([..., value])
docker build --build-arg TOKEN=value

# RIGHT
value = get_secret("VAULT_SEC_KEY_ANYTHING")  # stays in memory, used directly
```

Only `VAULT_CFG_*` config keys may be written to `os.environ`. Everything else is forbidden. This is invariant I1.

---

### 2. Call `get_secret()`, `get_env()`, or `read_file()` before `init_client()`

```python
# WRONG — at module level or before init_client()
GITSPACE = get_env("CONTAINER_CFG_DIR_GITSPACE", "/gitspace")  # fires at import time

# RIGHT — inline at point of use, inside a function body
def my_function():
    gitspace = get_env("CONTAINER_CFG_DIR_GITSPACE", "/gitspace")
```

The startup phase gate will raise `RuntimeError` if you violate this. Config files (`.env`, `deploy.config.yml`) use `Path.read_text()` — never `read_file()`. This is invariant I2 and principle P3.

---

### 3. Set `APP_PROJECT_NAME` anywhere except `deploy_runner` injecting it into target containers

```python
# WRONG — any of these
# docker-compose.yml:  APP_PROJECT_NAME=agent-devagent-platform
# .env:                APP_PROJECT_NAME=agent-devagent-platform
# os.environ:          os.environ["APP_PROJECT_NAME"] = ...

# RIGHT
# deploy_runner.py injects it via docker run --env for target containers only
# main.py hardcodes the dev-agent's own identity — never reads it from env
```

This is invariant I3. A Cursor agent added this to `docker-compose.yml` in a previous session to fix a crash. That was wrong. The correct fix for "init_client needs a project name" in the dev-agent is to hardcode it.

---

## Naming convention

Every env var key must follow `{LOCATION}_{TYPE}_{KIND}_{NAME}`:

| Segment | Values |
|---|---|
| LOCATION | `HOST`, `CONTAINER`, `VAULT` |
| TYPE | `CFG` (config), `SEC` (secret), `ENV` (env integration) |
| KIND | `KEY` (scalar), `DIR` (directory), `FILE` (file path) |
| NAME | Uppercase descriptive |

Exempt: `HOME`, `PATH`, `APP_PROJECT_NAME`.

A new env var that does not follow this convention is a bug. Renames must be completed atomically across code, manifest, and vault in the same session — use `da verify` to confirm end-to-end consistency after any rename.

---

## Module boundary you must not cross

```
client.py    ← owns: VaultClient, registry, ContextVar, StartupPhase, _assert_ready()
infisical.py ← owns: InfisicalClient, init_client(), _load_bootstrap_credentials()
```

`client.py` has zero imports from `infisical.py` or any backend module. If you add logic to `client.py` that requires importing from `infisical.py`, you are breaking the boundary. Move the logic to `infisical.py` instead.

Future backends (`hashicorp.py` etc.) import from `client.py` — they do not reimplement registry or ContextVar logic.

---

## Manifest rules

Every `get_secret()`, `get_env()`, and `read_file()` call is checked against `manifest.yml` before execution. If you add a new secret or env var access:

1. Add the key to `manifest.yml` first
2. Then add the call in code
3. Run `da verify` to confirm

No `pattern: "*"` or `pattern: "?*"` in any manifest — test manifests included. Pattern entries must have a `note` field.

---

## After every change

```bash
# adis-secrets
cd ~/gitspace/adis-secrets
python -m pytest tests/ -v
# Expected: 31 passed

# agent-devagent-platform
cd ~/Github/agent-devagent-platform
PYTHONPATH="/Users/nandakumarp/gitspace/adis-secrets" \
  VAULT_CFG_KEY_BACKEND=infisical \
  python -m pytest tests/ -v
# Expected: 34 passed

# Verify vault connectivity end-to-end
da verify
da verify agent-slackbot-multitenant
```

If any test fails, stop. Report the full traceback. Do not proceed to the next change.

---

## Cross-system changes (renames, removals)

Any change that spans code + manifest + vault must be completed atomically in the same session:

1. Rename in code
2. Rename in `manifest.yml`
3. Rename in Infisical dashboard
4. Run `da verify` — must show PASS before the session ends

A partial rename is worse than no rename. If you cannot complete all three steps, revert.

---

## If you are about to do something that feels like a workaround

Stop. The correct fix is almost always one of:
- Move the call inside a function body (not module level)
- Use `Path.read_text()` instead of `read_file()` for config files
- Hardcode the identity value instead of reading it from an env var
- Add the key to the manifest before making the call

If none of these apply, flag it for architectural review before proceeding.
