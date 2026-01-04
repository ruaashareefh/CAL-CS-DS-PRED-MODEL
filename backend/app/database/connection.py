"""
Database connection management
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from ..config import settings


def get_db_connection():
    """
    Create a database connection with proper configuration

    Returns:
        sqlite3.Connection: Database connection object

    Raises:
        FileNotFoundError: If database file doesn't exist
        sqlite3.Error: If connection fails
    """
    db_path = settings.DB_PATH

    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries

    return conn


@contextmanager
def get_db():
    """
    Context manager for database connections
    Automatically closes connection after use

    Usage:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM courses")
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def test_connection():
    """
    Test database connection

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM courses")
            result = cursor.fetchone()
            return True
    except Exception:
        return False
