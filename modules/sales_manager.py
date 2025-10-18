from typing import List, Dict, Any
from datetime import datetime
from ..database.db_connection import get_connection


def list_sales() -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.sale_id, s.product_id, p.name as product_name, s.quantity_sold, s.sale_date, s.total_amount
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            ORDER BY s.sale_id ASC
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def record_sale(product_id: int, quantity_sold: int, price_per_unit: float):
    total_amount = quantity_sold * price_per_unit
    sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Check stock
        cur.execute("SELECT quantity FROM products WHERE product_id=?", (product_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Product not found")
        if row['quantity'] < quantity_sold:
            raise ValueError("Insufficient stock")
        # Insert sale
        cur.execute(
            "INSERT INTO sales (product_id, quantity_sold, sale_date, total_amount) VALUES (?, ?, ?, ?)",
            (product_id, quantity_sold, sale_date, total_amount)
        )
        # Update stock
        cur.execute(
            "UPDATE products SET quantity = quantity - ? WHERE product_id=?",
            (quantity_sold, product_id)
        )
        conn.commit()
    finally:
        conn.close()


def total_revenue() -> float:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM sales")
        return float(cur.fetchone()[0] or 0.0)
    finally:
        conn.close()
