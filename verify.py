#!/usr/bin/env python3
"""
Verification script for adis-secrets migration.
Usage:
  python verify.py --layer static
  python verify.py --layer unit
  python verify.py --layer mounts --container <name>
  python verify.py --layer da
  python verify.py --layer all --container <name>
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
import tokenize
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Counts:
    passed: int = 0
    failed: int = 0
    warned: int = 0


def _print(status: str, check_name: str, message: str | None = None) -> None:
    if message:
        print(f"{status}  {check_name} — {message}")
    else:
        print(f"{status}  {check_name}")


def _run(cmd: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        shell=True,
        text=True,
        capture_output=True,
    )


def _py_files_under(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def _tokens_without_comments(path: Path) -> str:
    src = path.read_text(encoding="utf-8")
    toks = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            continue
        toks.append(tok.string)
    return " ".join(toks)


def _first_match_line(path: Path, pattern: str) -> int:
    rx = re.compile(pattern)
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if rx.search(line):
            return idx
    return 1


def _check(
    counts: Counts,
    ok: bool,
    name: str,
    fail_msg: str | None = None,
    warn: bool = False,
) -> None:
    if warn:
        counts.warned += 1
        _print("WARN", name, fail_msg)
        return
    if ok:
        counts.passed += 1
        _print("PASS", name)
    else:
        counts.failed += 1
        _print("FAIL", name, fail_msg or "runtime:0: failed")


def run_static_layer() -> Counts:
    counts = Counts()
    roots = [
        Path("~/gitspace/adis-secrets/adis_secrets").expanduser(),
        Path("~/gitspace/agent-slackbot-multitenant").expanduser(),
        Path("~/Github/agent-devagent-platform/app").expanduser(),
        Path("~/LocalProjects/test_project").expanduser(),
    ]
    py_files: list[Path] = []
    token_cache: dict[Path, str] = {}
    for root in roots:
        py_files.extend(_py_files_under(root))
    for path in py_files:
        token_cache[path] = _tokens_without_comments(path)

    old_names = [
        "APP_SECRETS_FILE",
        "ENV_FILE",
        "LOCAL_CONTAINER_SECRETS_PATH",
        "PROJECT_SECRETS_DIR",
        "GITSPACE_DIR",
        "LOCAL_PROJECTS_DIR",
        "SECRETS_BACKEND",
        "HEALTH_CHECK_RETRIES",
        "HEALTH_CHECK_DELAY",
        "PROD_SERVER_HOST",
        "TEST_SERVER_HOST",
        "STAGING_SERVER_HOST",
        "REMOTE_SECRETS_PATH",
        "SECRET_LOADER",
        "secret_loader",
    ]
    for name in old_names:
        found = None
        for path, content in token_cache.items():
            if re.search(rf"\b{re.escape(name)}\b", content):
                found = path
                break
        if found:
            line = _first_match_line(found, re.escape(name))
            _check(
                counts,
                False,
                f"static.old_name.{name}",
                f"{found}:{line}: old variable/import name detected",
            )
        else:
            _check(counts, True, f"static.old_name.{name}")

    wrong_tier_patterns = [
        ("os.environ.vault_sec.slack_bot", r"os\.environ.*SLACK_BOT"),
        ("os.environ.vault_sec.anthropic", r"os\.environ.*ANTHROPIC"),
        ("os.environ.vault_sec.signing_secret", r"os\.environ.*SIGNING_SECRET"),
        ("os.environ.vault_sec.client_secret", r"os\.environ.*CLIENT_SECRET"),
        ("os.environ.vault_sec.github_token", r"os\.environ.*GITHUB_TOKEN"),
        ("get_secret.cfg.model", r"get_secret.*[Mm]odel"),
        ("get_secret.cfg.history", r"get_secret.*[Hh]istory"),
        ("get_secret.cfg.app_env", r"get_secret.*APP_ENV"),
    ]
    for check_name, pattern in wrong_tier_patterns:
        found = None
        for path, content in token_cache.items():
            if re.search(pattern, content):
                found = path
                break
        if found:
            line = _first_match_line(found, pattern)
            _check(
                counts,
                False,
                f"static.wrong_tier.{check_name}",
                f"{found}:{line}: wrong tier access pattern",
            )
        else:
            _check(counts, True, f"static.wrong_tier.{check_name}")

    hardcoded_path_patterns = [
        ("hardcoded.users", r"/Users/"),
        ("hardcoded.home_nandakumarp", r"/home/nandakumarp"),
        ("hardcoded.secrets_env", r"/\.secrets/secrets\.env"),
    ]
    for check_name, pattern in hardcoded_path_patterns:
        found = None
        for path, content in token_cache.items():
            if re.search(pattern, content):
                found = path
                break
        if found:
            line = _first_match_line(found, pattern)
            _check(
                counts,
                False,
                f"static.{check_name}",
                f"{found}:{line}: hardcoded path detected",
            )
        else:
            _check(counts, True, f"static.{check_name}")

    deploy_runner = Path("~/Github/agent-devagent-platform/app/deploy_runner.py").expanduser()
    deploy_runner_text = deploy_runner.read_text(encoding="utf-8") if deploy_runner.exists() else ""
    if "CONTAINER_ENV_FILE_APP_SECRETS" not in deploy_runner_text:
        _check(
            counts,
            True,
            "static.warn.container_env_file_present",
            "CONTAINER_ENV_FILE_APP_SECRETS not in deploy_runner.py",
            warn=True,
        )
    else:
        _check(counts, True, "static.warn.container_env_file_present")

    if "VAULT_CFG_KEY_BACKEND" not in deploy_runner_text:
        _check(
            counts,
            True,
            "static.warn.backend_key_present",
            "VAULT_CFG_KEY_BACKEND not in deploy_runner.py",
            warn=True,
        )
    else:
        _check(counts, True, "static.warn.backend_key_present")

    deploy_configs = [
        Path("~/gitspace/agent-slackbot-multitenant/deploy.config.yml").expanduser(),
        Path("~/LocalProjects/test_project/deploy.config.yml").expanduser(),
        Path("~/Github/agent-devagent-platform/deploy.config.yml").expanduser(),
    ]
    combined_cfg = "\n".join(
        p.read_text(encoding="utf-8") for p in deploy_configs if p.exists()
    )
    if "environments:" not in combined_cfg:
        _check(
            counts,
            True,
            "static.warn.environments_present",
            "environments: not in a deploy.config.yml",
            warn=True,
        )
    else:
        _check(counts, True, "static.warn.environments_present")

    if "deploy_mode:" not in combined_cfg:
        _check(
            counts,
            True,
            "static.warn.deploy_mode_present",
            "deploy_mode: not in a deploy.config.yml",
            warn=True,
        )
    else:
        _check(counts, True, "static.warn.deploy_mode_present")

    return counts


def run_unit_layer() -> Counts:
    counts = Counts()
    repo = Path("~/gitspace/adis-secrets").expanduser()
    proc = _run(f"{sys.executable} -m pytest tests/ -v --tb=short", cwd=repo)
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    matched = False
    for line in output.splitlines():
        m = re.search(r"^(tests/\S+::\S+)\s+(PASSED|FAILED)", line.strip())
        if not m:
            continue
        matched = True
        test_name, status = m.group(1), m.group(2)
        if status == "PASSED":
            _check(counts, True, test_name)
        else:
            _check(counts, False, test_name, "runtime:0: test failed")
    if not matched:
        _check(
            counts,
            proc.returncode == 0,
            "unit.pytest.run",
            f"runtime:0: pytest output parse failed\n{output.strip()}",
        )
    return counts


def _project_name_from_container(container: str) -> str:
    if "test-project" in container or "test_project" in container:
        return "test_project"
    return "agent-slackbot-multitenant"


def run_mounts_layer(container: str) -> Counts:
    counts = Counts()
    project = _project_name_from_container(container)

    check1 = _run(f"docker exec {container} ls /.secrets/")
    has_env = bool(re.search(r"\S+-secrets\.env", check1.stdout or ""))
    _check(
        counts,
        check1.returncode == 0 and has_env,
        "mounts.secrets_dir_mounted",
        f"runtime:0: expected *-secrets.env in /.secrets, got: {(check1.stdout or '').strip()}",
    )

    check2 = _run(
        f"docker exec {container} sh -c \"touch /.secrets/.write_test && rm /.secrets/.write_test\""
    )
    _check(
        counts,
        check2.returncode == 0,
        "mounts.secrets_dir_writable",
        f"runtime:0: {check2.stderr.strip()}",
    )

    check3 = _run(
        f"docker exec {container} sh -c \"cat \\$CONTAINER_ENV_FILE_APP_SECRETS | grep -c =\""
    )
    count = int((check3.stdout or "0").strip() or "0") if check3.returncode == 0 else 0
    _check(
        counts,
        check3.returncode == 0 and count > 0,
        "mounts.container_env_file_set",
        "runtime:0: CONTAINER_ENV_FILE_APP_SECRETS missing or empty",
    )

    check4 = _run(f"docker exec {container} sh -c \"echo \\$VAULT_CFG_KEY_BACKEND\"")
    _check(
        counts,
        check4.returncode == 0 and (check4.stdout or "").strip() == "file",
        "mounts.backend_set",
        f"runtime:0: expected 'file', got '{(check4.stdout or '').strip()}'",
    )

    check5 = _run(
        "docker exec {c} python -c \"from adis_secrets import get_secret; "
        "k = get_secret('VAULT_SEC_KEY_SLACK_SIGNING_SECRET'); "
        "assert k and not k.startswith('your-'), 'placeholder value — update secrets file'; "
        "print('PASS')\"".format(c=container)
    )
    _check(
        counts,
        check5.returncode == 0,
        "mounts.get_secret_works",
        f"runtime:0: {(check5.stderr or check5.stdout).strip()}",
    )

    cfg_key = "app_name" if project == "test_project" else "model"
    check6 = _run(
        "docker exec {c} python -c \"from adis_secrets import get_config; "
        "m = get_config('{k}'); assert m, '{k} not in deploy.config.yml config block'; "
        "print('PASS {k}=' + str(m))\"".format(c=container, k=cfg_key)
    )
    _check(
        counts,
        check6.returncode == 0,
        "mounts.get_config_works",
        f"runtime:0: {(check6.stderr or check6.stdout).strip()}",
    )

    check7 = _run(
        "docker exec {c} python -c \"from adis_secrets import write_tenant_token; "
        "write_tenant_token('TEST_TEAM_VERIFY', {{'access_token': 'test-verify-token'}}); print('PASS')\"".format(
            c=container
        )
    )
    host_file = (
        Path("~/.secrets/project-secrets").expanduser()
        / project
        / "tenant_tokens.json"
    )
    host_ok = False
    if host_file.exists():
        try:
            data = json.loads(host_file.read_text(encoding="utf-8"))
            host_ok = "TEST_TEAM_VERIFY" in data
            if host_ok:
                data.pop("TEST_TEAM_VERIFY", None)
                host_file.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except Exception:
            host_ok = False
    _check(
        counts,
        check7.returncode == 0 and host_ok,
        "mounts.tenant_tokens_lands_on_host",
        f"runtime:0: token write/check failed for {host_file}",
    )

    check8 = _run(f"docker logs {container} 2>&1")
    leaked = re.search(r"(xoxb-|sk-ant-|your-signing|your-token)", check8.stdout or "", re.IGNORECASE)
    _check(
        counts,
        check8.returncode == 0 and not leaked,
        "mounts.no_secret_values_in_logs",
        "runtime:0: found possible secret values in logs",
    )

    return counts


def run_da_layer() -> Counts:
    counts = Counts()
    repo = Path("~/Github/agent-devagent-platform").expanduser()

    checks = [
        ("da.doctor", f"{sys.executable} app/agent.py doctor", "no_traceback", None),
        ("da.doctor.test_project", f"{sys.executable} app/agent.py doctor --local test_project", "no_traceback", None),
        ("da.deploy.test_project", f"{sys.executable} app/agent.py deploy --local test_project --env test", "exit_and_contains", "healthy"),
        ("da.status.test_project", f"{sys.executable} app/agent.py status --local test_project --env test", "no_traceback", None),
        ("da.health.test_project", "curl -sf http://localhost:8080/health", "exit_and_contains", "{\"status\":\"ok\""),
        ("da.root.test_project", "curl -sf http://localhost:8080/", "exit0", None),
        ("da.env.test_project", "curl -sf http://localhost:8080/env", "env_endpoint", None),
        ("da.stop.test_project", f"{sys.executable} app/agent.py stop --local test_project --env test", "exit0", None),
        ("da.teardown.test_project", f"{sys.executable} app/agent.py teardown --local test_project --env test", "exit0", None),
        ("da.deploy.slackbot", f"{sys.executable} app/agent.py deploy AppliedDisruption/agent-slackbot-multitenant --local", "exit_and_contains", "healthy"),
        ("da.health.slackbot", "curl -sf http://localhost:8080/health", "exit_and_contains", "{\"status\":\"ok\""),
        ("da.oauth.slackbot", "curl -s http://localhost:8080/slack/oauth/callback", "exit_and_contains", "Missing Slack OAuth code"),
        ("da.stop.slackbot", f"{sys.executable} app/agent.py stop AppliedDisruption/agent-slackbot-multitenant --local", "exit0", None),
        ("da.rebuild", "da rebuild", "exit0", None),
    ]

    for name, cmd, mode, expected in checks:
        proc = _run(cmd, cwd=repo)
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        ok = False
        if mode == "no_traceback":
            ok = "Traceback" not in combined
        elif mode == "exit_and_contains":
            ok = proc.returncode == 0 and expected in combined
        elif mode == "exit0":
            ok = proc.returncode == 0
        elif mode == "env_endpoint":
            old_name_patterns = [r"\bAPP_SECRETS_FILE\b", r"\bENV_FILE\b"]
            has_old = any(re.search(p, combined) for p in old_name_patterns)
            ok = (
                proc.returncode == 0
                and "CONTAINER_ENV_FILE_APP_SECRETS" in combined
                and not has_old
            )
        _check(
            counts,
            ok,
            name,
            f"runtime:0: cmd failed `{cmd}`\n{combined.strip()}",
        )
        if not ok:
            break

    return counts


def _print_layer_summary(name: str, counts: Counts, include_warn: bool = False) -> None:
    if include_warn:
        print(f"Layer {name}:  {counts.passed} passed, {counts.failed} failed, {counts.warned} warned")
    else:
        print(f"Layer {name}:  {counts.passed} passed, {counts.failed} failed")


def run_all_layers(container: str) -> int:
    total = Counts()

    static = run_static_layer()
    _print_layer_summary("static", static, include_warn=True)
    total.passed += static.passed
    total.failed += static.failed
    total.warned += static.warned
    if static.failed:
        print("─────────────────────────────────────")
        print(f"Total:  {total.passed} passed, {total.failed} failed, {total.warned} warned")
        return 1

    unit = run_unit_layer()
    _print_layer_summary("unit", unit)
    total.passed += unit.passed
    total.failed += unit.failed
    if unit.failed:
        print("─────────────────────────────────────")
        print(f"Total:  {total.passed} passed, {total.failed} failed, {total.warned} warned")
        return 1

    da = run_da_layer()
    _print_layer_summary("da", da)
    total.passed += da.passed
    total.failed += da.failed
    if da.failed:
        print("─────────────────────────────────────")
        print(f"Total:  {total.passed} passed, {total.failed} failed, {total.warned} warned")
        return 1

    repo = Path("~/Github/agent-devagent-platform").expanduser()
    api_ready = False
    for _ in range(20):
        probe = _run("curl -sf http://localhost:8000/doctor")
        if probe.returncode == 0:
            api_ready = True
            break
        time.sleep(1)
    if not api_ready:
        print("FAIL  all.agent_api_ready — runtime:0: dev-agent API not ready after da layer")
        return 1

    deploy_slackbot = _run(
        f"{sys.executable} app/agent.py deploy AppliedDisruption/agent-slackbot-multitenant --local",
        cwd=repo,
    )
    if deploy_slackbot.returncode != 0:
        print("FAIL  all.redeploy.slackbot — runtime:0: failed to redeploy slackbot for mounts checks")
        print((deploy_slackbot.stdout or "") + (deploy_slackbot.stderr or ""))
        return 1

    mounts_slackbot = run_mounts_layer(container)
    _print_layer_summary("mounts", mounts_slackbot)
    total.passed += mounts_slackbot.passed
    total.failed += mounts_slackbot.failed
    if mounts_slackbot.failed:
        print("─────────────────────────────────────")
        print(f"Total:  {total.passed} passed, {total.failed} failed, {total.warned} warned")
        return 1

    _run(
        f"{sys.executable} app/agent.py stop AppliedDisruption/agent-slackbot-multitenant --local",
        cwd=repo,
    )
    deploy_test_project = _run(
        f"{sys.executable} app/agent.py deploy --local test_project --env test",
        cwd=repo,
    )
    if deploy_test_project.returncode != 0:
        print("FAIL  all.redeploy.test_project — runtime:0: failed to redeploy test_project for mounts checks")
        print((deploy_test_project.stdout or "") + (deploy_test_project.stderr or ""))
        return 1

    test_container = "local-test-project-test-container"
    names = _run("docker ps -a --format '{{.Names}}'").stdout or ""
    if test_container not in names and "test-project-test-container" in names:
        test_container = "test-project-test-container"

    mounts_test_project = run_mounts_layer(test_container)
    _print_layer_summary("mounts", mounts_test_project)
    total.passed += mounts_test_project.passed
    total.failed += mounts_test_project.failed

    print("─────────────────────────────────────")
    print(f"Total:  {total.passed} passed, {total.failed} failed, {total.warned} warned")
    return 1 if total.failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--layer",
        required=True,
        choices=["static", "unit", "mounts", "da", "all"],
    )
    parser.add_argument("--container", default=None)
    args = parser.parse_args()

    if args.layer == "static":
        counts = run_static_layer()
        _print_layer_summary("static", counts, include_warn=True)
        return 1 if counts.failed else 0
    if args.layer == "unit":
        counts = run_unit_layer()
        _print_layer_summary("unit", counts)
        return 1 if counts.failed else 0
    if args.layer == "mounts":
        if not args.container:
            print("FAIL  mounts.args — runtime:0: --container is required for --layer mounts")
            return 1
        counts = run_mounts_layer(args.container)
        _print_layer_summary("mounts", counts)
        return 1 if counts.failed else 0
    if args.layer == "da":
        counts = run_da_layer()
        _print_layer_summary("da", counts)
        return 1 if counts.failed else 0
    if args.layer == "all":
        if not args.container:
            print("FAIL  all.args — runtime:0: --container is required for --layer all")
            return 1
        return run_all_layers(args.container)
    return 1


if __name__ == "__main__":
    sys.exit(main())
