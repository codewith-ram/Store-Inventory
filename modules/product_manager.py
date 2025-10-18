from typing import List, Optional, Dict, Any
from ..database.db_connection import get_connection


def list_products() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.product_id, p.name, p.category, p.quantity, p.price, p.supplier_id,
                   s.name AS supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            ORDER BY p.product_id ASC
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def add_product(name: str, category: str, quantity: int, price: float, supplier_id: Optional[int]):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, category, quantity, price, supplier_id) VALUES (?, ?, ?, ?, ?)",
            (name, category, quantity, price, supplier_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_product(product_id: int, name: str, category: str, quantity: int, price: float, supplier_id: Optional[int]):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE products SET name=?, category=?, quantity=?, price=?, supplier_id=?
            WHERE product_id=?
            """,
            (name, category, quantity, price, supplier_id, product_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_product(product_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE product_id=?", (product_id,))
        conn.commit()
    finally:
        conn.close()


def search_products(keyword: str) -> List[Dict[str, Any]]:
    kw = f"%{keyword}%"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.product_id, p.name, p.category, p.quantity, p.price, p.supplier_id,
                   s.name AS supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
            WHERE p.name LIKE ? OR p.category LIKE ?
            ORDER BY p.name ASC
            """,
            (kw, kw)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def count_low_stock(threshold: int = 5) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM products WHERE quantity <= ?", (threshold,))
        return int(cur.fetchone()[0])
    finally:
        conn.close()


def count_products() -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM products")
        return int(cur.fetchone()[0])
    finally:
        conn.close()
