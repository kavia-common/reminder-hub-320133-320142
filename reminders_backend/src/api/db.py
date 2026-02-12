import os
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg
from psycopg.rows import dict_row


def _get_database_url() -> str:
    """
    Returns the configured Postgres connection string.

    We intentionally do not hardcode credential/host info; the runtime must provide it
    through environment variables.

    Supported variables:
    - DATABASE_URL (preferred)
    - POSTGRES_URL (fallback)

    If neither is set, we raise with a clear message so misconfiguration is obvious.
    """
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url:
        raise RuntimeError(
            "Database connection is not configured. Please set DATABASE_URL (preferred) "
            "or POSTGRES_URL in the environment."
        )
    return database_url


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """
    Context manager that yields a psycopg3 connection with dict row factory.

    Using a context manager ensures connections are closed promptly.
    """
    conn = psycopg.connect(_get_database_url(), row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def try_connect() -> Optional[str]:
    """
    Attempts a short connectivity check to the DB.

    Returns:
        None if OK, else an error string suitable for diagnostics.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as ok;")
                _ = cur.fetchone()
        return None
    except Exception as exc:  # noqa: BLE001 - we want a diagnostic string
        return str(exc)
