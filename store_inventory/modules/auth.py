import bcrypt
from typing import Optional
from ..database.db_connection import get_connection


def _get_user_by_username(username: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        return row
    finally:
        conn.close()


def ensure_default_admin():
    """Create a default admin if no users exist."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM users")
        if cur.fetchone()[0] == 0:
            username = 'admin'
            password = 'admin123'
            role = 'admin'
            pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, pw_hash.decode('utf-8'), role)
            )
            conn.commit()
    finally:
        conn.close()


def verify_login(username: str, password: str) -> bool:
    row = _get_user_by_username(username)
    if not row:
        return False
    stored_hash = row['password_hash']
    try:
        ok = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        return ok
    except Exception:
        return False


def get_user_role(username: str) -> Optional[str]:
    row = _get_user_by_username(username)
    return row['role'] if row else None
