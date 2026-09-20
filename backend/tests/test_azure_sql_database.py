import struct

from app.core.database import SQL_COPT_SS_ACCESS_TOKEN, get_azure_sql_token_struct, is_azure_sql_url


def test_azure_sql_url_detection():
    assert is_azure_sql_url("mssql+pyodbc://@server/database?driver=ODBC+Driver+18")
    assert not is_azure_sql_url("sqlite:///./labtrace.db")


def test_azure_sql_token_is_encoded_for_pyodbc():
    class FakeCredential:
        def get_token(self, scope):
            assert scope == "https://database.windows.net/.default"
            return type("Token", (), {"token": "abc"})()

    token_struct = get_azure_sql_token_struct(FakeCredential())

    assert SQL_COPT_SS_ACCESS_TOKEN == 1256
    assert struct.unpack("<I", token_struct[:4])[0] == len("abc".encode("utf-16-le"))
    assert token_struct[4:] == b"a\x00b\x00c\x00"
