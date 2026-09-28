"""
ferrum.presentation.views.pos_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Terminal de cobro con campos limpios y moneda COP.
"""
from typing import List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ferrum.application.services.sale_service import CartItemDTO, SaleService


class POSView(QWidget):
    def __init__(self, on_sale_completed_callback=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.on_sale_completed_callback = on_sale_completed_callback
        self.cart: List[CartItemDTO] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Panel Izquierdo
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(14)

        # Barra de ingreso
        input_bar = QFrame()
        input_bar.setStyleSheet("""
            QFrame {
                background-color: #131d31;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        input_layout = QHBoxLayout(input_bar)
        input_layout.setSpacing(10)

        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Escanear Código o SKU (ej. CAB-001, PUN-002)...")
        self.input_search.returnPressed.connect(self.add_product_to_cart)
        input_layout.addWidget(self.input_search, stretch=3)

        lbl_qty = QLabel("Cant:")
        lbl_qty.setStyleSheet("font-weight: 700; color: #94a3b8;")
        input_layout.addWidget(lbl_qty)

        self.spin_qty = QDoubleSpinBox()
        self.spin_qty.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_qty.setRange(0.01, 9999.0)
        self.spin_qty.setValue(1.0)
        self.spin_qty.setDecimals(2)
        self.spin_qty.setStyleSheet("color: #38bdf8; font-size: 14px; font-weight: bold;")
        input_layout.addWidget(self.spin_qty, stretch=1)

        btn_add = QPushButton("➕ Agregar")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self.add_product_to_cart)
        input_layout.addWidget(btn_add)

        left_layout.addWidget(input_bar)

        # Tabla de Carrito
        self.table_cart = QTableWidget()
        self.table_cart.setColumnCount(6)
        self.table_cart.setHorizontalHeaderLabels([
            "SKU", "Descripción", "Cantidad", "Unidad", "Precio Unitario", "Subtotal"
        ])
        
        h = self.table_cart.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table_cart.verticalHeader().setVisible(False)
        self.table_cart.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.table_cart)

        btn_remove = QPushButton("🗑️ Eliminar Ítem Seleccionado")
        btn_remove.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ef4444;
                border: 1px solid #7f1d1d;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #450a0a;
            }
        """)
        btn_remove.clicked.connect(self.remove_selected_item)
        left_layout.addWidget(btn_remove, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(left_panel, stretch=2)

        # Panel Derecho (Cobro COP)
        checkout_panel = QFrame()
        checkout_panel.setStyleSheet("""
            QFrame {
                background-color: #131d31;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        checkout_layout = QVBoxLayout(checkout_panel)
        checkout_layout.setContentsMargins(20, 24, 20, 24)
        checkout_layout.setSpacing(16)

        lbl_checkout = QLabel("CAJA REGISTRADORA (COP)")
        lbl_checkout.setStyleSheet("font-size: 13px; font-weight: 800; color: #94a3b8; letter-spacing: 1px;")
        checkout_layout.addWidget(lbl_checkout)

        total_card = QFrame()
        total_card.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 14px; border: 1px solid #334155;")
        total_card_layout = QVBoxLayout(total_card)
        
        lbl_total_title = QLabel("TOTAL A COBRAR")
        lbl_total_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        self.lbl_grand_total = QLabel("$ 0")
        self.lbl_grand_total.setStyleSheet("color: #10b981; font-size: 32px; font-weight: 900;")
        total_card_layout.addWidget(lbl_total_title)
        total_card_layout.addWidget(self.lbl_grand_total)
        checkout_layout.addWidget(total_card)

        grid_pay = QGridLayout()
        grid_pay.setSpacing(12)

        lbl_received = QLabel("Efectivo Recibido ($):")
        lbl_received.setStyleSheet("font-size: 13px; font-weight: 600; color: #cbd5e1;")
        
        self.input_cash = QLineEdit()
        self.input_cash.setPlaceholderText("Ej: 50000")
        self.input_cash.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        self.input_cash.textChanged.connect(self.calculate_change)

        lbl_change_title = QLabel("Cambio / Vuelto:")
        lbl_change_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #cbd5e1;")
        
        self.lbl_change = QLabel("$ 0")
        self.lbl_change.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8;")

        grid_pay.addWidget(lbl_received, 0, 0)
        grid_pay.addWidget(self.input_cash, 0, 1)
        grid_pay.addWidget(lbl_change_title, 1, 0)
        grid_pay.addWidget(self.lbl_change, 1, 1)
        checkout_layout.addLayout(grid_pay)

        checkout_layout.addStretch()

        self.btn_pay = QPushButton("💳  PROCESAR VENTA")
        self.btn_pay.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #042f2e;
                border: none;
                border-radius: 8px;
                padding: 16px;
                font-size: 15px;
                font-weight: 900;
            }
            QPushButton:hover {
                background-color: #059669;
                color: #ffffff;
            }
        """)
        self.btn_pay.clicked.connect(self.complete_sale)
        checkout_layout.addWidget(self.btn_pay)

        main_layout.addWidget(checkout_panel, stretch=1)

    def add_product_to_cart(self) -> None:
        query = self.input_search.text().strip()
        if not query:
            return

        qty = float(self.spin_qty.value())
        product = SaleService.get_product_by_identifier(query)

        if not product:
            QMessageBox.warning(self, "No Encontrado", f"No existe ningún producto con el código: '{query}'")
            return

        if product.stock < qty:
            QMessageBox.warning(
                self,
                "Stock Insuficiente",
                f"El producto '{product.name}' solo tiene {product.stock:.2f} {product.unit.value} disponibles."
            )
            return

        item_dto = CartItemDTO(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            quantity=qty,
            unit_price=float(product.sale_price),
            unit=product.unit.value
        )
        self.cart.append(item_dto)

        self.input_search.clear()
        self.spin_qty.setValue(1.0)
        self.input_search.setFocus()
        self._refresh_cart_table()

    def remove_selected_item(self) -> None:
        current_row = self.table_cart.currentRow()
        if current_row >= 0 and current_row < len(self.cart):
            self.cart.pop(current_row)
            self._refresh_cart_table()

    def _refresh_cart_table(self) -> None:
        self.table_cart.setRowCount(0)
        total = 0.0

        for row, item in enumerate(self.cart):
            self.table_cart.insertRow(row)
            total += item.subtotal

            self.table_cart.setItem(row, 0, QTableWidgetItem(f" {item.sku} "))
            self.table_cart.setItem(row, 1, QTableWidgetItem(f" {item.name}"))
            
            qty_item = QTableWidgetItem(f"{item.quantity:.2f} ")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_cart.setItem(row, 2, qty_item)

            unit_item = QTableWidgetItem(f" {item.unit} ")
            unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_cart.setItem(row, 3, unit_item)

            price_item = QTableWidgetItem(f"${item.unit_price:,.0f} ".replace(",", "."))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_cart.setItem(row, 4, price_item)

            sub_item = QTableWidgetItem(f"${item.subtotal:,.0f} ".replace(",", "."))
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_cart.setItem(row, 5, sub_item)

        total_fmt = f"${total:,.0f}".replace(",", ".")
        self.lbl_grand_total.setText(total_fmt)
        self.calculate_change()

    def calculate_change(self) -> None:
        total = sum(i.subtotal for i in self.cart)
        cash_text = self.input_cash.text().strip().replace(".", "").replace(",", "")
        try:
            cash = float(cash_text) if cash_text else 0.0
            change = cash - total
            if change >= 0 and total > 0:
                self.lbl_change.setText(f"${change:,.0f}".replace(",", "."))
                self.lbl_change.setStyleSheet("font-size: 20px; font-weight: 800; color: #10b981;")
            else:
                self.lbl_change.setText("$ 0")
                self.lbl_change.setStyleSheet("font-size: 20px; font-weight: 800; color: #ef4444;")
        except ValueError:
            self.lbl_change.setText("$ 0")

    def complete_sale(self) -> None:
        if not self.cart:
            QMessageBox.warning(self, "Carrito Vacío", "No hay productos en la orden de venta.")
            return

        total = sum(i.subtotal for i in self.cart)
        cash_text = self.input_cash.text().strip().replace(".", "").replace(",", "")
        cash = float(cash_text) if cash_text else 0.0

        if cash < total:
            QMessageBox.warning(self, "Pago Insuficiente", "El dinero recibido es menor al total a cobrar.")
            return

        ok, msg, sale = SaleService.process_sale(self.cart)
        if ok and sale:
            change_val = cash - total
            QMessageBox.information(
                self,
                "Venta Exitosa",
                f"✅ {msg}\n\nTotal Cobrado: ${total:,.0f}\nCambio entregado: ${change_val:,.0f}".replace(",", ".")
            )
            self.cart.clear()
            self.input_cash.clear()
            self._refresh_cart_table()

            if self.on_sale_completed_callback:
                self.on_sale_completed_callback()
        else:
            QMessageBox.critical(self, "Error de Venta", f"❌ {msg}")
