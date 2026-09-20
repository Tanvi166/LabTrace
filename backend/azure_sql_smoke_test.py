"""Read-only Azure SQL connectivity check using Azure CLI/Entra authentication.

Run from ``backend`` after ``az login``. This script executes only ``SELECT 1``;
it does not run Alembic or modify schema/data.
"""

import logging

import pyodbc
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.database import (
    SQL_COPT_SS_ACCESS_TOKEN,
    create_database_engine,
    get_azure_sql_token_struct,
)


def _print_safe_configuration(database_url: str) -> None:
    url = make_url(database_url)
    configured_driver = settings.AZURE_SQL_DRIVER
    print(f"Azure SQL server: {settings.AZURE_SQL_SERVER}")
    print(f"Azure SQL database: {settings.AZURE_SQL_DATABASE}")
    print(f"SQLAlchemy URL: {database_url}")
    print(f"ODBC driver configured: {configured_driver}")
    print(f"ODBC driver installed: {configured_driver in pyodbc.drivers()}")
    print(f"Encrypt enabled: {url.query.get('Encrypt', '').lower() == 'yes'}")
    print(f"SQL password authentication configured: {bool(url.username or url.password)}")
    print(f"Entra token ODBC option: SQL_COPT_SS_ACCESS_TOKEN={SQL_COPT_SS_ACCESS_TOKEN}")


def main() -> None:
    # Keep credential-chain diagnostics out of normal smoke-test output. The
    # underlying ODBC exception is printed below, but no token is ever printed.
    logging.getLogger("azure.identity").setLevel(logging.CRITICAL)
    database_url = settings.model_copy(update={"AZURE_SQL_ENABLED": True}).database_url
    _print_safe_configuration(database_url)
    try:
        token_struct = get_azure_sql_token_struct()
        print(f"DefaultAzureCredential token obtained: {len(token_struct) > 4}")
        engine = create_database_engine(database_url)
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        engine.dispose()
        print("Azure SQL connectivity smoke test passed: SELECT 1 returned 1.")
    except Exception as exc:
        print(f"Azure SQL connectivity smoke test failed ({type(exc).__name__}).")
        print("Underlying exception details:")
        print(repr(exc))
        if getattr(exc, "orig", None) is not None:
            print("Underlying DBAPI exception:")
            print(repr(exc.orig))
            print(f"DBAPI error arguments: {exc.orig.args!r}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
