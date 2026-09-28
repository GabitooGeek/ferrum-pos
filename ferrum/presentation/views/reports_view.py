"""
ferrum.presentation.views.reports_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Vista de arqueo de caja y métricas diarias de facturación para Colombia (COP).
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ferrum.application.services.report_service import ReportService
from ferrum.infrastructure.hardware.printer.network_adapter import NetworkPrinterAdapter


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


class ReportsView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        view_title = QLabel("Cierre de Caja y Reporte del Día")
        view_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #f8fafc;")
        header_layout.addWidget(view_title)
        header_layout.addStretch()

        btn_print_close = QPushButton("🖨️ Imprimir Corte de Caja")
        btn_print_close.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: 800;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        btn_print_close.clicked.connect(self._print_closing)
        header_layout.addWidget(btn_print_close)

        btn_refresh = QPushButton("Recargar")
        btn_refresh.setObjectName("btn_primary")
        btn_refresh.clicked.connect(self.load_report_data)
        header_layout.addWidget(btn_refresh)

        main_layout.addLayout(header_layout)

        # Tarjetas KPI del Día
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(14)
        self.card_daily_total = KPICard("Total Recaudado Hoy (COP)", "$ 0")
        self.card_transactions = KPICard("Ventas Realizadas", "0")
        self.card_avg_ticket = KPICard("Ticket Promedio (COP)", "$ 0")

        self.kpi_layout.addWidget(self.card_daily_total)
        self.kpi_layout.addWidget(self.card_transactions)
        self.kpi_layout.addWidget(self.card_avg_ticket)
        main_layout.addLayout(self.kpi_layout)

        # Tabla de Facturas del Día
        lbl_table_title = QLabel("Detalle de Ventas Registradas Hoy:")
        lbl_table_title.setStyleSheet("font-weight: 700; color: #94a3b8; font-size: 12px;")
        main_layout.addWidget(lbl_table_title)

        self.table_sales = QTableWidget()
        self.table_sales.setColumnCount(4)
        self.table_sales.setHorizontalHeaderLabels([
            "N° Factura", "Hora", "Cant. Artículos", "Total Venta (COP)"
        ])

        h = self.table_sales.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table_sales.verticalHeader().setVisible(False)
        self.table_sales.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_sales.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table_sales)

        # Cargar datos iniciales
        self.load_report_data()

    def load_report_data(self) -> None:
        summary = ReportService.get_daily_summary()

        # Actualizar KPIs
        self.card_daily_total.lbl_value.setText(f"${summary.total_revenue:,.0f}".replace(",", "."))
        self.card_transactions.lbl_value.setText(str(summary.total_transactions))
        self.card_avg_ticket.lbl_value.setText(f"${summary.average_ticket:,.0f}".replace(",", "."))

        # Llenar Tabla
        self.table_sales.setRowCount(0)
        for row, s in enumerate(summary.sales_list):
            self.table_sales.insertRow(row)

            item_invoice = QTableWidgetItem(f" {s['invoice_number']} ")
            item_invoice.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table_sales.setItem(row, 0, item_invoice)

            item_time = QTableWidgetItem(f" {s['time']} ")
            item_time.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sales.setItem(row, 1, item_time)

            item_count = QTableWidgetItem(f" {s['items_count']} artículos ")
            item_count.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sales.setItem(row, 2, item_count)

            item_total = QTableWidgetItem(f"${s['total']:,.0f} ".replace(",", "."))
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table_sales.setItem(row, 3, item_total)

    def _print_closing(self) -> None:
        ticket_text = ReportService.build_closing_ticket()
        QMessageBox.information(
            self,
            "Corte de Caja Generado",
            f"✅ Resumen del Cierre listo para imprimir:\n\n{ticket_text}"
        )
