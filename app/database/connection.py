"""Database connection manager for ORISUN IBUKUN - Owode Unit."""
import sqlite3
import os
import sys
import threading
from pathlib import Path
from contextlib import contextmanager


def _get_db_dir() -> Path:
    """Get the database directory, handling PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle - use APPDATA
        return Path(os.environ.get("APPDATA", Path.home())) / "OrisunIbukun"
    else:
        # Running from source - use local directory
        return Path(__file__).parent.parent / "data"


DB_DIR = _get_db_dir()
# NOTE: the frozen app uses its own database file. The legacy .NET app uses
# orisun_ibukun.db in the same folder — the two schemas are incompatible,
# so they must never share a file.
DB_NAME = "orisun_ibukun_py.db" if getattr(sys, 'frozen', False) else "orisun_ibukun.db"
DB_PATH = DB_DIR / DB_NAME

_connection = None
_connection_lock = threading.Lock()
_pool: list[sqlite3.Connection] = []
_pool_lock = threading.Lock()
_MAX_POOL_SIZE = 5


def _create_connection() -> sqlite3.Connection:
    """Create a new database connection with proper configuration."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def get_connection() -> sqlite3.Connection:
    """Get the shared application connection (single-threaded Tk app).

    Reuses one connection to avoid SQLITE_LOCKED errors and handle leaks
    from opening a new connection per call.
    """
    global _connection
    with _connection_lock:
        if _connection is None:
            if _pool:
                _connection = _pool.pop()
            else:
                _connection = _create_connection()
        return _connection


def return_connection(conn: sqlite3.Connection) -> None:
    """Return a connection to the pool."""
    with _pool_lock:
        if len(_pool) < _MAX_POOL_SIZE:
            _pool.append(conn)
        else:
            conn.close()


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        return_connection(conn)


def close_connection() -> None:
    """Close all connections in the pool and the main connection."""
    global _connection

    with _pool_lock:
        for conn in _pool:
            conn.close()
        _pool.clear()

    if _connection:
        _connection.close()
        _connection = None


def init_connection_pool(size: int = 3) -> None:
    """Initialize the connection pool with a specific size."""
    global _pool
    with _pool_lock:
        for conn in _pool:
            conn.close()
        _pool = [_create_connection() for _ in range(size)]
