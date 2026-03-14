import io
import logging
import os
import tempfile
import unittest
from unittest import mock

from adis_secrets.reader import _cache, get_secret


class TestReader(unittest.TestCase):
    def setUp(self):
        _cache.invalidate()
        os.environ.pop("CONTAINER_ENV_FILE_APP_SECRETS", None)

    def _write_env_file(self, content: str) -> str:
        fd, path = tempfile.mkstemp(text=True)
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_get_secret_returns_value(self):
        path = self._write_env_file("KEY=VALUE\n")
        os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = path
        self.assertEqual(get_secret("KEY"), "VALUE")

    def test_get_secret_key_error(self):
        path = self._write_env_file("KEY=VALUE\n")
        os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = path
        with self.assertRaises(KeyError) as ctx:
            get_secret("MISSING")
        self.assertIn("Available keys:", str(ctx.exception))

    def test_secret_value_never_logged(self):
        path = self._write_env_file("SECRET_KEY=super-secret-value\n")
        os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = path

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
        os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = path

        with mock.patch("builtins.open", wraps=open) as mocked_open:
            self.assertEqual(get_secret("KEY"), "VALUE")
            self.assertEqual(get_secret("KEY"), "VALUE")

        self.assertEqual(mocked_open.call_count, 1)

    def test_cache_refreshes_after_ttl(self):
        path = self._write_env_file("KEY=VALUE\n")
        os.environ["CONTAINER_ENV_FILE_APP_SECRETS"] = path

        with mock.patch("builtins.open", wraps=open) as mocked_open:
            self.assertEqual(get_secret("KEY"), "VALUE")
            loaded_at = _cache._loaded_at
            with mock.patch("adis_secrets.reader.time.time", return_value=loaded_at + 301):
                self.assertEqual(get_secret("KEY"), "VALUE")

        self.assertEqual(mocked_open.call_count, 2)

    def test_missing_env_var_raises(self):
        os.environ.pop("CONTAINER_ENV_FILE_APP_SECRETS", None)
        with self.assertRaises(EnvironmentError) as ctx:
            get_secret("ANY")
        self.assertIn("CONTAINER_ENV_FILE_APP_SECRETS is not set", str(ctx.exception))
