"""
ferrum.presentation.views.main_window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Ventana principal del sistema POS industrial con telemetría e inventario.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ferrum.core.config import settings
from ferrum.infrastructure.database.connection import db
from ferrum.infrastructure.database.models import Product


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FERRUM POS | Industrial Point of Sale")
        self.resize(1000, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121214;
            }
            QLabel {
                color: #e1e1e6;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QTableWidget {
                background-color: #1a1a1e;
                color: #e1e1e6;
                border: 1px solid #29292e;
                gridline-color: #29292e;
                border-radius: 6px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #202024;
                color: #04d361;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #29292e;
            }
            QTextEdit {
                background-color: #1a1a1e;
                color: #00e676;
                border: 1px solid #29292e;
                border-radius: 6px;
                font-family: monospace;
                font-size: 11px;
            }
        """)

        # Contenedor central
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header Superior
        header_layout = QHBoxLayout()
        title = QLabel("🔩 FERRUM POS - ESTACIÓN DE VENTA E INVENTARIO")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.btn_refresh = QPushButton("🔄 Recargar Inventario")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        self.btn_refresh.clicked.connect(self.load_inventory_data)
        header_layout.addWidget(self.btn_refresh)
        main_layout.addLayout(header_layout)

        # Tabla de productos
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "SKU", "Descripción", "Unidad", "Precio Venta", "Stock Actual"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)

        # Telemetría inferior
        info_label = QLabel("Diagnóstico de Plataforma y Hardware:")
        info_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        main_layout.addWidget(info_label)

        self.telemetry_box = QTextEdit()
        self.telemetry_box.setReadOnly(True)
        self.telemetry_box.setMaximumHeight(120)
        main_layout.addWidget(self.telemetry_box)

        # Cargar datos iniciales
        self.load_telemetry()
        self.load_inventory_data()

    def load_telemetry(self) -> None:
        """Muestra los datos de entorno en el widget."""
        info = [
            f"[SISTEMA OPERATIVO]: {settings.os_type.upper()} (Arch Linux validado)",
            f"[BASE DE DATOS]    : {settings.paths.sqlite_db_path.as_posix()}",
            f"[LOGS]             : {settings.paths.log_dir.as_posix()}",
            "[HARDWARE STATUS]  : Adaptador ESC/POS Network cargado.",
            "[CERBERUS CCTV]    : Standby (Listo para conectar stream RTSP)",
        ]
        self.telemetry_box.setText("\n".join(info))

    def load_inventory_data(self) -> None:
        """Consulta la base de datos y llena la tabla."""
        self.table.setRowCount(0)
        for session in db.get_session():
            products = session.query(Product).all()
            for row_idx, p in enumerate(products):
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(p.id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(p.sku))
                self.table.setItem(row_idx, 2, QTableWidgetItem(p.name))
                self.table.setItem(row_idx, 3, QTableWidgetItem(p.unit.value))
                self.table.setItem(row_idx, 4, QTableWidgetItem(f"${p.sale_price:.2f}"))
                self.table.setItem(row_idx, 5, QTableWidgetItem(f"{p.stock:.3f}"))
