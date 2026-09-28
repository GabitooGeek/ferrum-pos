"""
ferrum.presentation.views.main_window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ventana principal con inventario en números enteros limpios.
"""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ferrum.core.config import settings
from ferrum.infrastructure.database.connection import db
from ferrum.infrastructure.database.models import Product
from ferrum.presentation.components.product_modal import ProductModal
from ferrum.presentation.views.cctv_view import CCTVView
from ferrum.presentation.views.pos_view import POSView
from ferrum.presentation.views.reports_view import ReportsView


class KPICard(QFrame):
    def __init__(self, title: str, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "kpi_card")
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 12, 16, 12)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "kpi_title")
        self.lbl_value = QLabel(value)
        self.lbl_value.setProperty("class", "kpi_value")

        layout.addWidget(lbl_title)
        layout.addWidget(self.lbl_value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FERRUM POS — Control Industrial (Colombia COP)")
        self.resize(1200, 720)
        self.setMinimumSize(1050, 640)

        self._load_stylesheet()

        root_widget = QWidget(self)
        self.setCentralWidget(root_widget)
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.view_pos = POSView(on_sale_completed_callback=self._on_sale_completed)
        self.view_inventory = self._build_inventory_view()
        self.view_cctv = CCTVView()
        self.view_reports = ReportsView()

        self.stack.addWidget(self.view_pos)        # 0
        self.stack.addWidget(self.view_inventory)  # 1
        self.stack.addWidget(self.view_reports)    # 2
        self.stack.addWidget(self.view_cctv)       # 3

        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(28, 20, 28, 0)
        content_layout.setSpacing(16)

        content_layout.addWidget(self.stack, stretch=1)

        status_bar = self._build_status_bar()
        content_layout.addWidget(status_bar)

        root_layout.addWidget(content_container, stretch=1)

        self.load_inventory_data()

    def _load_stylesheet(self) -> None:
        qss_path = Path(__file__).resolve().parent.parent / "assets" / "style.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)

        brand_icon = QLabel("FERRUM")
        brand_icon.setObjectName("brand_title")
        brand_sub = QLabel("Industrial POS & CCTV")
        brand_sub.setObjectName("brand_subtitle")
        layout.addWidget(brand_icon)
        layout.addWidget(brand_sub)
        layout.addSpacing(24)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_pos = QPushButton("🛒  Punto de Venta")
        self.btn_pos.setCheckable(True)
        self.btn_pos.setChecked(True)
        self.btn_pos.setProperty("class", "nav_button")
        self.btn_pos.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.btn_inv = QPushButton("📦  Inventario")
        self.btn_inv.setCheckable(True)
        self.btn_inv.setProperty("class", "nav_button")
        self.btn_inv.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        self.btn_rep = QPushButton("📊  Cierre de Caja")
        self.btn_rep.setCheckable(True)
        self.btn_rep.setProperty("class", "nav_button")
        self.btn_rep.clicked.connect(self._open_reports_tab)

        self.btn_cctv = QPushButton("📹  Cerberus CCTV")
        self.btn_cctv.setCheckable(True)
        self.btn_cctv.setProperty("class", "nav_button")
        self.btn_cctv.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        self.nav_group.addButton(self.btn_pos)
        self.nav_group.addButton(self.btn_inv)
        self.nav_group.addButton(self.btn_rep)
        self.nav_group.addButton(self.btn_cctv)

        layout.addWidget(self.btn_pos)
        layout.addWidget(self.btn_inv)
        layout.addWidget(self.btn_rep)
        layout.addWidget(self.btn_cctv)
        layout.addStretch()

        ver_lbl = QLabel("v0.1.0-alpha (COP)")
        ver_lbl.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(ver_lbl)

        return sidebar

    def _open_reports_tab(self) -> None:
        self.view_reports.load_report_data()
        self.stack.setCurrentIndex(2)

    def _build_inventory_view(self) -> QWidget:
        view = QWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        view_title = QLabel("Control de Inventario")
        view_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")
        header_layout.addWidget(view_title)
        header_layout.addStretch()

        btn_new = QPushButton("➕ Nuevo Producto")
        btn_new.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #042f2e;
                border: none;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: 800;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
                color: #ffffff;
            }
        """)
        btn_new.clicked.connect(self._open_new_product_modal)
        header_layout.addWidget(btn_new)

        btn_refresh = QPushButton("Recargar")
        btn_refresh.setObjectName("btn_primary")
        btn_refresh.clicked.connect(self.load_inventory_data)
        header_layout.addWidget(btn_refresh)
        layout.addLayout(header_layout)

        # KPIs
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(14)
        self.card_total_items = KPICard("Total de Productos", "0")
        self.card_stock_value = KPICard("Valor Inventario (COP)", "$ 0")
        self.card_system_mode = KPICard("Modo de Operación", "OFFLINE (SQLite)")
        self.kpi_layout.addWidget(self.card_total_items)
        self.kpi_layout.addWidget(self.card_stock_value)
        self.kpi_layout.addWidget(self.card_system_mode)
        layout.addLayout(self.kpi_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "SKU", "Descripción del Producto", "Unidad", "Costo Unit. (COP)", "Precio Venta (COP)", "Stock Disponible"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        return view

    def _open_new_product_modal(self) -> None:
        modal = ProductModal(self)
        if modal.exec():
            self.load_inventory_data()

    def _build_status_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("status_bar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(4, 6, 4, 6)

        status_left = QLabel(f"● SISTEMA ACTIVO: Arch Linux | Moneda: COP ($)")
        status_left.setStyleSheet("color: #10b981; font-weight: bold; font-family: monospace; font-size: 11px;")

        status_right = QLabel(f"DB: {settings.paths.sqlite_db_path.name}")
        status_right.setStyleSheet("color: #64748b; font-family: monospace; font-size: 11px;")

        layout.addWidget(status_left)
        layout.addStretch()
        layout.addWidget(status_right)
        return bar

    def _on_sale_completed(self) -> None:
        self.load_inventory_data()
        self.view_reports.load_report_data()

    def load_inventory_data(self) -> None:
        self.table.setRowCount(0)
        total_items = 0
        total_value = 0.0

        for session in db.get_session():
            products = session.query(Product).all()
            total_items = len(products)

            for row, p in enumerate(products):
                self.table.insertRow(row)
                total_value += float(p.stock) * float(p.sale_price)

                # SKU
                item_sku = QTableWidgetItem(f" {p.sku} ")
                item_sku.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item_sku)

                # Descripción
                self.table.setItem(row, 1, QTableWidgetItem(f" {p.name}"))

                # Unidad
                item_unit = QTableWidgetItem(f" {p.unit.value} ")
                item_unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, item_unit)

                # Costo COP entero
                item_cost = QTableWidgetItem(f"${p.cost_price:,.0f} ".replace(",", "."))
                item_cost.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, item_cost)

                # Precio Venta COP entero
                item_price = QTableWidgetItem(f"${p.sale_price:,.0f} ".replace(",", "."))
                item_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, item_price)

                # Stock en Entero Limpio (ej: 148, 50, 12)
                item_stock = QTableWidgetItem(f"{int(p.stock)} ")
                item_stock.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 5, item_stock)

        self.card_total_items.lbl_value.setText(str(total_items))
        self.card_stock_value.lbl_value.setText(f"${total_value:,.0f}".replace(",", "."))

    def closeEvent(self, event) -> None:
        self.view_cctv.stop_stream()
        super().closeEvent(event)
