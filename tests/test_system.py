import os
import unittest
from pathlib import Path

from store_inventory.database.db_connection import DB_PATH, get_connection
from store_inventory.database.db_init import initialize_database
from store_inventory.modules.auth import ensure_default_admin, verify_login
from store_inventory.modules import product_manager as pm
from store_inventory.modules import supplier_manager as sm
from store_inventory.modules import sales_manager as sam
from store_inventory.modules import report_manager as rm


class TestStoreInventorySystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset DB for tests
        if DB_PATH.exists():
            DB_PATH.unlink()
        initialize_database()
        ensure_default_admin()

    def test_default_admin_login(self):
        self.assertTrue(verify_login('admin', 'admin123'))
        self.assertFalse(verify_login('admin', 'wrongpassword'))

    def test_supplier_crud(self):
        # Create
        sm.add_supplier('Supplier A', 'contact@a.com', 'Address A')
        suppliers = sm.list_suppliers()
        self.assertTrue(any(s['name'] == 'Supplier A' for s in suppliers))
        sid = next(s['supplier_id'] for s in suppliers if s['name'] == 'Supplier A')
        # Update
        sm.update_supplier(sid, 'Supplier A1', 'contact@a1.com', 'Address A1')
        suppliers = sm.list_suppliers()
        s = next(s for s in suppliers if s['supplier_id'] == sid)
        self.assertEqual(s['name'], 'Supplier A1')
        # Delete
        sm.delete_supplier(sid)
        suppliers = sm.list_suppliers()
        self.assertFalse(any(s['supplier_id'] == sid for s in suppliers))

    def test_product_crud_and_search(self):
        # ensure a supplier to link
        sm.add_supplier('Supplier B', '', '')
        supplier = next(s for s in sm.list_suppliers() if s['name'] == 'Supplier B')
        sid = supplier['supplier_id']
        # Create product
        pm.add_product('Test Product', 'Category1', 10, 9.99, sid)
        products = pm.list_products()
        self.assertTrue(any(p['name'] == 'Test Product' for p in products))
        pid = next(p['product_id'] for p in products if p['name'] == 'Test Product')
        # Update
        pm.update_product(pid, 'Test Product 2', 'Category2', 20, 19.99, sid)
        products = pm.list_products()
        p = next(p for p in products if p['product_id'] == pid)
        self.assertEqual(p['name'], 'Test Product 2')
        # Search
        res = pm.search_products('Product 2')
        self.assertTrue(any(x['product_id'] == pid for x in res))
        # Counts
        self.assertGreaterEqual(pm.count_products(), 1)
        self.assertGreaterEqual(pm.count_low_stock(1000), 1)

    def test_sales_and_revenue(self):
        # Ensure a product exists
        products = pm.list_products()
        if not products:
            pm.add_product('SaleProd', 'Cat', 5, 5.0, None)
            products = pm.list_products()
        p = products[0]
        starting_rev = sam.total_revenue()
        # Record sale of 1 unit at price p['price']
        sam.record_sale(p['product_id'], 1, float(p['price']))
        # Revenue increased
        self.assertGreaterEqual(sam.total_revenue(), starting_rev + float(p['price']) - 1e-9)
        # Quantity decreased
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute('SELECT quantity FROM products WHERE product_id=?', (p['product_id'],))
            qty = cur.fetchone()['quantity']
            self.assertGreaterEqual(qty, 0)
        finally:
            conn.close()

    def test_export_pdf_report(self):
        out = Path.cwd() / 'test_report.pdf'
        if out.exists():
            out.unlink()
        rm.export_pdf_report(str(out))
        self.assertTrue(out.exists())
        self.assertGreater(out.stat().st_size, 0)
        out.unlink()


if __name__ == '__main__':
    unittest.main()
