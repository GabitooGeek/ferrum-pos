"""
ferrum.infrastructure.vision.detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Motor de detección y decodificación de códigos de barras 1D (Code128, EAN13) con OpenCV.
"""
from typing import Optional, Tuple
import cv2
import numpy as np


class BarcodeDetectorEngine:
    """Detecta y traza recuadros sobre códigos de barras en fotogramas de video."""

    def __init__(self) -> None:
        # Detector nativo de OpenCV 4.8+
        self.detector = cv2.barcode.BarcodeDetector()

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[str]]:
        """
        Analiza el fotograma, dibuja el polígono de detección y extrae el texto del código.
        """
        try:
            ok, decoded_info, decoded_type, corners = self.detector.detectAndDecode(frame)
            if ok and len(decoded_info) > 0:
                code_text = decoded_info[0]
                if code_text:
                    # Dibujar recuadro de seguimiento en verde neón (#10b981)
                    if corners is not None and len(corners) > 0:
                        pts = corners[0].astype(int)
                        cv2.polylines(frame, [pts], isClosed=True, color=(16, 185, 129), thickness=3)
                        # Dibujar etiqueta de texto sobre el código
                        x, y = pts[0]
                        cv2.putText(
                            frame,
                            f"CODIGO: {code_text}",
                            (x, max(20, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (16, 185, 129),
                            2,
                            cv2.LINE_AA,
                        )
                    return frame, code_text
        except Exception:
            pass

        return frame, None
