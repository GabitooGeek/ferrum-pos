"""
ferrum.application.services.receipt_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generador de tickets térmicos con detalle de métodos de pago colombianos.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List

from ferrum.application.services.sale_service import CartItemDTO, PaymentInfoDTO
from ferrum.infrastructure.database.models import PaymentMethod
from ferrum.infrastructure.hardware.printer.base import ReceiptItem


@dataclass
class StoreInfo:
    name: str = "FERRETERÍA EL MARTILLO INDUSTRIAL"
    nit: str = "NIT: 900.854.120-3"
    regime: str = "Régimen Simple de Tributación"
    address: str = "Cra. 15 # 45-20, Bogotá D.C."
    phone: str = "Tel: (601) 310-8590"


class ReceiptService:
    @classmethod
    def build_ticket_text(
        cls,
        invoice_number: str,
        items: List[CartItemDTO],
        payment: PaymentInfoDTO,
        store: StoreInfo = StoreInfo()
    ) -> str:
        total = sum(i.subtotal for i in items)
        now_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")

        width = 42
        lines = []

        # Header
        lines.append(store.name.center(width))
        lines.append(store.nit.center(width))
        lines.append(store.regime.center(width))
        lines.append(store.address.center(width))
        lines.append(store.phone.center(width))
        lines.append("=" * width)

        # Datos Venta
        lines.append(f"Factura N°: {invoice_number}")
        lines.append(f"Fecha/Hora: {now_str}")
        lines.append(f"Cajero    : Estación 01 (Caja Principal)")
        lines.append("-" * width)

        # Columnas
        lines.append(f"{'CANT':<6} {'DESCRIPCIÓN':<19} {'VR.UNIT':>7} {'TOTAL':>8}")
        lines.append("-" * width)

        for item in items:
            desc = item.name[:width]
            lines.append(desc)
            
            qty_unit = f"{int(item.quantity)} {item.unit[:3]}"
            p_unit = f"${item.unit_price:,.0f}".replace(",", ".")
            p_sub = f"${item.subtotal:,.0f}".replace(",", ".")
            
            lines.append(f"  {qty_unit:<10} {p_unit:>12} {p_sub:>14}")

        lines.append("-" * width)

        # Totales
        lines.append(f"{'TOTAL A PAGAR (COP):':<25} {f'${total:,.0f}'.replace(',', '.'):>16}")

        # Desglose según método de pago
        if payment.method == PaymentMethod.CASH:
            change = max(0.0, payment.cash_amount - total)
            lines.append(f"{'Forma de Pago:':<25} {'EFECTIVO':>16}")
            lines.append(f"{'Efectivo Recibido:':<25} {f'${payment.cash_amount:,.0f}'.replace(',', '.'):>16}")
            lines.append(f"{'Cambio / Vuelto:':<25} {f'${change:,.0f}'.replace(',', '.'):>16}")
        elif payment.method == PaymentMethod.NEQUI_DAVIPLATA:
            ref = payment.reference_number if payment.reference_number else "N/A"
            lines.append(f"{'Forma de Pago:':<25} {'NEQUI / DAVIPLATA':>16}")
            lines.append(f"{'Comprobante N°:':<25} {ref:>16}")
        elif payment.method == PaymentMethod.CARD:
            ref = payment.reference_number if payment.reference_number else "N/A"
            lines.append(f"{'Forma de Pago:':<25} {'TARJETA / DATÁFONO':>16}")
            lines.append(f"{'Aprobación N°:':<25} {ref:>16}")
        elif payment.method == PaymentMethod.CREDIT:
            cliente = payment.customer_name if payment.customer_name else "Cliente General"
            lines.append(f"{'Forma de Pago:':<25} {'CRÉDITO / FIADO':>16}")
            lines.append(f"{'A Nombre de:':<20} {cliente[:21]:>21}")
            lines.append(f"{'Estado:':<25} {'PENDIENTE DE PAGO':>16}")
        elif payment.method == PaymentMethod.MIXED:
            lines.append(f"{'Forma de Pago:':<25} {'PAGO MIXTO':>16}")
            lines.append(f"{'  - Efectivo:':<25} {f'${payment.cash_amount:,.0f}'.replace(',', '.'):>16}")
            lines.append(f"{'  - Electrónico:':<25} {f'${payment.electronic_amount:,.0f}'.replace(',', '.'):>16}")

        lines.append("=" * width)

        lines.append("¡Gracias por su compra!".center(width))
        lines.append("Garantía de 30 días con este ticket".center(width))
        lines.append("Software: FERRUM POS (Linux Industrial)".center(width))

        return "\n".join(lines)

    @classmethod
    def to_hal_receipt_items(cls, items: List[CartItemDTO]) -> List[ReceiptItem]:
        hal_items = []
        for i in items:
            hal_items.append(
                ReceiptItem(
                    sku=i.sku,
                    description=i.name,
                    quantity=float(int(i.quantity)),
                    unit_price=i.unit_price,
                    total=i.subtotal
                )
            )
        return hal_items
