from typing import List, Dict, Any
from ..database.db_connection import get_connection


def list_suppliers() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM suppliers ORDER BY supplier_id ASC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def add_supplier(name: str, contact: str, address: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO suppliers (name, contact, address) VALUES (?, ?, ?)",
            (name, contact, address)
        )
        conn.commit()
    finally:
        conn.close()


def update_supplier(supplier_id: int, name: str, contact: str, address: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE suppliers SET name=?, contact=?, address=? WHERE supplier_id=?",
            (name, contact, address, supplier_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_supplier(supplier_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE supplier_id=?", (supplier_id,))
        conn.commit()
    finally:
        conn.close()
