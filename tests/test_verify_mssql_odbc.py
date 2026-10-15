"""Exercise real unixODBC registration and native loading without a database."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "resources/release/verify_mssql_odbc.py"
DRIVER = "ODBC Driver 18 for SQL Server"


@unittest.skipUnless(importlib.util.find_spec("pyodbc"), "requires pyodbc and unixODBC")
class VerifyMssqlOdbcTest(unittest.TestCase):
    def run_check(self, config):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "odbcinst.ini").write_text(config)
            return subprocess.run(
                [sys.executable, str(SCRIPT)],
                env={
                    **os.environ,
                    "ODBCSYSINI": directory,
                    "ODBCINSTINI": "odbcinst.ini",
                },
                capture_output=True,
                text=True,
                timeout=10,
            )

    def test_rejects_missing_driver_even_when_pyodbc_imports(self):
        result = self.run_check("")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"Missing registered ODBC driver: {DRIVER}", result.stderr)

    def test_rejects_registered_driver_with_missing_library(self):
        result = self.run_check(f"[{DRIVER}]\nDriver=/nonexistent/tbi-odbc-driver.so\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OSError", result.stderr)
        self.assertIn("tbi-odbc-driver.so", result.stderr)

    def test_loads_installed_driver(self):
        import pyodbc

        if DRIVER not in pyodbc.drivers():
            self.skipTest("requires Microsoft ODBC 18")
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SQL Server ODBC driver loaded:", result.stdout)


if __name__ == "__main__":
    unittest.main()
