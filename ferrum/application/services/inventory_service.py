"""
ferrum.application.services.inventory_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Servicio para gestión de catálogo de productos y generación de códigos de barras.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import barcode
from barcode.writer import ImageWriter

from ferrum.core.config import settings
from ferrum.core.logging import logger
from ferrum.infrastructure.database.connection import db
from ferrum.infrastructure.database.models import Product, UnitOfMeasure


@dataclass
class NewProductDTO:
    sku: str
    name: str
    unit: UnitOfMeasure
    cost_price: float
    sale_price: float
    initial_stock: float
    barcode_value: Optional[str] = None
    description: Optional[str] = None


class InventoryService:
    """Administra altas, modificaciones y generación de etiquetas."""

    @staticmethod
    def _ensure_barcode_dir() -> Path:
        barcode_dir = settings.paths.cache_dir / "barcodes"
        barcode_dir.mkdir(parents=True, exist_ok=True)
        return barcode_dir

    @classmethod
    def generate_barcode_image(cls, code_data: str) -> Path:
        """Genera una imagen PNG del código de barras Code128."""
        b_dir = cls._ensure_barcode_dir()
        file_path = b_dir / f"{code_data}"
        
        # Usar estándar Code128 (alfanumérico de alta densidad)
        code_class = barcode.get_barcode_class("code128")
        writer = ImageWriter()
        writer.font_path = None  # Usa fuente integrada por defecto
        
        code_instance = code_class(code_data, writer=writer)
        saved_path = code_instance.save(str(file_path), options={"write_text": True})
        logger.debug(f"Código de barras generado en: {saved_path}")
        return Path(saved_path)

    @classmethod
    def create_product(cls, dto: NewProductDTO) -> Tuple[bool, str, Optional[Product]]:
        """Crea y persiste un nuevo producto en la base de datos."""
        sku_clean = dto.sku.strip().upper()
        if not sku_clean:
            return False, "El SKU no puede estar vacío.", None

        if not dto.name.strip():
            return False, "La descripción del producto es obligatoria.", None

        if dto.sale_price < dto.cost_price:
            return False, "El precio de venta no puede ser menor al costo.", None

        barcode_val = dto.barcode_value.strip() if dto.barcode_value else sku_clean

        for session in db.get_session():
            try:
                # Validar duplicados de SKU
                existing = session.query(Product).filter(
                    (Product.sku == sku_clean) | (Product.barcode == barcode_val)
                ).first()
                if existing:
                    return False, f"Ya existe un producto con SKU o Código '{sku_clean}'.", None

                product = Product(
                    sku=sku_clean,
                    barcode=barcode_val,
                    name=dto.name.strip(),
                    description=dto.description,
                    unit=dto.unit,
                    cost_price=dto.cost_price,
                    sale_price=dto.sale_price,
                    stock=dto.initial_stock,
                    min_stock=5.0
                )
                session.add(product)
                session.commit()

                # Generar imagen de código de barras
                cls.generate_barcode_image(barcode_val)

                logger.info(f"Producto '{product.name}' ({product.sku}) registrado exitosamente.")
                return True, f"Producto '{product.name}' agregado correctamente.", product

            except Exception as exc:
                session.rollback()
                logger.error(f"Error al guardar producto: {exc}")
                return False, f"Error en base de datos: {str(exc)}", None

        return False, "No se pudo conectar a la base de datos.", None
