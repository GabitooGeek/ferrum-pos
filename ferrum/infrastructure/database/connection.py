"""
ferrum.infrastructure.database.connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Gestor de sesiones y motor de base de datos con SQLAlchemy 2.0.
"""
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ferrum.core.config import settings
from ferrum.core.logging import logger


class Base(DeclarativeBase):
    """Clase base de la que heredarán todas las tablas."""
    pass


class DatabaseEngine:
    """Administra el pool de conexiones a la base de datos."""

    def __init__(self) -> None:
        self.uri = settings.database_uri
        self._is_sqlite = self.uri.startswith("sqlite")

        # SQLite requiere check_same_thread=False cuando se usa en interfaces gráficas multitarea
        connect_args = {"check_same_thread": False} if self._is_sqlite else {}

        self.engine = create_engine(
            self.uri,
            connect_args=connect_args,
            echo=False,  # Cambiar a True si necesitas ver las sentencias SQL en consola
            pool_pre_ping=True,
        )

        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        logger.debug(f"Engine de base de datos inicializado -> {self.uri}")

    def create_all_tables(self) -> None:
        """Crea todas las tablas registradas si no existen."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Tablas de base de datos verificadas/creadas con éxito.")

    def get_session(self) -> Generator[Session, None, None]:
        """Provee una sesión limpia para operaciones de base de datos."""
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()


# Instancia global del motor
db = DatabaseEngine()