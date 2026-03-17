# adis-secrets

Shared secrets and config access package for local Docker and SSH deployments.

## API

- `get_secret(key)` reads from `VAULT_CFG_KEY_SECRETS_PATH`, or defaults via `APP_PROJECT_NAME` to `~/.secrets/<project>-secrets.env`.
- `get_config(key, default)` reads `deploy.config.yml` under `config:`.
- `write_tenant_token(team_id, token_data)` writes token to backend.
- `get_tenant_token(team_id)` reads token from backend.

## Backends

- `file` backend is implemented.
- `aws` and `gcp` backends are placeholders.

## Environment Variables Naming Convention

All environment variables across projects using `adis-secrets` must strictly follow this naming convention:

`{LOCATION}_{TYPE}_{KIND}_{NAME}`

- **LOCATION:** `HOST` (host machine), `CONTAINER` (inside docker), `VAULT` (secrets manager)
- **TYPE:** `CFG` (configuration), `SEC` (secret), `ENV` (environment mapping)
- **KIND:** `KEY` (scalar value), `DIR` (directory path), `FILE` (file path)
- **NAME:** Descriptive uppercase identifier

**Exemptions:**
- OS-provided: `HOME`, `PATH`
- Project Identity: `APP_PROJECT_NAME` (workload identity domain prefix)

*Example compliant keys:*
`HOST_CFG_DIR_GITSPACE`
`CONTAINER_ENV_FILE_SSH_KEY`
`VAULT_CFG_KEY_BACKEND`
