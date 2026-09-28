"""
ferrum.presentation.components.product_modal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modal limpio sin botones de flechas laterales en campos numéricos.
"""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ferrum.application.services.inventory_service import InventoryService, NewProductDTO
from ferrum.infrastructure.database.models import UnitOfMeasure


class ProductModal(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar Nuevo Producto")
        self.resize(520, 440)
        self.setModal(True)
        self._load_stylesheet()
        self._setup_ui()

    def _load_stylesheet(self) -> None:
        qss_path = Path(__file__).resolve().parent.parent / "assets" / "style.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("🔩 REGISTRO DE ARTÍCULO (COLOMBIA - COP)")
        title.setStyleSheet("font-size: 15px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # SKU
        lbl_sku = QLabel("SKU / Código:")
        grid.addWidget(lbl_sku, 0, 0)
        self.input_sku = QLineEdit()
        self.input_sku.setPlaceholderText("Ej: CAB-001, PUN-002")
        grid.addWidget(self.input_sku, 0, 1)

        # Código de Barras
        lbl_barcode = QLabel("Código de Barras:")
        grid.addWidget(lbl_barcode, 1, 0)
        self.input_barcode = QLineEdit()
        self.input_barcode.setPlaceholderText("Opcional (Usa el SKU)")
        grid.addWidget(self.input_barcode, 1, 1)

        # Descripción
        lbl_name = QLabel("Descripción:")
        grid.addWidget(lbl_name, 2, 0)
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Ej: Puntilla 2 pulg con cabeza")
        grid.addWidget(self.input_name, 2, 1)

        # Unidad
        lbl_unit = QLabel("Unidad de Medida:")
        grid.addWidget(lbl_unit, 3, 0)
        self.combo_unit = QComboBox()
        for u in UnitOfMeasure:
            self.combo_unit.addItem(u.value, u)
        grid.addWidget(self.combo_unit, 3, 1)

        # Costo (Sin flechas, campo limpio)
        lbl_cost = QLabel("Precio Costo (COP $):")
        grid.addWidget(lbl_cost, 4, 0)
        self.spin_cost = QSpinBox()
        self.spin_cost.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_cost.setRange(0, 500000000)
        self.spin_cost.setValue(0)
        grid.addWidget(self.spin_cost, 4, 1)

        # Venta (Sin flechas, campo limpio)
        lbl_price = QLabel("Precio Venta (COP $):")
        grid.addWidget(lbl_price, 5, 0)
        self.spin_price = QSpinBox()
        self.spin_price.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_price.setRange(0, 500000000)
        self.spin_price.setValue(0)
        grid.addWidget(self.spin_price, 5, 1)

        # Stock (Sin flechas)
        lbl_stock = QLabel("Stock Inicial:")
        grid.addWidget(lbl_stock, 6, 0)
        self.spin_stock = QDoubleSpinBox()
        self.spin_stock.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_stock.setRange(0.0, 999999.0)
        self.spin_stock.setDecimals(2)
        self.spin_stock.setValue(10.0)
        grid.addWidget(self.spin_stock, 6, 1)

        layout.addLayout(grid)
        layout.addSpacing(6)

        # Botones
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Guardar Producto")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #042f2e;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 800;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
                color: #ffffff;
            }
        """)
        btn_save.clicked.connect(self._save_product)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def _save_product(self) -> None:
        selected_unit = self.combo_unit.currentData()
        dto = NewProductDTO(
            sku=self.input_sku.text(),
            name=self.input_name.text(),
            unit=selected_unit,
            cost_price=float(self.spin_cost.value()),
            sale_price=float(self.spin_price.value()),
            initial_stock=float(self.spin_stock.value()),
            barcode_value=self.input_barcode.text() if self.input_barcode.text().strip() else None
        )

        ok, msg, prod = InventoryService.create_product(dto)
        if ok:
            QMessageBox.information(self, "Éxito", msg)
            self.accept()
        else:
            QMessageBox.warning(self, "Validación", msg)
