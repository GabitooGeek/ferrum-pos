"""
ferrum.application.services.report_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Servicio de cálculo de métricas financieras, arqueo de caja y reportes diarios.
"""
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import List, Tuple
from sqlalchemy import func

from ferrum.core.logging import logger
from ferrum.infrastructure.database.connection import db
from ferrum.infrastructure.database.models import Product, Sale, SaleItem


@dataclass
class DailySummaryDTO:
    total_revenue: float
    total_transactions: int
    average_ticket: float
    sales_list: List[dict]


class ReportService:
    """Calcula arqueos de caja y resúmenes de venta."""

    @classmethod
    def get_daily_summary(cls, target_date: date | None = None) -> DailySummaryDTO:
        if target_date is None:
            target_date = date.today()

        start_of_day = datetime.combine(target_date, time.min)
        end_of_day = datetime.combine(target_date, time.max)

        for session in db.get_session():
            sales = (
                session.query(Sale)
                .filter(Sale.created_at >= start_of_day, Sale.created_at <= end_of_day)
                .order_by(Sale.created_at.desc())
                .all()
            )

            total_revenue = sum(float(s.total_amount) for s in sales)
            total_transactions = len(sales)
            avg_ticket = (total_revenue / total_transactions) if total_transactions > 0 else 0.0

            sales_data = []
            for s in sales:
                sales_data.append({
                    "id": s.id,
                    "invoice_number": s.invoice_number,
                    "time": s.created_at.strftime("%I:%M %p") if s.created_at else "--:--",
                    "items_count": len(s.items),
                    "total": float(s.total_amount)
                })

            return DailySummaryDTO(
                total_revenue=total_revenue,
                total_transactions=total_transactions,
                average_ticket=avg_ticket,
                sales_list=sales_data
            )

        return DailySummaryDTO(0.0, 0, 0.0, [])

    @classmethod
    def build_closing_ticket(cls, target_date: date | None = None) -> str:
        """Genera el comprobante de Arqueo / Cierre de Caja para la impresora térmica."""
        summary = cls.get_daily_summary(target_date)
        width = 42
        lines = []

        lines.append("==========================================")
        lines.append("       CORTE DE CAJA / ARQUEO DIARIO      ")
        lines.append("      FERRETERÍA EL MARTILLO INDUSTRIAL   ")
        lines.append("==========================================")
        lines.append(f"Fecha de Cierre : {datetime.now().strftime('%d/%m/%Y %I:%M %p')}")
        lines.append(f"Terminal        : CAJA PRINCIPAL 01")
        lines.append("-" * width)
        lines.append(f"Total Facturas  : {summary.total_transactions}")
        lines.append(f"Ticket Promedio : ${summary.average_ticket:,.0f}".replace(",", "."))
        lines.append("=" * width)
        lines.append(f"TOTAL RECAUDADO : ${summary.total_revenue:,.0f}".replace(",", "."))
        lines.append("==========================================")
        lines.append("\n\nFirma Responsable: _____________________\n\n")

        return "\n".join(lines)
