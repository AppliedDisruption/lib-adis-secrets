import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

from adis_secrets.reader import _cache, get_secret
from adis_secrets.writer import get_tenant_token, write_tenant_token
from adis_secrets.manifest import _reset_manifest_cache
from adis_secrets.client import (
    StartupPhase,
    VaultClient, _client_registry, _active_client_var, _reset_client_registry,
)
import adis_secrets.client as _client_module



class TestWriter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.secrets_file = Path(self.temp_dir.name) / "test-secrets.env"
        self.secrets_file.write_text("KEY=VALUE\n")
        os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = str(self.secrets_file)
        os.environ["VAULT_CFG_KEY_BACKEND"] = "file"
        
        self.manifest_fd, self.manifest_path = tempfile.mkstemp(text=True)
        with os.fdopen(self.manifest_fd, "w") as f:
            f.write("""version: 1
project: test
secrets:
  - key: KEY
  - pattern: \"T0*\"
    note: \"test tokens\"
""")
        os.environ["VAULT_CFG_KEY_MANIFEST_PATH"] = self.manifest_path
        
        _cache.invalidate()
        _reset_manifest_cache()
        _reset_client_registry()

        # Explicit client init — no legacy fallback needed
        vc = VaultClient(project_name="test", manifest_path=self.manifest_path)
        vc._client = Mock()  # InfisicalClient not needed for file backend tests
        _client_registry["test"] = vc
        _active_client_var.set(vc)
        _client_module._startup_phase = StartupPhase.READY

    def tearDown(self):
        self.temp_dir.cleanup()
        os.remove(self.manifest_path)
        os.environ.pop("VAULT_CFG_KEY_MANIFEST_PATH", None)
        os.environ.pop("VAULT_CFG_KEY_SECRETS_PATH", None)
        os.environ.pop("VAULT_CFG_KEY_BACKEND", None)
        _cache.invalidate()
        _reset_manifest_cache()
        _reset_client_registry()

    def _token_file(self) -> Path:
        return Path(self.temp_dir.name) / "tenant_tokens.json"

    def _read_tokens(self) -> dict:
        with open(self._token_file()) as f:
            return json.load(f)

    def test_write_creates_file(self):
        write_tenant_token("T001", {"access_token": "tok1"})
        self.assertTrue(self._token_file().exists())

    def test_write_merges_teams(self):
        write_tenant_token("T001", {"access_token": "tok1"})
        write_tenant_token("T002", {"access_token": "tok2"})
        data = self._read_tokens()
        self.assertEqual(data["T001"]["access_token"], "tok1")
        self.assertEqual(data["T002"]["access_token"], "tok2")

    def test_write_preserves_existing(self):
        write_tenant_token("T001", {"access_token": "tok1"})
        write_tenant_token("T001", {"access_token": "tok2"})
        write_tenant_token("T002", {"access_token": "tok3"})
        data = self._read_tokens()
        self.assertEqual(data["T001"]["access_token"], "tok2")
        self.assertEqual(data["T002"]["access_token"], "tok3")

    def test_get_returns_none_for_unknown(self):
        self.assertIsNone(get_tenant_token("UNKNOWN"))

    def test_get_returns_correct_data(self):
        write_tenant_token("T001", {"access_token": "tok1"})
        token = get_tenant_token("T001")
        self.assertIsNotNone(token)
        self.assertEqual(token["access_token"], "tok1")

    def test_write_is_atomic(self):
        with mock.patch("adis_secrets.backends.file.os.replace") as mocked_replace:
            write_tenant_token("T001", {"access_token": "tok1"})
        mocked_replace.assert_called_once()

    def test_stored_at_present(self):
        write_tenant_token("T001", {"access_token": "tok1"})
        data = self._read_tokens()
        self.assertIn("stored_at", data["T001"])
        datetime.fromisoformat(data["T001"]["stored_at"])

    def test_cache_invalidated_after_write(self):
        get_secret("KEY")
        self.assertFalse(_cache.is_stale())
        write_tenant_token("T001", {"access_token": "tok1"})
        self.assertTrue(_cache.is_stale())
