"""Check the registered SQL Server driver and load its native dependencies offline."""

import configparser
import ctypes
import subprocess

import pyodbc


def main():
    driver = "ODBC Driver 18 for SQL Server"
    if driver not in pyodbc.drivers():
        raise SystemExit(f"Missing registered ODBC driver: {driver}")

    registration = subprocess.check_output(
        ["odbcinst", "-q", "-d", "-n", driver], text=True
    )
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(registration)
    library = config[driver]["Driver"]
    ctypes.CDLL(library)
    print(f"SQL Server ODBC driver loaded: {library}")


if __name__ == "__main__":
    main()
