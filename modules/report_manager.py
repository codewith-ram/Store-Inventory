import io
from typing import List, Dict
from ..database.db_connection import get_connection
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def top_products(limit: int = 5) -> List[Dict]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.name, COALESCE(SUM(s.quantity_sold), 0) AS qty
            FROM products p
            LEFT JOIN sales s ON p.product_id = s.product_id
            GROUP BY p.product_id
            ORDER BY qty DESC
            LIMIT ?
            """,
            (limit,)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def monthly_sales() -> List[Dict]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT substr(sale_date, 1, 7) AS ym, SUM(total_amount) AS total
            FROM sales
            GROUP BY ym
            ORDER BY ym ASC
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def render_bar_chart(data: List[Dict], x_key: str, y_key: str, title: str) -> bytes:
    x = [d.get(x_key, '') for d in data]
    y = [float(d.get(y_key, 0)) for d in data]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(x, y, color="#0078D7")
    ax.set_title(title)
    ax.set_ylabel(y_key)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    return buf.getvalue()


def export_pdf_report(output_path: str):
    tp = top_products(5)
    ms = monthly_sales()

    top_img = render_bar_chart(tp, 'name', 'qty', 'Top Products by Quantity') if tp else None
    mon_img = render_bar_chart(ms, 'ym', 'total', 'Monthly Sales Total') if ms else None

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    c.setTitle("Store Inventory Report")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Store Inventory Report")

    y = height - 90
    c.setFont("Helvetica", 12)

    if top_img:
        c.drawString(50, y, "Top Products")
        y -= 20
        c.drawImage(ImageReader(io.BytesIO(top_img)), 50, y - 200, width=500, height=200, preserveAspectRatio=True, mask='auto')
        y -= 220

    if mon_img:
        c.drawString(50, y, "Monthly Sales")
        y -= 20
        c.drawImage(ImageReader(io.BytesIO(mon_img)), 50, y - 200, width=500, height=200, preserveAspectRatio=True, mask='auto')
        y -= 220

    c.showPage()
    c.save()
