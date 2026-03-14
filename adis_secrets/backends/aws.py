_MSG = (
    "AWS Secrets Manager backend not yet implemented. "
    "Set VAULT_CFG_KEY_BACKEND=file for local/DO deployments."
)


def write_tenant_token(team_id: str, token_data: dict) -> None:
    raise NotImplementedError(_MSG)


def get_tenant_token(team_id: str) -> dict | None:
    raise NotImplementedError(_MSG)
