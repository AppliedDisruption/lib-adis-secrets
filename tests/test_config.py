import os
import tempfile
import unittest
from pathlib import Path

import adis_secrets.config as cfg
from adis_secrets.config import get_config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.prev_cwd = os.getcwd()
        cfg._config_cache = {}
        cfg._config_mtime = 0.0

    def tearDown(self):
        os.chdir(self.prev_cwd)
        cfg._config_cache = {}
        cfg._config_mtime = 0.0

    def test_get_config_reads_value(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "deploy.config.yml"
            path.write_text(
                "config:\n"
                "  model: claude-test\n"
                "  history_limit: 5\n"
            )
            os.chdir(td)
            self.assertEqual(get_config("model"), "claude-test")
            self.assertEqual(get_config("history_limit"), 5)

    def test_get_config_default(self):
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            self.assertEqual(get_config("nonexistent", default="x"), "x")

    def test_get_config_none_default(self):
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            self.assertIsNone(get_config("nonexistent"))

    def test_get_config_never_raises(self):
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            self.assertIsNone(get_config("anything"))

    def test_get_config_not_sensitive(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "deploy.config.yml"
            path.write_text(
                "config:\n"
                "  model: claude-test\n"
                "  history_limit: 5\n"
                "  enabled: true\n"
            )
            os.chdir(td)
            self.assertIsInstance(get_config("model"), (str, int, float, bool))
            self.assertIsInstance(get_config("history_limit"), (str, int, float, bool))
            self.assertIsInstance(get_config("enabled"), (str, int, float, bool))
