import os
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

    def test_container_env_var_used_in_reader(self):
        reader_path = Path(__file__).resolve().parents[1] / "adis_secrets" / "reader.py"
        source = reader_path.read_text()
        self.assertIn("CONTAINER_ENV_FILE_APP_SECRETS", source)

    def test_token_path_derived_correctly(self):
        old_value = os.environ.get("CONTAINER_ENV_FILE_APP_SECRETS")
        os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = "/.secrets/test-secrets.env"
        try:
            self.assertEqual(_token_file_path(), Path("/.secrets/tenant_tokens.json"))
        finally:
            if old_value is None:
                os.environ.pop("CONTAINER_ENV_FILE_APP_SECRETS", None)
            else:
                os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = old_value

    def test_token_path_requires_env_var(self):
        old_value = os.environ.pop("CONTAINER_ENV_FILE_APP_SECRETS", None)
        try:
            with self.assertRaises(EnvironmentError):
                _token_file_path()
        finally:
            if old_value is not None:
                os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = old_value
