#!/usr/bin/env python3
# LEGACY: This script tests the slug-based routing system (TENANT_SLUGS /
# get_tenant_slug / set_tenant_context) which has been superseded by direct
# /tenants/{tenant_id} lookups via TenantSecretsManager. Tests [9]-[10] that
# exercise get_tenant_slug and set_tenant_context will fail against the current
# library — they are preserved here for historical reference only.
#
# Usage:
#   APP_PROJECT_NAME=agent-slackbot-multitenant python verify_infisical.py
import os
import sys
import time
from pathlib import Path

# verify_infisical.py is a dev tool, not application code.
# Hardcoded path here is intentional — this script is only ever run locally.
os.chdir(os.path.expanduser("~/gitspace/agent-slackbot-multitenant"))

from adis_secrets import (  # noqa: E402
    clear_tenant_context,
    get_config,
    get_secret,
    get_tenant_slug,
    load_env_file,
    set_tenant_context,
)
from adis_secrets.reader import resolve_bootstrap_secrets_file  # noqa: E402
from adis_secrets.backends.infisical import (  # noqa: E402
    _get_client,
    get_tenant_context,
    invalidate_slug_cache,
)


def _fmt_line(idx: int, label: str, status: str, detail: str | None = None):
    left = f"[{idx:>2}/11] {label} "
    dots = "." * max(1, 40 - len(left))
    line = f"{left}{dots} {status}"
    if detail:
        line += f" — {detail}"
    print(line)


def _abort(idx: int, label: str, detail: str):
    _fmt_line(idx, label, "FAIL", detail)
    print(
        "[ABORT] Fix the above before continuing. Re-run: "
        "APP_PROJECT_NAME=agent-slackbot-multitenant python verify_infisical.py"
    )
    sys.exit(1)


def _secret_has_value(secret_obj) -> bool:
    if hasattr(secret_obj, "secret_value"):
        return bool(secret_obj.secret_value)
    if isinstance(secret_obj, dict):
        value = secret_obj.get("secretValue") or secret_obj.get("secret_value")
        if value:
            return True
        inner = secret_obj.get("secret")
        if isinstance(inner, dict):
            return bool(inner.get("secretValue") or inner.get("secret_value"))
    return False


def main():
    # [1/11]
    try:
        path = Path(resolve_bootstrap_secrets_file())
    except Exception as exc:
        _abort(1, "Secrets file readable", f"{type(exc).__name__}: {exc}")
    if not path.exists():
        _abort(1, "Secrets file readable", f"File does not exist: {path}")
    if not os.access(path, os.R_OK):
        _abort(1, "Secrets file readable", f"File is not readable: {path}")
    try:
        loaded = load_env_file(str(path))
    except Exception as exc:
        _abort(1, "Secrets file readable", f"{type(exc).__name__}: {exc}")
    if not loaded:
        _abort(1, "Secrets file readable", "Secrets file is empty")
    _fmt_line(1, "Secrets file readable", "OK", f"{len(loaded)} keys found")

    # [2/11]
    required = [
        "VAULT_CFG_KEY_BACKEND",
        "VAULT_SEC_KEY_INFISICAL_CLIENT_ID",
        "VAULT_SEC_KEY_INFISICAL_CLIENT_SECRET",
    ]
    missing = []
    for name in required:
        present = name in loaded and bool(loaded.get(name))
        print(f"      - {name}: {'PRESENT' if present else 'MISSING'}")
        if not present:
            missing.append(name)
    if missing:
        _abort(2, "Required secrets present", f"Missing keys: {', '.join(missing)}")
    _fmt_line(2, "Required secrets present", "OK")

    # JUSTIFIED EXCEPTION: verify_infisical.py is a local-only dev tool.
    # The adis_secrets library dispatches on VAULT_CFG_KEY_BACKEND from
    # os.environ — there is no config-only path without a library refactor.
    # We use setdefault so an already-set value is never overwritten, and
    # the value comes from the bootstrap file (a config key, not a secret).
    os.environ.setdefault(
        "VAULT_CFG_KEY_BACKEND",
        loaded.get("VAULT_CFG_KEY_BACKEND", "infisical"),
    )

    # [3/11]
    cfg_keys = [
        "infisical_project_id",
        "infisical_environment",
    ]
    missing_cfg = []
    for name in cfg_keys:
        value = get_config(name)
        present = value is not None
        print(f"      - {name}: {'PRESENT' if present else 'MISSING'}")
        if not present:
            missing_cfg.append(name)
    if missing_cfg:
        _abort(3, "Required config present", f"Missing config keys: {', '.join(missing_cfg)}")
    _fmt_line(3, "Required config present", "OK")

    infisical_project_id = str(get_config("infisical_project_id"))
    infisical_environment = str(get_config("infisical_environment"))

    # [4/11]
    try:
        client = _get_client()
    except Exception as exc:
        _abort(4, "Auth", f"{type(exc).__name__}: {exc}")
    _fmt_line(4, "Auth", "OK", "Infisical client authenticated")

    # [5/11]
    try:
        secret = client.secrets.get_secret_by_name(
            secret_name="VAULT_SEC_KEY_SLACK_SIGNING_SECRET",
            project_id=infisical_project_id,
            environment_slug=infisical_environment,
            secret_path="/app",
        )
        if not _secret_has_value(secret):
            raise KeyError("VAULT_SEC_KEY_SLACK_SIGNING_SECRET empty in /app")
    except Exception as exc:
        _abort(5, "Read /app", f"{type(exc).__name__}: {exc}")
    _fmt_line(5, "Read /app", "OK")

    # [6/11]
    try:
        secret = client.secrets.get_secret_by_name(
            secret_name="VAULT_SEC_KEY_ANTHROPIC_API_KEY",
            project_id=infisical_project_id,
            environment_slug=infisical_environment,
            secret_path="/app",
        )
        if not _secret_has_value(secret):
            raise KeyError("VAULT_SEC_KEY_ANTHROPIC_API_KEY empty in /app")
    except Exception as exc:
        _abort(6, "Read /app", f"{type(exc).__name__}: {exc}")
    _fmt_line(6, "Read /app", "OK")

    # [7/11]
    try:
        secret = client.secrets.get_secret_by_name(
            secret_name="VAULT_SEC_KEY_SLACK_BOT_TOKEN",
            project_id=infisical_project_id,
            environment_slug=infisical_environment,
            secret_path="/applieddisruption",
        )
        if not _secret_has_value(secret):
            raise KeyError("VAULT_SEC_KEY_SLACK_BOT_TOKEN empty in /applieddisruption")
    except Exception as exc:
        _abort(7, "Read /applieddisruption", f"{type(exc).__name__}: {exc}")
    _fmt_line(7, "Read /applieddisruption", "OK")

    # [8/11]
    try:
        clear_tenant_context()
        value = get_secret("VAULT_SEC_KEY_ANTHROPIC_API_KEY")
        if not value:
            raise RuntimeError("Empty value returned")
    except Exception as exc:
        _abort(8, "Layered resolution (no tenant)", f"{type(exc).__name__}: {exc}")
    _fmt_line(8, "Layered resolution (no tenant)", "OK")

    # [9/11]
    try:
        set_tenant_context("applieddisruption")
        value = get_secret("VAULT_SEC_KEY_SLACK_BOT_TOKEN")
        if not value:
            raise RuntimeError("Empty value returned")
        clear_tenant_context()
        if get_tenant_context() is not None:
            raise AssertionError("Tenant context not cleared")
    except Exception as exc:
        _abort(9, "Layered resolution (tenant)", f"{type(exc).__name__}: {exc}")
    _fmt_line(9, "Layered resolution (tenant)", "OK")

    # [10/11]
    try:
        slug1 = get_tenant_slug("T09PNTTSM7Z")
        if slug1 != "applieddisruption":
            raise AssertionError(f"FAIL — got: {slug1}")
        slug2 = get_tenant_slug("T0AGE0ZRZFF")
        if slug2 != "invis":
            raise AssertionError(f"FAIL — got: {slug2}")
        slug3 = get_tenant_slug("UNKNOWN_TEAM")
        if slug3 != "UNKNOWN_TEAM":
            raise AssertionError(f"FAIL — got: {slug3}")
        invalidate_slug_cache()
        slug4 = get_tenant_slug("T09PNTTSM7Z")
        if slug4 != "applieddisruption":
            raise AssertionError(f"FAIL — got: {slug4}")
    except Exception as exc:
        _abort(10, "Tenant slug cache", f"{type(exc).__name__}: {exc}")
    _fmt_line(10, "Tenant slug cache", "OK", "all slug lookups correct")

    # [11/11]
    try:
        t1_start = time.perf_counter()
        v1 = get_secret("VAULT_SEC_KEY_SLACK_SIGNING_SECRET")
        t1 = time.perf_counter() - t1_start
        if not v1:
            raise RuntimeError("First call returned empty value")

        t2_start = time.perf_counter()
        v2 = get_secret("VAULT_SEC_KEY_SLACK_SIGNING_SECRET")
        t2 = time.perf_counter() - t2_start
        if not v2:
            raise RuntimeError("Second call returned empty value")
        if t2 > (t1 / 10):
            raise AssertionError(
                f"second call not significantly faster (first={t1:.4f}s, second={t2:.4f}s)"
            )
    except Exception as exc:
        _abort(11, "Cache performance", f"{type(exc).__name__}: {exc}")
    _fmt_line(
        11,
        "Cache performance",
        "OK",
        f"first: {t1:.4f}s, second: {t2:.4f}s (cache hit confirmed)",
    )

    print("")
    print("[PASS] All 11 checks passed — Infisical backend ready to integrate")


if __name__ == "__main__":
    main()
