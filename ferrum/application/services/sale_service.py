"""
ferrum.application.services.sale_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Lógica de negocio blindada para transacciones con múltiples métodos de pago colombianos.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from ferrum.core.logging import logger
from ferrum.infrastructure.database.connection import db
from ferrum.infrastructure.database.models import PaymentMethod, Product, Sale, SaleItem


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


@dataclass
class PaymentInfoDTO:
    method: PaymentMethod
    cash_amount: float = 0.0
    electronic_amount: float = 0.0
    reference_number: Optional[str] = None
    customer_name: Optional[str] = None


class SaleService:
    """Servicio que ejecuta la venta y asegura consistencia en inventario y pagos."""

    @staticmethod
    def get_product_by_identifier(query: str) -> Product | None:
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
    def process_sale(
        cart_items: List[CartItemDTO],
        payment: PaymentInfoDTO
    ) -> Tuple[bool, str, Sale | None]:
        if not cart_items:
            return False, "El carrito de compras está vacío.", None

        for session in db.get_session():
            try:
                invoice_num = f"VNT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                total_sale = sum(item.subtotal for item in cart_items)

                # Validar y descontar stock
                sale_items_db = []
                for item in cart_items:
                    prod = session.query(Product).filter(Product.id == item.product_id).with_for_update().first()
                    if not prod:
                        session.rollback()
                        return False, f"El producto {item.sku} ya no existe.", None

                    unit_str = prod.unit.value if hasattr(prod.unit, "value") else str(prod.unit)

                    if prod.stock < item.quantity:
                        session.rollback()
                        return (
                            False,
                            f"Stock insuficiente para '{prod.name}'. Disponible: {int(prod.stock)} {unit_str}",
                            None,
                        )

                    # Descontar stock
                    prod.stock = float(prod.stock) - float(item.quantity)

                    sale_item = SaleItem(
                        product_id=prod.id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        subtotal=item.subtotal,
                    )
                    sale_items_db.append(sale_item)

                method_enum = payment.method if isinstance(payment.method, PaymentMethod) else PaymentMethod(payment.method)
                method_label = method_enum.value if hasattr(method_enum, "value") else str(method_enum)

                # Registrar la venta
                sale = Sale(
                    invoice_number=invoice_num,
                    total_amount=total_sale,
                    payment_method=method_enum,
                    cash_amount=payment.cash_amount,
                    electronic_amount=payment.electronic_amount,
                    reference_number=payment.reference_number,
                    customer_name=payment.customer_name,
                    items=sale_items_db,
                )
                session.add(sale)
                session.commit()

                logger.info(f"Venta {invoice_num} procesada con método [{method_label}] por ${total_sale:,.0f}")
                return True, f"Venta {invoice_num} completada con éxito.", sale

            except Exception as exc:
                session.rollback()
                logger.error(f"Error crítico al procesar la venta: {exc}")
                return False, f"Error al procesar la transacción: {str(exc)}", None

        return False, "No se pudo establecer sesión de base de datos.", None
