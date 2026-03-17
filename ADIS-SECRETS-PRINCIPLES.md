# ADIS-SECRETS Principles

## `VAULT_CFG_KEY_MANIFEST_PATH`
- It is required in every container alongside `VAULT_CFG_KEY_BACKEND`
- It must be an absolute path to the project's `manifest.yml`
- It is injected by the deploy runner, never set manually
- The repo copy of `manifest.yml` is source of truth; the `~/.secrets/` copy is what the container reads at runtime via the bind mount
