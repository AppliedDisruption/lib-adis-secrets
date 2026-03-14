# adis-secrets

Shared secrets and config access package for local Docker and SSH deployments.

## API

- `get_secret(key)` reads from `CONTAINER_ENV_FILE_APP_SECRETS`.
- `get_config(key, default)` reads `deploy.config.yml` under `config:`.
- `write_tenant_token(team_id, token_data)` writes token to backend.
- `get_tenant_token(team_id)` reads token from backend.

## Backends

- `file` backend is implemented.
- `aws` and `gcp` backends are placeholders.
