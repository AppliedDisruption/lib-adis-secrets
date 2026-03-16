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
