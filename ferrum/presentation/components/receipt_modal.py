"""
ferrum.presentation.components.receipt_modal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modal de ticket térmico blindado contra tipos Enum/str.
"""
from pathlib import Path
from typing import List
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ferrum.application.services.receipt_service import ReceiptService, StoreInfo
from ferrum.application.services.sale_service import CartItemDTO, PaymentInfoDTO
from ferrum.infrastructure.hardware.printer.network_adapter import NetworkPrinterAdapter


class ReceiptModal(QDialog):
    def __init__(
        self,
        invoice_number: str,
        items: List[CartItemDTO],
        payment: PaymentInfoDTO,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.invoice_number = invoice_number
        self.items = items
        self.payment = payment
        self.ticket_text = ReceiptService.build_ticket_text(invoice_number, items, payment)

        self.setWindowTitle(f"Ticket de Venta — {invoice_number}")
        self.resize(470, 640)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
            }
            QLabel {
                color: #cbd5e1;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("📄 COMPROBANTE DE PAGO (80mm)")
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #38bdf8;")
        layout.addWidget(title)

        # Visor de Papel Térmico
        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setFont(QFont("Monospace", 10))
        self.txt_preview.setStyleSheet("""
            QTextEdit {
                background-color: #131d31;
                color: #38bdf8;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Courier New', 'JetBrains Mono', monospace;
                font-size: 11px;
                line-height: 1.2;
            }
        """)
        self.txt_preview.setText(self.ticket_text)
        layout.addWidget(self.txt_preview, stretch=1)

        # Configuración de IP
        printer_bar = QFrame()
        printer_bar.setStyleSheet("background-color: #131d31; border-radius: 6px; padding: 8px; border: 1px solid #1e293b;")
        p_layout = QHBoxLayout(printer_bar)
        p_layout.setContentsMargins(8, 4, 8, 4)
        
        lbl_ip = QLabel("IP Impresora:")
        self.input_printer_ip = QLineEdit("192.168.1.200")
        self.input_printer_ip.setPlaceholderText("IP Impresora Térmica")
        p_layout.addWidget(lbl_ip)
        p_layout.addWidget(self.input_printer_ip)
        layout.addWidget(printer_bar)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_print = QPushButton("🖨️ Imprimir Ticket")
        self.btn_print.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: 800;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_print.clicked.connect(self._print_physical_ticket)

        self.btn_done = QPushButton("✅ Finalizar Venta")
        self.btn_done.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #042f2e;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: 800;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #059669;
                color: #ffffff;
            }
        """)
        self.btn_done.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_print)
        btn_layout.addWidget(self.btn_done)
        layout.addLayout(btn_layout)

    def _print_physical_ticket(self) -> None:
        ip = self.input_printer_ip.text().strip()
        if not ip:
            QMessageBox.warning(self, "Error", "Debe ingresar una dirección IP para la impresora.")
            return

        adapter = NetworkPrinterAdapter(host=ip, port=9100, timeout=2.0)
        if adapter.connect():
            store = StoreInfo()
            header = [
                store.name,
                store.nit,
                store.regime,
                store.address,
                store.phone,
                f"Factura: {self.invoice_number}"
            ]
            hal_items = ReceiptService.to_hal_receipt_items(self.items)
            total = sum(i.subtotal for i in self.items)
            method_str = self.payment.method.value if hasattr(self.payment.method, "value") else str(self.payment.method)
            totals = {
                "Total COP": total,
                "Forma Pago": method_str,
            }
            try:
                adapter.print_ticket(
                    header=header,
                    items=hal_items,
                    totals=totals,
                    footer="Gracias por su compra en Ferretería El Martillo"
                )
                QMessageBox.information(self, "Impresión Exitosa", "El ticket fue enviado correctamente a la impresora.")
            finally:
                adapter.disconnect()
        else:
            QMessageBox.warning(
                self,
                "Impresora No Encontrada",
                f"No se pudo conectar a la impresora en {ip}:9100.\n(Verifique que la impresora esté encendida)."
            )
