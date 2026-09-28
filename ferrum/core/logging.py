"""
ferrum.core.logging
~~~~~~~~~~~~~~~~~~~
Configuración de logs con rotación automática de archivos.
"""
import sys
from loguru import logger
from ferrum.core.config import settings


def setup_logging() -> None:
    """Inicializa los logs en consola y archivo."""
    # Limpiamos manejadores por defecto
    logger.remove()

    # Formato con colores y detalles del archivo
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 1. Salida en consola (Terminal)
    logger.add(
        sys.stdout,
        level="DEBUG",
        format=log_format,
        colorize=True,
    )

    # 2. Archivo en disco con rotación de 10 MB
    log_file = settings.paths.log_dir / "ferrum.log"
    logger.add(
        str(log_file),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,  # Seguro para usar con hilos concurrentes
    )

    logger.info("Sistema de logs iniciado.")


# Exportar para usar con: from ferrum.core.logging import logger
__all__ = ["logger", "setup_logging"]