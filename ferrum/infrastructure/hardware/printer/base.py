"""
ferrum.infrastructure.hardware.printer.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Contratos base para la Hardware Abstraction Layer (HAL) de impresión de tickets.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class PrinterStatus(Enum):
    READY = auto()
    BUSY = auto()
    OUT_OF_PAPER = auto()
    DISCONNECTED = auto()
    ERROR = auto()


@dataclass
class ReceiptItem:
    description: str
    quantity: float
    unit_price: float
    total: float
    sku: str


class PrinterAdapter(ABC):
    """Interfaz abstracta que deben cumplir todos los adaptadores físicos o de red."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        self._is_connected: bool = False

    @abstractmethod
    def connect(self) -> bool:
        """Establece conexión física o socket con la impresora térmica."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Cierra el handle o socket del dispositivo de manera segura."""
        pass

    @abstractmethod
    def get_status(self) -> PrinterStatus:
        """Consulta el estado del hardware."""
        pass

    @abstractmethod
    def write_raw(self, data: bytes) -> None:
        """Envía comandos ESC/POS crudos al stream de la impresora."""
        pass

    @abstractmethod
    def cut_paper(self, partial: bool = False) -> None:
        """Ejecuta el corte de papel mediante comandos ESC/POS."""
        pass

    @abstractmethod
    def open_cash_drawer(self) -> None:
        """Envía el pulso al solenoide del cajón de dinero (Pin 2 / Pin 5)."""
        pass

    @abstractmethod
    def print_ticket(
        self,
        header: list[str],
        items: list[ReceiptItem],
        totals: dict[str, float],
        footer: Optional[str] = None
    ) -> None:
        """Orquesta la impresión formateada del ticket."""
        pass

    @property
    def is_connected(self) -> bool:
        return self._is_connected
