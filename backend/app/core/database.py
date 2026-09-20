import struct

from azure.identity import DefaultAzureCredential
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# SQL Server ODBC constant from msodbcsql.h. pyodbc does not expose it on every
# platform, so keep the documented numeric value in one narrowly scoped place.
SQL_COPT_SS_ACCESS_TOKEN = 1256


def is_azure_sql_url(database_url: str) -> bool:
    return database_url.startswith("mssql+pyodbc:")


def get_azure_sql_token_struct(credential: DefaultAzureCredential | None = None) -> bytes:
    """Return the ODBC token structure required by SQL_COPT_SS_ACCESS_TOKEN."""
    credential = credential or DefaultAzureCredential()
    encoded_token = credential.get_token(settings.AZURE_SQL_TOKEN_SCOPE).token.encode("utf-16-le")
    return struct.pack("<I", len(encoded_token)) + encoded_token


def create_database_engine(database_url: str | None = None):
    """Create a SQLite or Azure SQL engine without embedding credentials in URLs."""
    database_url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    database_engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=not database_url.startswith("sqlite"),
        echo=False,
    )

    if is_azure_sql_url(database_url):
        @event.listens_for(database_engine, "do_connect")
        def provide_azure_sql_token(dialect, connection_record, cargs, cparams):
            # The dialect adds this for a URL with no username. Entra token auth
            # cannot be combined with Trusted_Connection authentication.
            cargs[0] = cargs[0].replace(";Trusted_Connection=Yes", "")
            cparams["attrs_before"] = {
                **cparams.get("attrs_before", {}),
                SQL_COPT_SS_ACCESS_TOKEN: get_azure_sql_token_struct(),
            }

    return database_engine

engine = create_database_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def is_sqlite_database() -> bool:
    """SQLite remains the zero-configuration local development database."""
    return settings.database_url.startswith("sqlite")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
