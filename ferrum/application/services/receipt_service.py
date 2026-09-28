"""
ferrum.application.services.receipt_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generador y formateador de tickets de compra térmicos para Colombia.
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
    """Construye y formatea el recibo de compra para pantalla e impresora térmica."""

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

        # 42 caracteres de ancho (Estándar papel térmico 80mm)
        width = 42
        lines = []

        # Header
        lines.append(store.name.center(width))
        lines.append(store.nit.center(width))
        lines.append(store.regime.center(width))
        lines.append(store.address.center(width))
        lines.append(store.phone.center(width))
        lines.append("=" * width)

        # Metadatos de la venta
        lines.append(f"Factura N°: {invoice_number}")
        lines.append(f"Fecha/Hora: {now_str}")
        lines.append(f"Cajero    : Estación 01 (Caja Principal)")
        lines.append("-" * width)

        # Columnas de Ítems
        lines.append(f"{'CANT':<7} {'DESCRIPCIÓN':<18} {'VR.UNIT':>7} {'TOTAL':>8}")
        lines.append("-" * width)

        for item in items:
            # Línea de descripción
            desc = item.name[:width]
            lines.append(desc)
            
            # Cantidad con unidad, valor unitario y subtotal COP
            qty_unit = f"{item.quantity:.2f} {item.unit[:3]}"
            p_unit = f"${item.unit_price:,.0f}".replace(",", ".")
            p_sub = f"${item.subtotal:,.0f}".replace(",", ".")
            
            lines.append(f"  {qty_unit:<12} {p_unit:>11} {p_sub:>13}")

        lines.append("-" * width)

        # Totales
        lines.append(f"{'TOTAL A PAGAR (COP):':<25} {f'${total:,.0f}'.replace(',', '.'):>16}")
        lines.append(f"{'Efectivo Recibido:':<25} {f'${cash_received:,.0f}'.replace(',', '.'):>16}")
        lines.append(f"{'Cambio / Vuelto:':<25} {f'${change:,.0f}'.replace(',', '.'):>16}")
        lines.append("=" * width)

        # Pie de página
        lines.append("¡Gracias por su compra!".center(width))
        lines.append("Garantía de 30 días con este ticket".center(width))
        lines.append("Software: FERRUM POS (Linux Industrial)".center(width))

        return "\n".join(lines)

    @classmethod
    def to_hal_receipt_items(cls, items: List[CartItemDTO]) -> List[ReceiptItem]:
        """Convierte los ítems del carrito al formato esperado por la HAL de impresión."""
        hal_items = []
        for i in items:
            hal_items.append(
                ReceiptItem(
                    sku=i.sku,
                    description=i.name,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                    total=i.subtotal
                )
            )
        return hal_items
