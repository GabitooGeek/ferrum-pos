"""
ferrum.application.services.sale_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Lógica de negocio para transacciones de venta, validación de stock y persistencia.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session

from ferrum.core.logging import logger
from ferrum.infrastructure.database.connection import db
from ferrum.infrastructure.database.models import Product, Sale, SaleItem


@dataclass
class CartItemDTO:
    product_id: int
    sku: str
    name: str
    quantity: float
    unit_price: float
    unit: str

    @property
    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)


class SaleService:
    """Servicio que ejecuta la venta y asegura consistencia en inventario."""

    @staticmethod
    def get_product_by_identifier(query: str) -> Product | None:
        """Busca un producto por SKU exacto, código de barras o coincidencia de nombre."""
        query_clean = query.strip()
        for session in db.get_session():
            product = (
                session.query(Product)
                .filter(
                    (Product.sku.ilike(query_clean))
                    | (Product.barcode == query_clean)
                    | (Product.name.ilike(f"%{query_clean}%"))
                )
                .first()
            )
            return product
        return None

    @staticmethod
    def process_sale(cart_items: List[CartItemDTO]) -> Tuple[bool, str, Sale | None]:
        """
        Ejecuta la transacción de venta de forma atómica:
        1. Valida disponibilidad de stock.
        2. Descuenta el inventario según la cantidad (admite decimales).
        3. Registra la venta y sus ítems asociados.
        """
        if not cart_items:
            return False, "El carrito de compras está vacío.", None

        for session in db.get_session():
            try:
                # Generar folio único basado en timestamp
                invoice_num = f"VNT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                total_sale = sum(item.subtotal for item in cart_items)

                # 1. Validar y descontar stock de cada producto
                sale_items_db = []
                for item in cart_items:
                    prod = session.query(Product).filter(Product.id == item.product_id).with_for_update().first()
                    if not prod:
                        session.rollback()
                        return False, f"El producto {item.sku} ya no existe.", None

                    if prod.stock < item.quantity:
                        session.rollback()
                        return (
                            False,
                            f"Stock insuficiente para '{prod.name}'. Disponible: {prod.stock:.3f} {prod.unit.value}",
                            None,
                        )

                    # Descuento de inventario fraccional
                    prod.stock = float(prod.stock) - float(item.quantity)

                    # Crear ítem de detalle
                    sale_item = SaleItem(
                        product_id=prod.id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        subtotal=item.subtotal,
                    )
                    sale_items_db.append(sale_item)

                # 2. Registrar la cabecera de la venta
                sale = Sale(
                    invoice_number=invoice_num,
                    total_amount=total_sale,
                    items=sale_items_db,
                )
                session.add(sale)
                session.commit()

                logger.info(f"Venta {invoice_num} procesada exitosamente por ${total_sale:.2f}")
                return True, f"Venta {invoice_num} completada con éxito.", sale

            except Exception as exc:
                session.rollback()
                logger.error(f"Error crítico al procesar la venta: {exc}")
                return False, f"Error al procesar la transacción: {str(exc)}", None

        return False, "No se pudo establecer sesión de base de datos.", None
