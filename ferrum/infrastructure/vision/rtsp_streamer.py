"""
ferrum.infrastructure.vision.rtsp_streamer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Motor de captura y streaming de video concurrente en QThread independiente.
"""
import time
from typing import Union
import cv2
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QImage

from ferrum.core.logging import logger


class VideoCaptureWorker(QThread):
    """Worker que lee fotogramas en bucle continuo sin bloquear la GUI."""

    # Señales emitidas hacia la interfaz gráfica
    frame_ready = Signal(QImage)
    status_changed = Signal(str, bool)  # (mensaje, conectado)

    def __init__(self, source: Union[int, str] = 0, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.source = source
        self._is_running = False

    def set_source(self, source: Union[int, str]) -> None:
        """Permite cambiar la fuente (ej. /dev/video0 o URL rtsp://)."""
        self.source = source

    def run(self) -> None:
        self._is_running = True
        logger.info(f"[Cerberus] Iniciando hilo de captura para: {self.source}")
        self.status_changed.emit("Conectando a cámara...", False)

        cap = cv2.VideoCapture(self.source)

        # Si es cámara web local (Linux V4L2), optimizamos el backend
        if isinstance(self.source, int):
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            logger.warning(f"[Cerberus] No se pudo abrir el origen de video: {self.source}")
            self.status_changed.emit("No se pudo conectar a la cámara", False)
            self._is_running = False
            return

        self.status_changed.emit("Cámara Conectada (En Vivo)", True)
        logger.info(f"[Cerberus] Stream activo y capturando fotogramas.")

        while self._is_running:
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning("[Cerberus] Pérdida de señal o fin de stream. Reintentando...")
                self.status_changed.emit("Reconectando señal...", False)
                time.sleep(1.0)
                continue

            # Conversión de OpenCV BGR a formato QImage RGB888 compatible con Qt
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(
                rgb_frame.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            ).copy()

            # Emitir fotograma listo a la GUI
            self.frame_ready.emit(qt_image)

            # Control de tasa de muestreo (~30 FPS)
            self.msleep(33)

        cap.release()
        logger.info("[Cerberus] Hilo de captura finalizado correctamente.")
        self.status_changed.emit("Cámara Detenida", False)

    def stop(self) -> None:
        """Detiene de manera limpia el bucle del hilo."""
        self._is_running = False
        self.wait(2000)  # Espera hasta 2 segundos para liberar el hardware
