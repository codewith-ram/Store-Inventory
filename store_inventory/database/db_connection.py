import os
import sqlite3
from pathlib import Path

DB_NAME = 'store_inventory.db'
DB_PATH = Path(__file__).resolve().parents[1] / DB_NAME


def get_connection():
    """Return a SQLite connection with row factory dict-like."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn
