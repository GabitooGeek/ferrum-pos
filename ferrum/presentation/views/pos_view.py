"""
ferrum.presentation.views.pos_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Terminal de cobro completa con métodos de pago colombianos (Efectivo, Nequi, Tarjeta, Fiado, Mixto).
"""
from typing import List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ferrum.application.services.sale_service import CartItemDTO, PaymentInfoDTO, SaleService
from ferrum.infrastructure.database.models import PaymentMethod
from ferrum.presentation.components.receipt_modal import ReceiptModal


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

        # =========================================================================
        # PANEL IZQUIERDO: Buscador de Pistola Láser y Carrito
        # =========================================================================
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
        self.input_search.setPlaceholderText("🔴 Listo para pistola láser o SKU (ej. CAB-001, PUN-002)...")
        self.input_search.returnPressed.connect(self.add_product_to_cart)
        input_layout.addWidget(self.input_search, stretch=3)

        lbl_qty = QLabel("Cant:")
        lbl_qty.setStyleSheet("font-weight: 700; color: #94a3b8;")
        input_layout.addWidget(lbl_qty)

        self.spin_qty = QSpinBox()
        self.spin_qty.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_qty.setRange(1, 10000)
        self.spin_qty.setValue(1)
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

        # =========================================================================
        # PANEL DERECHO: Métodos de Pago Colombianos y Cobro
        # =========================================================================
        checkout_panel = QFrame()
        checkout_panel.setStyleSheet("""
            QFrame {
                background-color: #131d31;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
        """)
        checkout_layout = QVBoxLayout(checkout_panel)
        checkout_layout.setContentsMargins(20, 20, 20, 20)
        checkout_layout.setSpacing(14)

        lbl_checkout = QLabel("CAJA REGISTRADORA (COP)")
        lbl_checkout.setStyleSheet("font-size: 13px; font-weight: 800; color: #94a3b8; letter-spacing: 1px;")
        checkout_layout.addWidget(lbl_checkout)

        # Tarjeta de Gran Total
        total_card = QFrame()
        total_card.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 12px; border: 1px solid #334155;")
        total_card_layout = QVBoxLayout(total_card)
        
        lbl_total_title = QLabel("TOTAL A COBRAR")
        lbl_total_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        self.lbl_grand_total = QLabel("$ 0")
        self.lbl_grand_total.setStyleSheet("color: #10b981; font-size: 28px; font-weight: 900;")
        total_card_layout.addWidget(lbl_total_title)
        total_card_layout.addWidget(self.lbl_grand_total)
        checkout_layout.addWidget(total_card)

        # Selector de Método de Pago
        lbl_method = QLabel("Forma de Pago:")
        lbl_method.setStyleSheet("font-size: 12px; font-weight: 700; color: #cbd5e1;")
        checkout_layout.addWidget(lbl_method)

        self.combo_payment = QComboBox()
        self.combo_payment.addItem("💵  Efectivo", PaymentMethod.CASH)
        self.combo_payment.addItem("📲  Nequi / Daviplata", PaymentMethod.NEQUI_DAVIPLATA)
        self.combo_payment.addItem("💳  Tarjeta / Datáfono", PaymentMethod.CARD)
        self.combo_payment.addItem("📝  Crédito / Fiado", PaymentMethod.CREDIT)
        self.combo_payment.addItem("🔀  Pago Mixto (Efectivo + Transf.)", PaymentMethod.MIXED)
        self.combo_payment.currentIndexChanged.connect(self._on_payment_method_changed)
        checkout_layout.addWidget(self.combo_payment)

        # Campos Dinámicos de Pago
        self.grid_pay = QGridLayout()
        self.grid_pay.setSpacing(10)

        # 1. Campo Efectivo Recibido
        self.lbl_cash = QLabel("Efectivo Recibido ($):")
        self.lbl_cash.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.input_cash = QLineEdit()
        self.input_cash.setPlaceholderText("Ej: 50000")
        self.input_cash.textChanged.connect(self.calculate_change)

        # 2. Campo Cambio / Vuelto
        self.lbl_change_title = QLabel("Cambio / Vuelto:")
        self.lbl_change_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.lbl_change = QLabel("$ 0")
        self.lbl_change.setStyleSheet("font-size: 18px; font-weight: 800; color: #38bdf8;")

        # 3. Campo Referencia (Nequi / Voucher)
        self.lbl_ref = QLabel("Comprobante / Aprobación:")
        self.lbl_ref.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.input_ref = QLineEdit()
        self.input_ref.setPlaceholderText("Ej: M192839")

        # 4. Campo Cliente (Para Fiados)
        self.lbl_customer = QLabel("Nombre del Cliente:")
        self.lbl_customer.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.input_customer = QLineEdit()
        self.input_customer.setPlaceholderText("Ej: Don Carlos (Maestro de Obra)")

        # 5. Campo Monto Electrónico (Para Pago Mixto)
        self.lbl_mixed_electronic = QLabel("Monto Transferencia ($):")
        self.lbl_mixed_electronic.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.input_mixed_electronic = QLineEdit()
        self.input_mixed_electronic.setPlaceholderText("Ej: 20000")

        self.grid_pay.addWidget(self.lbl_cash, 0, 0)
        self.grid_pay.addWidget(self.input_cash, 0, 1)
        self.grid_pay.addWidget(self.lbl_change_title, 1, 0)
        self.grid_pay.addWidget(self.lbl_change, 1, 1)
        self.grid_pay.addWidget(self.lbl_ref, 2, 0)
        self.grid_pay.addWidget(self.input_ref, 2, 1)
        self.grid_pay.addWidget(self.lbl_customer, 3, 0)
        self.grid_pay.addWidget(self.input_customer, 3, 1)
        self.grid_pay.addWidget(self.lbl_mixed_electronic, 4, 0)
        self.grid_pay.addWidget(self.input_mixed_electronic, 4, 1)

        checkout_layout.addLayout(self.grid_pay)
        self._on_payment_method_changed(0)  # Iniciar con efectivo visible

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

    def _on_payment_method_changed(self, index: int) -> None:
        """Muestra u oculta los campos según el método de pago seleccionado."""
        method = self.combo_payment.currentData()

        # Ocultar todos por defecto
        self.lbl_cash.setVisible(False)
        self.input_cash.setVisible(False)
        self.lbl_change_title.setVisible(False)
        self.lbl_change.setVisible(False)
        self.lbl_ref.setVisible(False)
        self.input_ref.setVisible(False)
        self.lbl_customer.setVisible(False)
        self.input_customer.setVisible(False)
        self.lbl_mixed_electronic.setVisible(False)
        self.input_mixed_electronic.setVisible(False)

        if method == PaymentMethod.CASH:
            self.lbl_cash.setVisible(True)
            self.input_cash.setVisible(True)
            self.lbl_change_title.setVisible(True)
            self.lbl_change.setVisible(True)
        elif method in (PaymentMethod.NEQUI_DAVIPLATA, PaymentMethod.CARD):
            self.lbl_ref.setVisible(True)
            self.input_ref.setVisible(True)
            self.lbl_ref.setText("N° Comprobante / Aprobación:")
        elif method == PaymentMethod.CREDIT:
            self.lbl_customer.setVisible(True)
            self.input_customer.setVisible(True)
        elif method == PaymentMethod.MIXED:
            self.lbl_cash.setVisible(True)
            self.input_cash.setVisible(True)
            self.lbl_cash.setText("Monto en Efectivo ($):")
            self.lbl_mixed_electronic.setVisible(True)
            self.input_mixed_electronic.setVisible(True)

    def add_product_to_cart(self) -> None:
        query = self.input_search.text().strip()
        if not query:
            return

        qty = int(self.spin_qty.value())
        product = SaleService.get_product_by_identifier(query)

        if not product:
            QMessageBox.warning(self, "No Encontrado", f"No existe ningún producto con el código: '{query}'")
            return

        if product.stock < qty:
            QMessageBox.warning(
                self,
                "Stock Insuficiente",
                f"El producto '{product.name}' solo tiene {int(product.stock)} {product.unit.value} disponibles."
            )
            return

        item_dto = CartItemDTO(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            quantity=float(qty),
            unit_price=float(product.sale_price),
            unit=product.unit.value
        )
        self.cart.append(item_dto)

        self.input_search.clear()
        self.spin_qty.setValue(1)
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
            
            qty_item = QTableWidgetItem(f"{int(item.quantity)} ")
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
                self.lbl_change.setStyleSheet("font-size: 18px; font-weight: 800; color: #10b981;")
            else:
                self.lbl_change.setText("$ 0")
                self.lbl_change.setStyleSheet("font-size: 18px; font-weight: 800; color: #ef4444;")
        except ValueError:
            self.lbl_change.setText("$ 0")

    def complete_sale(self) -> None:
        if not self.cart:
            QMessageBox.warning(self, "Carrito Vacío", "No hay productos en la orden de venta.")
            return

        total = sum(i.subtotal for i in self.cart)
        selected_method = self.combo_payment.currentData()

        # Construir y validar el objeto de pago según el método
        cash_val = 0.0
        electronic_val = 0.0
        ref_val = None
        customer_val = None

        if selected_method == PaymentMethod.CASH:
            cash_text = self.input_cash.text().strip().replace(".", "").replace(",", "")
            cash_val = float(cash_text) if cash_text else 0.0
            if cash_val < total:
                QMessageBox.warning(self, "Pago Insuficiente", "El dinero recibido es menor al total a cobrar.")
                return

        elif selected_method in (PaymentMethod.NEQUI_DAVIPLATA, PaymentMethod.CARD):
            electronic_val = total
            ref_val = self.input_ref.text().strip()
            if not ref_val:
                QMessageBox.warning(self, "Comprobante Obligatorio", "Debe ingresar el número de comprobante o aprobación de la transferencia.")
                return

        elif selected_method == PaymentMethod.CREDIT:
            customer_val = self.input_customer.text().strip()
            if not customer_val:
                QMessageBox.warning(self, "Cliente Obligatorio", "Debe ingresar el nombre del cliente al que se le autoriza el fiado.")
                return

        elif selected_method == PaymentMethod.MIXED:
            cash_text = self.input_cash.text().strip().replace(".", "").replace(",", "")
            elec_text = self.input_mixed_electronic.text().strip().replace(".", "").replace(",", "")
            cash_val = float(cash_text) if cash_text else 0.0
            electronic_val = float(elec_text) if elec_text else 0.0
            if (cash_val + electronic_val) < total:
                QMessageBox.warning(self, "Monto Incompleto", f"La suma de efectivo + transferencia (${cash_val + electronic_val:,.0f}) es menor al total (${total:,.0f}).")
                return

        payment_dto = PaymentInfoDTO(
            method=selected_method,
            cash_amount=cash_val,
            electronic_amount=electronic_val,
            reference_number=ref_val,
            customer_name=customer_val
        )

        items_for_receipt = list(self.cart)

        ok, msg, sale = SaleService.process_sale(self.cart, payment_dto)
        if ok and sale:
            receipt_modal = ReceiptModal(
                invoice_number=sale.invoice_number,
                items=items_for_receipt,
                payment=payment_dto,
                parent=self
            )
            receipt_modal.exec()

            # Limpiar campos
            self.cart.clear()
            self.input_cash.clear()
            self.input_ref.clear()
            self.input_customer.clear()
            self.input_mixed_electronic.clear()
            self._refresh_cart_table()

            if self.on_sale_completed_callback:
                self.on_sale_completed_callback()
        else:
            QMessageBox.critical(self, "Error de Venta", f"❌ {msg}")
