import logging
import os
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

_manifest_cache: dict | None = None


def _reset_manifest_cache():
    """Reset the manifest cache for testing."""
    global _manifest_cache
    _manifest_cache = None


def _validate_manifest(manifest: dict):
    """Validate manifest rules."""
    # Enforce pattern rules
    for section in ["env", "secrets"]:
        entries = manifest.get(section, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            pattern = entry.get("pattern")
            if pattern is not None:
                if pattern == "*":
                    raise ValueError(f"Pattern cannot be just '*' in manifest section {section}")
                if "note" not in entry:
                    logger.warning(f"Pattern '{pattern}' in manifest section {section} is missing a 'note'")

    # Enforce file rules
    files = manifest.get("files", [])
    if isinstance(files, list):
        for entry in files:
            path_val = entry.get("path")
            if path_val and "*" in path_val:
                raise ValueError(f"Wildcards are not allowed in file paths: {path_val}")


def get_manifest() -> dict:
    """Load and cache the manifest."""
    global _manifest_cache
    if _manifest_cache is not None:
        return _manifest_cache

    # We use os.environ.get directly because we don't want to trigger
    # the enforcement loop while trying to load the enforcement manifest.
    manifest_path_str = os.environ.get("VAULT_CFG_KEY_MANIFEST_PATH")
    if not manifest_path_str:
        raise EnvironmentError("VAULT_CFG_KEY_MANIFEST_PATH is not set. Manifest enforcement requires a manifest.")

    manifest_path = Path(manifest_path_str)
    if not manifest_path.is_absolute():
        raise ValueError(f"VAULT_CFG_KEY_MANIFEST_PATH must be an absolute path: {manifest_path_str}")

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at: {manifest_path_str}")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
            if not isinstance(manifest, dict):
                manifest = {}
    except Exception as e:
        raise ValueError(f"Failed to parse manifest YAML at {manifest_path_str}: {e}")

    _validate_manifest(manifest)

    _manifest_cache = manifest
    return _manifest_cache
