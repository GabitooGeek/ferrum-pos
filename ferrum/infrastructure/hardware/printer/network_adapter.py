"""
ferrum.infrastructure.hardware.printer.network_adapter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Adaptador para impresoras térmicas ESC/POS conectadas vía Socket TCP/IP.
"""
import socket
from ferrum.core.logging import logger
from ferrum.infrastructure.hardware.printer.base import (
    PrinterAdapter,
    PrinterStatus,
    ReceiptItem,
)


class NetworkPrinterAdapter(PrinterAdapter):
    """Manejo de impresión térmica mediante Socket crudo TCP/IP (Puerto estándar 9100)."""

    def __init__(self, host: str, port: int = 9100, timeout: float = 3.0) -> None:
        super().__init__(identifier=f"{host}:{port}")
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket: socket.socket | None = None

    def connect(self) -> bool:
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            self._socket.connect((self.host, self.port))
            self._is_connected = True
            logger.info(f"Conexión establecida con impresora en {self.identifier}")
            return True
        except (socket.error, TimeoutError) as exc:
            self._is_connected = False
            self._socket = None
            logger.warning(f"No se pudo conectar a la impresora en {self.identifier}: {exc}")
            return False

    def disconnect(self) -> None:
        if self._socket:
            try:
                self._socket.close()
            finally:
                self._socket = None
                self._is_connected = False
                logger.info(f"Desconectado de la impresora en {self.identifier}")

    def get_status(self) -> PrinterStatus:
        if not self._is_connected:
            return PrinterStatus.DISCONNECTED
        try:
            # Query status ESC/POS: DLE EOT 1 (Transmit Printer Status)
            self.write_raw(b"\x10\x04\x01")
            status_byte = self._socket.recv(1)  # type: ignore[union-attr]
            if not status_byte:
                return PrinterStatus.ERROR
            return PrinterStatus.READY
        except socket.timeout:
            return PrinterStatus.ERROR
        except Exception:
            return PrinterStatus.DISCONNECTED

    def write_raw(self, data: bytes) -> None:
        if not self._is_connected or not self._socket:
            raise ConnectionError("Impresora desconectada. No se pueden enviar datos.")
        self._socket.sendall(data)

    def cut_paper(self, partial: bool = False) -> None:
        # ESC/POS: GS V 65 n
        cut_mode = b"\x01" if partial else b"\x00"
        self.write_raw(b"\x1d\x56" + cut_mode)

    def open_cash_drawer(self) -> None:
        # ESC/POS: ESC p m t1 t2 (Pulso de 25ms al pin 2)
        self.write_raw(b"\x1b\x70\x00\x19\xfa")

    def print_ticket(
        self,
        header: list[str],
        items: list[ReceiptItem],
        totals: dict[str, float],
        footer: str | None = None
    ) -> None:
        # Inicializar impresora
        self.write_raw(b"\x1b\x40")
        
        # Header centrado
        self.write_raw(b"\x1b\x61\x01")
        for line in header:
            self.write_raw(f"{line}\n".encode("latin-1", errors="replace"))

        # Separador y alineación izquierda
        self.write_raw(b"\x1b\x61\x00")
        self.write_raw(b"------------------------------------------------\n")

        # Items
        for item in items:
            line_str = f"{item.quantity:<6.2f} x {item.unit_price:>8.2f} | {item.total:>10.2f}\n"
            desc_str = f"{item.description[:40]}\n"
            self.write_raw(desc_str.encode("latin-1", errors="replace"))
            self.write_raw(line_str.encode("latin-1", errors="replace"))

        self.write_raw(b"------------------------------------------------\n")

        # Totales
        for k, v in totals.items():
            self.write_raw(f"{k.upper():<30} {v:>17.2f}\n".encode("latin-1"))

        if footer:
            self.write_raw(b"\x1b\x61\x01")
            self.write_raw(f"\n{footer}\n".encode("latin-1", errors="replace"))

        # Avance de papel y corte
        self.write_raw(b"\n\n\n")
        self.cut_paper()
