import sys
from pathlib import Path
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMessageBox, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QInputDialog,
    QComboBox, QSpinBox, QDoubleSpinBox, QFileDialog
)

from .database.db_init import initialize_database, seed_demo_data
from .modules.auth import verify_login, ensure_default_admin
from .modules import product_manager as pm
from .modules import supplier_manager as sm
from .modules import sales_manager as sam
from .modules import report_manager as rm

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / 'ui'


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(UI_DIR / 'login.ui'), self)
        self.btnLogin.clicked.connect(self.handle_login)

    def handle_login(self):
        username = self.lineUsername.text().strip()
        password = self.linePassword.text().strip()
        if verify_login(username, password):
            self.accept_login()
        else:
            QMessageBox.warning(self, 'Login Failed', 'Invalid username or password')

    def accept_login(self):
        self.hide()
        self.dashboard = DashboardWindow()
        self.dashboard.show()


class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(UI_DIR / 'products.ui'), self)
        self.table: QTableWidget = self.findChild(QTableWidget, 'tableProducts')
        self.btnAdd: QPushButton = self.findChild(QPushButton, 'btnAdd')
        self.btnEdit: QPushButton = self.findChild(QPushButton, 'btnEdit')
        self.btnDelete: QPushButton = self.findChild(QPushButton, 'btnDelete')
        self.btnSearch: QPushButton = self.findChild(QPushButton, 'btnSearch')
        self.lineSearch: QLineEdit = self.findChild(QLineEdit, 'lineSearch')

        self.btnAdd.clicked.connect(self.add_product)
        self.btnEdit.clicked.connect(self.edit_product)
        self.btnDelete.clicked.connect(self.delete_product)
        self.btnSearch.clicked.connect(self.refresh)

        self.setup_table()
        self.refresh()

    def setup_table(self):
        headers = ['ID', 'Name', 'Category', 'Quantity', 'Price', 'Supplier']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        try:
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.verticalHeader().setDefaultSectionSize(28)
        except Exception:
            pass
        self.table.setStyleSheet(
            "QTableWidget::item{padding:8px;} QHeaderView::section{padding:8px; background:#F4F6F8; border:0; border-right:1px solid #E2E6EA;}"
        )

    def refresh(self):
        keyword = (self.lineSearch.text() or '').strip()
        items = pm.search_products(keyword) if keyword else pm.list_products()
        self.table.setRowCount(len(items))
        for r, it in enumerate(items):
            self.table.setItem(r, 0, QTableWidgetItem(str(it['product_id'])))
            self.table.setItem(r, 1, QTableWidgetItem(it['name']))
            self.table.setItem(r, 2, QTableWidgetItem(it.get('category') or ''))
            self.table.setItem(r, 3, QTableWidgetItem(str(it['quantity'])))
            self.table.setItem(r, 4, QTableWidgetItem(f"{it['price']:.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(it.get('supplier_name') or ''))
        self.table.resizeColumnsToContents()

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        # ID column is at index 0
        return int(self.table.item(row, 0).text())

    def add_product(self):
        name, ok = QInputDialog.getText(self, 'Add Product', 'Name:')
        if not ok or not name:
            return
        category, _ = QInputDialog.getText(self, 'Add Product', 'Category:')
        qty, ok = QInputDialog.getInt(self, 'Add Product', 'Quantity:', 0, 0, 100000)
        if not ok:
            return
        price, ok = QInputDialog.getDouble(self, 'Add Product', 'Price:', 0.0, 0, 1e9, 2)
        if not ok:
            return
        # supplier selection
        suppliers = sm.list_suppliers()
        supplier_names = ['None'] + [s['name'] for s in suppliers]
        idx, ok = QInputDialog.getItem(self, 'Add Product', 'Supplier:', supplier_names, 0, False)
        if not ok:
            return
        supplier_id = None
        if idx != 'None':
            # map name to id
            m = {s['name']: s['supplier_id'] for s in suppliers}
            supplier_id = m.get(idx)
        pm.add_product(name, category, qty, price, supplier_id)
        self.refresh()

    def edit_product(self):
        pid = self._get_selected_id()
        if not pid:
            QMessageBox.information(self, 'Edit', 'Select a product row first')
            return
        row = self.table.currentRow()
        name, ok = QInputDialog.getText(self, 'Edit Product', 'Name:', text=self.table.item(row, 1).text())
        if not ok or not name:
            return
        category, _ = QInputDialog.getText(self, 'Edit Product', 'Category:', text=self.table.item(row, 2).text())
        qty, ok = QInputDialog.getInt(self, 'Edit Product', 'Quantity:', int(self.table.item(row, 3).text()), 0, 100000)
        if not ok:
            return
        price, ok = QInputDialog.getDouble(self, 'Edit Product', 'Price:', float(self.table.item(row, 4).text()), 0, 1e9, 2)
        if not ok:
            return
        suppliers = sm.list_suppliers()
        supplier_names = ['None'] + [s['name'] for s in suppliers]
        current_supplier = self.table.item(row, 5).text() or 'None'
        idx_text, ok = QInputDialog.getItem(self, 'Edit Product', 'Supplier:', supplier_names, supplier_names.index(current_supplier) if current_supplier in supplier_names else 0, False)
        if not ok:
            return
        supplier_id = None
        if idx_text != 'None':
            m = {s['name']: s['supplier_id'] for s in suppliers}
            supplier_id = m.get(idx_text)
        pm.update_product(pid, name, category, qty, price, supplier_id)
        self.refresh()

    def delete_product(self):
        pid = self._get_selected_id()
        if not pid:
            QMessageBox.information(self, 'Delete', 'Select a product row first')
            return
        if QMessageBox.question(self, 'Confirm', 'Delete selected product?') == QMessageBox.Yes:
            pm.delete_product(pid)
            self.refresh()


class SuppliersPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(UI_DIR / 'suppliers.ui'), self)
        self.table: QTableWidget = self.findChild(QTableWidget, 'tableSuppliers')
        self.btnAdd: QPushButton = self.findChild(QPushButton, 'btnAdd')
        self.btnEdit: QPushButton = self.findChild(QPushButton, 'btnEdit')
        self.btnDelete: QPushButton = self.findChild(QPushButton, 'btnDelete')
        self.btnAdd.clicked.connect(self.add_supplier)
        self.btnEdit.clicked.connect(self.edit_supplier)
        self.btnDelete.clicked.connect(self.delete_supplier)
        self.setup_table()
        self.refresh()

    def setup_table(self):
        headers = ['ID', 'Name', 'Contact', 'Address']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        try:
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.verticalHeader().setDefaultSectionSize(28)
        except Exception:
            pass
        self.table.setStyleSheet(
            "QTableWidget::item{padding:8px;} QHeaderView::section{padding:8px; background:#F4F6F8; border:0; border-right:1px solid #E2E6EA;}"
        )

    def refresh(self):
        items = sm.list_suppliers()
        self.table.setRowCount(len(items))
        for r, it in enumerate(items):
            self.table.setItem(r, 0, QTableWidgetItem(str(it['supplier_id'])))
            self.table.setItem(r, 1, QTableWidgetItem(it['name']))
            self.table.setItem(r, 2, QTableWidgetItem(it.get('contact') or ''))
            self.table.setItem(r, 3, QTableWidgetItem(it.get('address') or ''))
        self.table.resizeColumnsToContents()

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        # ID column is at index 0
        return int(self.table.item(row, 0).text())

    def add_supplier(self):
        name, ok = QInputDialog.getText(self, 'Add Supplier', 'Name:')
        if not ok or not name:
            return
        contact, _ = QInputDialog.getText(self, 'Add Supplier', 'Contact:')
        address, _ = QInputDialog.getText(self, 'Add Supplier', 'Address:')
        sm.add_supplier(name, contact, address)
        self.refresh()

    def edit_supplier(self):
        sid = self._get_selected_id()
        if not sid:
            QMessageBox.information(self, 'Edit', 'Select a supplier row first')
            return
        row = self.table.currentRow()
        name, ok = QInputDialog.getText(self, 'Edit Supplier', 'Name:', text=self.table.item(row, 1).text())
        if not ok or not name:
            return
        contact, _ = QInputDialog.getText(self, 'Edit Supplier', 'Contact:', text=self.table.item(row, 2).text())
        address, _ = QInputDialog.getText(self, 'Edit Supplier', 'Address:', text=self.table.item(row, 3).text())
        sm.update_supplier(sid, name, contact, address)
        self.refresh()

    def delete_supplier(self):
        sid = self._get_selected_id()
        if not sid:
            QMessageBox.information(self, 'Delete', 'Select a supplier row first')
            return
        if QMessageBox.question(self, 'Confirm', 'Delete selected supplier?') == QMessageBox.Yes:
            sm.delete_supplier(sid)
            self.refresh()


class SalesPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(UI_DIR / 'sales.ui'), self)
        self.comboProduct: QComboBox = self.findChild(QComboBox, 'comboProduct')
        self.spinQty: QSpinBox = self.findChild(QSpinBox, 'spinQty')
        self.spinPrice: QDoubleSpinBox = self.findChild(QDoubleSpinBox, 'spinPrice')
        self.btnRecord: QPushButton = self.findChild(QPushButton, 'btnRecord')
        self.table: QTableWidget = self.findChild(QTableWidget, 'tableSales')
        self.btnRecord.clicked.connect(self.record_sale)
        self.setup_table()
        self.refresh()

    def setup_table(self):
        headers = ['ID', 'Product', 'Quantity', 'Date', 'Total']
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        try:
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.verticalHeader().setDefaultSectionSize(28)
        except Exception:
            pass
        self.table.setStyleSheet(
            "QTableWidget::item{padding:8px;} QHeaderView::section{padding:8px; background:#F4F6F8; border:0; border-right:1px solid #E2E6EA;}"
        )

    def load_products_combo(self):
        self.comboProduct.clear()
        products = pm.list_products()
        for p in products:
            self.comboProduct.addItem(f"{p['name']} (#{p['product_id']})", p)

    def refresh(self):
        self.load_products_combo()
        sales = sam.list_sales()
        self.table.setRowCount(len(sales))
        for r, s in enumerate(sales):
            self.table.setItem(r, 0, QTableWidgetItem(str(s['sale_id'])))
            self.table.setItem(r, 1, QTableWidgetItem(s['product_name']))
            self.table.setItem(r, 2, QTableWidgetItem(str(s['quantity_sold'])))
            self.table.setItem(r, 3, QTableWidgetItem(s['sale_date']))
            self.table.setItem(r, 4, QTableWidgetItem(f"{s['total_amount']:.2f}"))
        self.table.resizeColumnsToContents()

    def record_sale(self):
        idx = self.comboProduct.currentIndex()
        if idx < 0:
            QMessageBox.information(self, 'Sale', 'No products available')
            return
        p = self.comboProduct.itemData(idx)
        qty = self.spinQty.value()
        price = self.spinPrice.value() or float(p['price'])
        try:
            sam.record_sale(p['product_id'], qty, price)
            QMessageBox.information(self, 'Sale', 'Sale recorded')
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, 'Sale Failed', str(e))


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(UI_DIR / 'reports.ui'), self)
        self.btnExportPdf: QPushButton = self.findChild(QPushButton, 'btnExportPdf')
        self.btnExportPdf.clicked.connect(self.export_pdf)

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export PDF', str(Path.home() / 'inventory_report.pdf'), 'PDF Files (*.pdf)')
        if not path:
            return
        try:
            rm.export_pdf_report(path)
            QMessageBox.information(self, 'Export', 'PDF report exported successfully')
        except Exception as e:
            QMessageBox.warning(self, 'Export Failed', str(e))


class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(str(UI_DIR / 'dashboard.ui'), self)
        # placeholders area setup
        self.pageProducts = ProductsPage()
        self.pageSales = SalesPage()
        self.pageSuppliers = SuppliersPage()
        self.pageReports = ReportsPage()

        self.stackedMain: QStackedWidget = self.findChild(QStackedWidget, 'stackedMain')
        self.tableMetrics: QTableWidget = self.findChild(QTableWidget, 'tableMetrics')
        # replace placeholder pages with actual ones
        self.stackedMain.removeWidget(self.stackedMain.widget(1))
        self.stackedMain.insertWidget(1, self.pageProducts)
        self.stackedMain.removeWidget(self.stackedMain.widget(2))
        self.stackedMain.insertWidget(2, self.pageSales)
        self.stackedMain.removeWidget(self.stackedMain.widget(3))
        self.stackedMain.insertWidget(3, self.pageSuppliers)
        self.stackedMain.removeWidget(self.stackedMain.widget(4))
        self.stackedMain.insertWidget(4, self.pageReports)

        # bind sidebar buttons
        self.btnNavDashboard: QPushButton = self.findChild(QPushButton, 'btnNavDashboard')
        self.btnNavProducts: QPushButton = self.findChild(QPushButton, 'btnNavProducts')
        self.btnNavSales: QPushButton = self.findChild(QPushButton, 'btnNavSales')
        self.btnNavSuppliers: QPushButton = self.findChild(QPushButton, 'btnNavSuppliers')
        self.btnNavReports: QPushButton = self.findChild(QPushButton, 'btnNavReports')
        self.btnLogout: QPushButton = self.findChild(QPushButton, 'btnLogout')

        self._setup_metrics_table()

        self.btnNavDashboard.clicked.connect(lambda: self.stackedMain.setCurrentIndex(0))
        self.btnNavProducts.clicked.connect(lambda: self._switch(1))
        self.btnNavSales.clicked.connect(lambda: self._switch(2))
        self.btnNavSuppliers.clicked.connect(lambda: self._switch(3))
        self.btnNavReports.clicked.connect(lambda: self._switch(4))
        self.btnLogout.clicked.connect(self.logout)

        self.refresh_metrics()

    def _switch(self, idx: int):
        self.stackedMain.setCurrentIndex(idx)
        if idx == 1:
            self.pageProducts.refresh()
        elif idx == 2:
            self.pageSales.refresh()
        elif idx == 3:
            self.pageSuppliers.refresh()
        elif idx == 4:
            pass
        self.refresh_metrics()

    def refresh_metrics(self):
        total_products = pm.count_products()
        revenue = sam.total_revenue()
        low_stock = pm.count_low_stock()
        if not self.tableMetrics:
            return
        rows = [
            ('Total Products', str(total_products)),
            ('Total Revenue', f"{revenue:.2f}"),
            ('Low Stock', str(low_stock)),
        ]
        self.tableMetrics.setRowCount(len(rows))
        for r, (metric, value) in enumerate(rows):
            self.tableMetrics.setItem(r, 0, QTableWidgetItem(metric))
            self.tableMetrics.setItem(r, 1, QTableWidgetItem(value))
        self.tableMetrics.resizeColumnsToContents()

    def _setup_metrics_table(self):
        if not self.tableMetrics:
            return
        headers = ['Metric', 'Value']
        self.tableMetrics.setColumnCount(len(headers))
        self.tableMetrics.setHorizontalHeaderLabels(headers)
        self.tableMetrics.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tableMetrics.setSelectionBehavior(QTableWidget.SelectRows)
        self.tableMetrics.setAlternatingRowColors(True)
        try:
            self.tableMetrics.horizontalHeader().setStretchLastSection(True)
            self.tableMetrics.verticalHeader().setDefaultSectionSize(28)
        except Exception:
            pass
        self.tableMetrics.setStyleSheet(
            "QTableWidget::item{padding:8px;} QHeaderView::section{padding:8px; background:#F4F6F8; border:0; border-right:1px solid #E2E6EA;}"
        )

    def logout(self):
        self.close()
        self.login = LoginWindow()
        self.login.show()


def main():
    # Initialize DB and default admin
    initialize_database()
    ensure_default_admin()
    # Seed demo stationery data if empty
    seed_demo_data()
    app = QApplication(sys.argv)
    # Premium light theme with black text
    app.setStyleSheet(
        """
        /* Base */
        QWidget { font-family: Segoe UI, Arial; font-size: 11pt; color: #111417; background: #FFFFFF; }
        QFrame#sidebar { background: #F4F6F8; }
        QLabel#labelBrand { color: #0078D7; }

        /* Buttons */
        QPushButton { background: #E9EEF5; color: #111417; border: 1px solid #D5DCE3; border-radius: 6px; padding: 8px 12px; }
        QPushButton:hover { background: #DCE6F2; }
        QPushButton:pressed { background: #CFDBEB; }
        QPushButton#btnLogout { background: #F0F2F5; color: #111417; }

        /* Inputs */
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            border: 1px solid #D5DCE3; border-radius: 6px; padding: 6px 8px; background: #FFFFFF; color: #111417;
        }
        QComboBox QAbstractItemView { background: #FFFFFF; color: #111417; selection-background-color: #E9EEF5; }

        /* Tables */
        QTableWidget { gridline-color: #E2E6EA; background: #FFFFFF; alternate-background-color: #FAFBFC; color: #111417; }
        QHeaderView::section { background: #F4F6F8; color: #4B5563; border: 0; border-right: 1px solid #E2E6EA; padding: 10px; font-weight: 700; }
        QTableWidget::item { padding: 10px; }
        QTableCornerButton::section { background: #F4F6F8; border: 0; }

        /* Scrollbars */
        QScrollBar:vertical { background: #FFFFFF; width: 12px; margin: 0; }
        QScrollBar::handle:vertical { background: #D5DCE3; min-height: 24px; border-radius: 6px; }
        QScrollBar:horizontal { background: #FFFFFF; height: 12px; margin: 0; }
        QScrollBar::handle:horizontal { background: #D5DCE3; min-width: 24px; border-radius: 6px; }

        /* Messages */
        QMessageBox { background-color: #FFFFFF; }
        """
    )
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
