"""
ferrum.application.services.receipt_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generador de tickets térmicos con cantidades enteras para Colombia.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List

from ferrum.application.services.sale_service import CartItemDTO
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
        cash_received: float,
        store: StoreInfo = StoreInfo()
    ) -> str:
        total = sum(i.subtotal for i in items)
        change = max(0.0, cash_received - total)
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
            
            # Cantidad en Entero (ej: 2 UND, 5 MET)
            qty_unit = f"{int(item.quantity)} {item.unit[:3]}"
            p_unit = f"${item.unit_price:,.0f}".replace(",", ".")
            p_sub = f"${item.subtotal:,.0f}".replace(",", ".")
            
            lines.append(f"  {qty_unit:<10} {p_unit:>12} {p_sub:>14}")

        lines.append("-" * width)

        # Totales
        lines.append(f"{'TOTAL A PAGAR (COP):':<25} {f'${total:,.0f}'.replace(',', '.'):>16}")
        lines.append(f"{'Efectivo Recibido:':<25} {f'${cash_received:,.0f}'.replace(',', '.'):>16}")
        lines.append(f"{'Cambio / Vuelto:':<25} {f'${change:,.0f}'.replace(',', '.'):>16}")
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
