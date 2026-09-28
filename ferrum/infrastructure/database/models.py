"""
ferrum.infrastructure.database.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Modelos relacionales con soporte para métodos de pago colombianos y fiados.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ferrum.infrastructure.database.connection import Base


class UnitOfMeasure(str, Enum):
    PIECE = "PIEZA"
    METER = "METRO"
    KILOGRAM = "KILOGRAMO"
    LITER = "LITRO"
    BOX = "CAJA"


class PaymentMethod(str, Enum):
    CASH = "EFECTIVO"
    NEQUI_DAVIPLATA = "NEQUI_DAVIPLATA"
    CARD = "TARJETA"
    CREDIT = "CREDITO_FIADO"
    MIXED = "MIXTO"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    barcode: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    unit: Mapped[UnitOfMeasure] = mapped_column(
        SQLEnum(UnitOfMeasure), default=UnitOfMeasure.PIECE, nullable=False
    )

    cost_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    sale_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0.000)
    min_stock: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=5.000)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Campos nuevos para Métodos de Pago Colombianos
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod), default=PaymentMethod.CASH, nullable=False
    )
    # Monto abonado en efectivo (útil para pagos mixtos)
    cash_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    # Monto pagado por transferencia/tarjeta
    electronic_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    
    # Número de aprobación (Nequi/Datáfono)
    reference_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    # Nombre de a quién se le fía
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    items: Mapped[List["SaleItem"]] = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
