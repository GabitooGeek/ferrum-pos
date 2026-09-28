"""
ferrum.presentation.views.cctv_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Monitor de videovigilancia en vivo para el subsistema Cerberus.
"""
from typing import Union
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ferrum.infrastructure.vision.rtsp_streamer import VideoCaptureWorker


class CCTVView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.worker: VideoCaptureWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Barra Superior de Control
        control_bar = QFrame()
        control_bar.setStyleSheet("""
            QFrame {
                background-color: #131d31;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout(control_bar)
        control_layout.setSpacing(12)

        lbl_src = QLabel("Fuente de Video:")
        lbl_src.setStyleSheet("font-weight: bold; color: #94a3b8;")
        control_layout.addWidget(lbl_src)

        self.combo_source = QComboBox()
        self.combo_source.addItems([
            "Cámara Local 0 (/dev/video0)",
            "Cámara Local 1 (/dev/video1)",
            "Cámara IP (Stream RTSP / HTTP)"
        ])
        self.combo_source.setStyleSheet("""
            QComboBox {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 220px;
            }
            QComboBox QAbstractItemView {
                background-color: #0f172a;
                color: #f8fafc;
                selection-background-color: #1e293b;
            }
        """)
        self.combo_source.currentIndexChanged.connect(self._on_source_type_changed)
        control_layout.addWidget(self.combo_source)

        # Campo para ingresar URL RTSP personalizada
        self.input_rtsp = QLineEdit()
        self.input_rtsp.setPlaceholderText("rtsp://admin:pass@192.168.1.100:554/stream1")
        self.input_rtsp.setVisible(False)
        self.input_rtsp.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
            }
        """)
        control_layout.addWidget(self.input_rtsp, stretch=1)

        control_layout.addStretch()

        # Indicador de estado LED
        self.lbl_status = QLabel("● Desconectado")
        self.lbl_status.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px;")
        control_layout.addWidget(self.lbl_status)

        # Botón Conectar/Detener
        self.btn_toggle = QPushButton("▶ Iniciar Stream")
        self.btn_toggle.setObjectName("btn_primary")
        self.btn_toggle.clicked.connect(self.toggle_stream)
        control_layout.addWidget(self.btn_toggle)

        main_layout.addWidget(control_bar)

        # Contenedor del Monitor de Video
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("""
            QFrame {
                background-color: #090d16;
                border: 2px dashed #1e293b;
                border-radius: 12px;
            }
        """)
        video_layout = QVBoxLayout(self.video_frame)
        video_layout.setContentsMargins(10, 10, 10, 10)

        # Lienzo del fotograma
        self.lbl_video_viewport = QLabel("Sin señal de video\nPresione 'Iniciar Stream' para conectar")
        self.lbl_video_viewport.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_video_viewport.setStyleSheet("color: #475569; font-size: 15px; font-weight: 600;")
        video_layout.addWidget(self.lbl_video_viewport)

        main_layout.addWidget(self.video_frame, stretch=1)

    def _on_source_type_changed(self, index: int) -> None:
        self.input_rtsp.setVisible(index == 2)

    def _get_selected_source(self) -> Union[int, str]:
        idx = self.combo_source.currentIndex()
        if idx == 0:
            return 0
        elif idx == 1:
            return 1
        else:
            return self.input_rtsp.text().strip()

    def toggle_stream(self) -> None:
        if self.worker and self.worker.isRunning():
            self.stop_stream()
        else:
            self.start_stream()

    def start_stream(self) -> None:
        source = self._get_selected_source()
        self.worker = VideoCaptureWorker(source=source)
        self.worker.frame_ready.connect(self.update_frame)
        self.worker.status_changed.connect(self.update_status)
        self.worker.start()

        self.btn_toggle.setText("⏹ Detener Stream")
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border-radius: 8px;
                padding: 9px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)

    def stop_stream(self) -> None:
        if self.worker:
            self.worker.stop()
            self.worker = None

        self.lbl_video_viewport.clear()
        self.lbl_video_viewport.setText("Transmisión Detenida")
        self.lbl_status.setText("● Desconectado")
        self.lbl_status.setStyleSheet("color: #ef4444; font-weight: bold;")

        self.btn_toggle.setText("▶ Iniciar Stream")
        self.btn_toggle.setObjectName("btn_primary")
        self.btn_toggle.setStyleSheet("")

    def update_frame(self, image: QImage) -> None:
        pixmap = QPixmap.fromImage(image)
        # Escalar el fotograma al tamaño del viewport manteniendo la proporción
        scaled = pixmap.scaled(
            self.lbl_video_viewport.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.lbl_video_viewport.setPixmap(scaled)

    def update_status(self, message: str, is_connected: bool) -> None:
        color = "#10b981" if is_connected else "#ef4444"
        self.lbl_status.setText(f"● {message}")
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")

    def hideEvent(self, event) -> None:
        """Si el usuario cambia de pestaña, no sobrecargar el CPU innecesariamente."""
        super().hideEvent(event)
