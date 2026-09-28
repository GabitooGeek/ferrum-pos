#!/usr/bin/env python3
"""
FERRUM POS - Entrypoint Principal
Inicializa la GUI de PySide6 y la conexión con el backend de datos.
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ferrum.core.logging import logger, setup_logging
from ferrum.presentation.views.main_window import MainWindow


def main() -> None:
    # 1. Iniciar registro de logs
    setup_logging()
    logger.info("Iniciando FERRUM POS...")

    # 2. Configurar escalado para pantallas de alta resolución (HiDPI)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 3. Arrancar la aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("FerrumPOS")
    app.setOrganizationName("Ferrum")

    # 4. Mostrar la ventana principal
    window = MainWindow()
    window.show()

    logger.info("Aplicación levantada y lista para operar.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
