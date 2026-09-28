"""
ferrum.presentation.views.main_window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Vista moderna e industrial para FERRUM POS.
"""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ferrum.core.config import settings
from ferrum.infrastructure.database.connection import db
from ferrum.infrastructure.database.models import Product


class KPICard(QFrame):
    """Tarjeta de resumen de métricas."""
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
        self.setWindowTitle("FERRUM POS — Control Industrial")
        self.resize(1150, 700)
        self.setMinimumSize(950, 600)

        # Cargar estilos QSS externos
        self._load_stylesheet()

        # Layout Raíz (Horizontal: Sidebar + Contenido)
        root_widget = QWidget(self)
        self.setCentralWidget(root_widget)
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Sidebar de navegación
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # 2. Área principal de contenido
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(28, 24, 28, 0)
        content_layout.setSpacing(20)

        # Header de sección
        header_layout = QHBoxLayout()
        view_title = QLabel("Inventario General")
        view_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc;")
        header_layout.addWidget(view_title)
        header_layout.addStretch()

        self.btn_refresh = QPushButton("Recargar Datos")
        self.btn_refresh.setObjectName("btn_primary")
        self.btn_refresh.clicked.connect(self.load_inventory_data)
        header_layout.addWidget(self.btn_refresh)
        content_layout.addLayout(header_layout)

        # Tarjetas resumen (KPIs)
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(16)
        self.card_total_items = KPICard("Total de Productos", "0")
        self.card_stock_value = KPICard("Valor de Inventario", "$0.00")
        self.card_system_mode = KPICard("Modo de Operación", "OFFLINE (SQLite)")
        self.kpi_layout.addWidget(self.card_total_items)
        self.kpi_layout.addWidget(self.card_stock_value)
        self.kpi_layout.addWidget(self.card_system_mode)
        content_layout.addLayout(self.kpi_layout)

        # Tabla de productos
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "SKU", "Descripción del Producto", "Unidad", "Costo", "Precio Venta", "Stock Disponible"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        content_layout.addWidget(self.table)

        # Barra de estado inferior discreta
        status_bar = self._build_status_bar()
        content_layout.addWidget(status_bar)

        root_layout.addWidget(content_wrapper, stretch=1)

        # Cargar datos desde SQLite
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

        # Logo / Marca
        brand_icon = QLabel("FERRUM")
        brand_icon.setObjectName("brand_title")
        brand_sub = QLabel("Industrial POS & CCTV")
        brand_sub.setObjectName("brand_subtitle")
        layout.addWidget(brand_icon)
        layout.addWidget(brand_sub)
        layout.addSpacing(24)

        # Botones de secciones
        btn_pos = QPushButton("🛒  Punto de Venta")
        btn_pos.setProperty("class", "nav_button")
        
        btn_inv = QPushButton("📦  Inventario")
        btn_inv.setProperty("class", "nav_button")
        btn_inv.setChecked(True)  # Activo por defecto

        btn_cctv = QPushButton("📹  Cerberus CCTV")
        btn_cctv.setProperty("class", "nav_button")

        btn_cfg = QPushButton("⚙️  Configuración")
        btn_cfg.setProperty("class", "nav_button")

        for b in [btn_pos, btn_inv, btn_cctv, btn_cfg]:
            layout.addWidget(b)

        layout.addStretch()

        # Versión en el pie del sidebar
        ver_lbl = QLabel("v0.1.0-alpha")
        ver_lbl.setStyleSheet("color: #475569; font-size: 11px;")
        layout.addWidget(ver_lbl)

        return sidebar

    def _build_status_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("status_bar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(4, 6, 4, 6)

        status_left = QLabel(f"● SISTEMA ACTIVO: Arch Linux ({settings.os_type})")
        status_left.setProperty("class", "status_text")
        status_left.setStyleSheet("color: #10b981; font-weight: bold;")

        status_right = QLabel(f"DB: {settings.paths.sqlite_db_path.name}")
        status_right.setProperty("class", "status_text")

        layout.addWidget(status_left)
        layout.addStretch()
        layout.addWidget(status_right)
        return bar

    def load_inventory_data(self) -> None:
        """Carga y recalcula métricas."""
        self.table.setRowCount(0)
        total_items = 0
        total_value = 0.0

        for session in db.get_session():
            products = session.query(Product).all()
            total_items = len(products)

            for row, p in enumerate(products):
                self.table.insertRow(row)
                total_value += float(p.stock) * float(p.sale_price)

                # Celda SKU
                item_sku = QTableWidgetItem(p.sku)
                item_sku.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item_sku)

                # Descripción
                self.table.setItem(row, 1, QTableWidgetItem(p.name))

                # Unidad
                item_unit = QTableWidgetItem(f"  {p.unit.value}  ")
                item_unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, item_unit)

                # Costo
                item_cost = QTableWidgetItem(f"${p.cost_price:.2f}")
                item_cost.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, item_cost)

                # Venta
                item_price = QTableWidgetItem(f"${p.sale_price:.2f}")
                item_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, item_price)

                # Stock
                item_stock = QTableWidgetItem(f"{p.stock:.3f}")
                item_stock.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 5, item_stock)

        # Actualizar Tarjetas KPI
        self.card_total_items.lbl_value.setText(str(total_items))
        self.card_stock_value.lbl_value.setText(f"${total_value:,.2f}")
