import os
import tempfile
import unittest
from pathlib import Path

from adis_secrets.backends.file import _token_file_path


class TestPathContexts(unittest.TestCase):
    def _all_python_source(self) -> str:
        root = Path(__file__).resolve().parents[1] / "adis_secrets"
        content = []
        for path in root.rglob("*.py"):
            content.append(path.read_text())
        return "\n".join(content)

    def test_no_hardcoded_host_paths_in_package(self):
        src = self._all_python_source()
        self.assertNotIn("/Users/", src)
        self.assertNotIn("/home/", src)

    def test_no_hardcoded_secrets_path(self):
        src = self._all_python_source()
        self.assertNotIn("/.secrets/secrets.env", src)

    def test_no_host_prefixed_vars_in_package(self):
        src = self._all_python_source()
        self.assertNotIn("HOST_", src)

    def test_resolution_vars_used_in_reader(self):
        reader_path = Path(__file__).resolve().parents[1] / "adis_secrets" / "reader.py"
        source = reader_path.read_text()
        self.assertIn("VAULT_CFG_KEY_SECRETS_PATH", source)
        self.assertIn("APP_PROJECT_NAME", source)

    def test_token_path_derived_correctly(self):
        old_value = os.environ.get("VAULT_CFG_KEY_SECRETS_PATH")
        with tempfile.TemporaryDirectory() as tmpdir:
            secrets_file = Path(tmpdir) / "test-secrets.env"
            secrets_file.write_text("KEY=VALUE\n", encoding="utf-8")
            os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = str(secrets_file)
            try:
                self.assertEqual(_token_file_path(), Path(tmpdir) / "tenant_tokens.json")
            finally:
                if old_value is None:
                    os.environ.pop("VAULT_CFG_KEY_SECRETS_PATH", None)
                else:
                    os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = old_value

    def test_token_path_requires_resolution_vars(self):
        old_value_override = os.environ.pop("VAULT_CFG_KEY_SECRETS_PATH", None)
        old_value_project = os.environ.pop("APP_PROJECT_NAME", None)
        try:
            with self.assertRaises(EnvironmentError):
                _token_file_path()
        finally:
            if old_value_override is not None:
                os.environ["VAULT_CFG_KEY_SECRETS_PATH"] = old_value_override
            if old_value_project is not None:
                os.environ["APP_PROJECT_NAME"] = old_value_project
