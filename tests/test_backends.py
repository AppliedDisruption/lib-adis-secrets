import os
import unittest

from adis_secrets.backends import aws, gcp
from adis_secrets.writer import write_tenant_token


class TestBackends(unittest.TestCase):
    def test_aws_write_raises(self):
        with self.assertRaises(NotImplementedError) as ctx:
            aws.write_tenant_token("T001", {"access_token": "tok"})
        self.assertIn("VAULT_CFG_KEY_BACKEND=file", str(ctx.exception))

    def test_aws_get_raises(self):
        with self.assertRaises(NotImplementedError):
            aws.get_tenant_token("T001")

    def test_gcp_write_raises(self):
        with self.assertRaises(NotImplementedError):
            gcp.write_tenant_token("T001", {"access_token": "tok"})

    def test_gcp_get_raises(self):
        with self.assertRaises(NotImplementedError):
            gcp.get_tenant_token("T001")

    def test_unknown_backend_raises_valueerror(self):
        os.environ["VAULT_CFG_KEY_BACKEND"] = "unknown"
        try:
            with self.assertRaises(ValueError) as ctx:
                write_tenant_token("T001", {"access_token": "tok"})
            self.assertIn("Supported: file, aws, gcp", str(ctx.exception))
        finally:
            os.environ.pop("VAULT_CFG_KEY_BACKEND", None)
