import io
import logging
import os
import tempfile
import unittest
from unittest import mock
from unittest.mock import Mock

import pytest

from adis_secrets.reader import _cache, get_secret
from adis_secrets.manifest import _reset_manifest_cache
from adis_secrets.client import (
    StartupPhase,
    VaultClient, _client_registry, _active_client_var, _reset_client_registry,
)
import adis_secrets.client as _client_module


class TestReader(unittest.TestCase):
    def setUp(self):
        _cache.invalidate()
        _reset_manifest_cache()
        _reset_client_registry()
        
        # Create a dummy test manifest
        self.manifest_fd, self.manifest_path = tempfile.mkstemp(text=True)
        with os.fdopen(self.manifest_fd, "w") as f:
            f.write("""version: 1
project: test
secrets:
  - key: KEY
  - key: SECRET_KEY
  - key: MISSING
env:
  - key: VAULT_CFG_KEY_BACKEND
  - key: VAULT_CFG_KEY_SECRETS_PATH
  - key: APP_PROJECT_NAME
  - key: VAULT_CFG_KEY_MANIFEST_PATH
files:
  - path: /tmp/
    access: read
    type: directory_prefix
  - path: /var/folders/
    access: read
    type: directory_prefix
""")
            
        os.environ["VAULT_CFG_KEY_MANIFEST_PATH"] = self.manifest_path
        os.environ["VAULT_CFG_KEY_BACKEND"] = "file"
        os.environ.pop("VAULT_CFG_KEY_SECRETS_PATH", None)
        os.environ.pop("APP_PROJECT_NAME", None)

        # Explicit client init — no legacy fallback needed
        vc = VaultClient(project_name="test", manifest_path=self.manifest_path)
        vc._client = Mock()  # InfisicalClient not needed for file backend tests
        _client_registry["test"] = vc
        _active_client_var.set(vc)
        _client_module._startup_phase = StartupPhase.READY

    def tearDown(self):
        os.remove(self.manifest_path)

    def _write_env_file(self, content: str) -> str:
        fd, path = tempfile.mkstemp(text=True)
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_get_secret_returns_value(self):
        path = self._write_env_file("KEY=VALUE\n")
        os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = path
        self.assertEqual(get_secret("KEY"), "VALUE")

    def test_get_secret_key_error(self):
        path = self._write_env_file("KEY=VALUE\n")
        os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = path
        with self.assertRaises(KeyError) as ctx:
            get_secret("MISSING")
        self.assertIn("Available keys:", str(ctx.exception))

    def test_secret_value_never_logged(self):
        path = self._write_env_file("SECRET_KEY=super-secret-value\n")
        os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = path

        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("adis_secrets.reader")
        old_level = logger.level
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        try:
            get_secret("SECRET_KEY")
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)

        output = stream.getvalue()
        self.assertIn("SECRET_KEY", output)
        self.assertNotIn("super-secret-value", output)

    def test_cache_used_on_second_call(self):
        path = self._write_env_file("KEY=VALUE\n")
        os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = path

        from adis_secrets.manifest import get_manifest
        get_manifest()

        with mock.patch("builtins.open", wraps=open) as mocked_open:
            self.assertEqual(get_secret("KEY"), "VALUE")
            self.assertEqual(get_secret("KEY"), "VALUE")

        self.assertEqual(mocked_open.call_count, 1)

    def test_cache_refreshes_after_ttl(self):
        path = self._write_env_file("KEY=VALUE\n")
        os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = path

        from adis_secrets.manifest import get_manifest
        get_manifest()

        with mock.patch("builtins.open", wraps=open) as mocked_open:
            self.assertEqual(get_secret("KEY"), "VALUE")
            loaded_at = _cache._loaded_at
            with mock.patch("adis_secrets.reader.time.time", return_value=loaded_at + 301):
                self.assertEqual(get_secret("KEY"), "VALUE")

        self.assertEqual(mocked_open.call_count, 2)

    def test_missing_resolution_vars_raises(self):
        os.environ.pop("VAULT_CFG_KEY_SECRETS_PATH", None)
        os.environ.pop("APP_PROJECT_NAME", None)
        with self.assertRaises(EnvironmentError) as ctx:
            get_secret("KEY")
        self.assertIn(
            "Cannot resolve secrets file: set VAULT_CFG_KEY_SECRETS_PATH or APP_PROJECT_NAME",
            str(ctx.exception),
        )


def test_get_secret_before_init_raises():
    _reset_client_registry()
    with pytest.raises(RuntimeError, match="init_client"):
        get_secret("VAULT_SEC_KEY_ANYTHING")
