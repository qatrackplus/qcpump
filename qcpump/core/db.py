import contextlib
import os
import sqlite3

import fdb
import firebirdsql

import pyodbc

from qcpump.settings import Settings

settings = Settings()


def db_query(driver, connect_kwargs, statement, params=None, fetch_method="fetchall"):

    params = params or ()
    params = tuple(params)

    with contextlib.closing(driver.connect(**connect_kwargs)) as conn:
        with conn:
            with contextlib.closing(conn.cursor()) as cursor:
                cursor.execute(statement, params)
                if fetch_method == "fetchallmap":
                    columns = [d[0].lower() for d in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    return getattr(cursor, fetch_method, cursor.fetchall)()


def fdb_query(connect_kwargs, statement, params=None, fetch_method="fetchall"):
    """
    Execute an FDB query and return results. Form of connect_kwargs is e.g.

    connect_kwargs = {
        "database": r"C:/path/to/database.fdb",
        "user": "username",
        "password": "password",
        "host": "localhost",
        "port": 3050,
    }
    """
    return db_query(fdb, connect_kwargs, statement, params=params, fetch_method=fetch_method)


def firebirdsql_query(connect_kwargs, statement, params=None, fetch_method="fetchall"):
    """
    Execute an FDB query and return results. Form of connect_kwargs is e.g.

    connect_kwargs = {
        "database": r"C:/path/to/database.fdb",
        "user": "username",
        "password": "password",
        "host": "localhost",
        "port": 3050,
    }
    """

    if 'timeout' not in connect_kwargs:
        connect_kwargs['timeout'] = settings.DB_CONNECT_TIMEOUT

    return db_query(firebirdsql, connect_kwargs, statement, params=params, fetch_method=fetch_method)


def sqlite_query(connect_kwargs, statement, params=None, fetch_method="fetchall"):
    """
    Execute an SQLite3 query and return results. Form of connect_kwargs is e.g.

    connect_kwargs = {
        "database": r"C:/path/to/database.sqlite3",
    }
    """

    return db_query(sqlite3, connect_kwargs, statement, params=params, fetch_method=fetch_method)


def mssql_query(connect_kwargs, statement, params=None, fetch_method="fetchall"):
    """
    Execute an MSSQL query and return results. Form of connect_kwargs is e.g.

    connect_kwargs = {
        "server": "localhost",
        "database": "some_database",
        "driver": "FreeTDS",
        "user": "username",
        "password": "password",
        "port": 1433,
        "timeout": 1, # 1 s connection timeout
    }
    """
    if connect_kwargs.get("driver").lower() == "freetds":  # pragma: nocover
        os.environ['TDSVER'] = '7.4'

    if 'timeout' not in connect_kwargs:
        connect_kwargs['timeout'] = settings.DB_CONNECT_TIMEOUT

    return db_query(pyodbc, connect_kwargs, statement, params=params, fetch_method=fetch_method)
