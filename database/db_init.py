from .db_connection import get_connection

SCHEMA = {
    'users': (
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        );
        """
    ),
    'suppliers': (
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            address TEXT
        );
        """
    ),
    'products': (
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0,
            supplier_id INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        );
        """
    ),
    'sales': (
        """
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity_sold INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
        """
    )
}


def initialize_database():
    conn = get_connection()
    try:
        cur = conn.cursor()
        for name, ddl in SCHEMA.items():
            cur.execute(ddl)
        conn.commit()
    finally:
        conn.close()


def seed_demo_data():
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Only seed if there are no products yet
        cur.execute("SELECT COUNT(*) FROM products")
        if int(cur.fetchone()[0]) > 0:
            return
        # Seed suppliers
        suppliers = [
            ("Office Depot", "sales@officedepot.com", "123 Market St"),
            ("Staples", "info@staples.com", "456 Commerce Ave"),
            ("Stationery Pro", "hello@stationerypro.com", "789 Industrial Rd"),
        ]
        for name, contact, address in suppliers:
            cur.execute(
                "INSERT INTO suppliers (name, contact, address) VALUES (?, ?, ?)",
                (name, contact, address)
            )
        # Map supplier names to IDs
        cur.execute("SELECT supplier_id, name FROM suppliers")
        id_map = {row[1]: row[0] for row in cur.fetchall()}
        # Seed products (name, category, qty, price, supplier_name)
        products = [
            ("Ballpoint Pen Blue", "Pens", 120, 0.50, "Office Depot"),
            ("Gel Pen Black", "Pens", 80, 0.80, "Office Depot"),
            ("A4 Notebook 200pg", "Notebooks", 60, 2.50, "Staples"),
            ("Highlighter Set (5)", "Markers", 40, 3.99, "Staples"),
            ("Stapler Heavy-Duty", "Accessories", 25, 7.49, "Stationery Pro"),
            ("Paper Clips 100ct", "Accessories", 100, 1.20, "Stationery Pro"),
        ]
        for name, cat, qty, price, sname in products:
            cur.execute(
                "INSERT INTO products (name, category, quantity, price, supplier_id) VALUES (?, ?, ?, ?, ?)",
                (name, cat, qty, price, id_map.get(sname))
            )
        conn.commit()
    finally:
        conn.close()
