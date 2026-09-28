"""
ferrum.core.config
~~~~~~~~~~~~~~~~~~
Gestión de rutas y variables globales para Arch Linux y Windows.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import os
import sys

from platformdirs import PlatformDirs

APP_NAME = "ferrum"
APP_AUTHOR = "FerrumPOS"


@dataclass(frozen=True)
class AppPaths:
    """Rutas del sistema."""
    config_dir: Path
    data_dir: Path
    log_dir: Path
    cache_dir: Path
    sqlite_db_path: Path


class ConfigurationManager:
    """Calcula y crea las carpetas adecuadas en el sistema."""

    def __init__(self) -> None:
        self._dirs = PlatformDirs(appname=APP_NAME, appauthor=APP_AUTHOR, roaming=True)
        self.os_type: Literal["linux", "windows"] = (
            "linux" if sys.platform.startswith("linux") else "windows"
        )
        self.paths = self._build_paths()
        self._bootstrap_filesystem()

    def _build_paths(self) -> AppPaths:
        config_path = Path(self._dirs.user_config_dir)
        data_path = Path(self._dirs.user_data_dir)
        log_path = Path(self._dirs.user_log_dir)
        cache_path = Path(self._dirs.user_cache_dir)

        return AppPaths(
            config_dir=config_path,
            data_dir=data_path,
            log_dir=log_path,
            cache_dir=cache_path,
            sqlite_db_path=data_path / "offline_ferrum.db",
        )

    def _bootstrap_filesystem(self) -> None:
        """Crea las carpetas en tu Arch Linux si no existen."""
        for path in [
            self.paths.config_dir,
            self.paths.data_dir,
            self.paths.log_dir,
            self.paths.cache_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    @property
    def database_uri(self) -> str:
        """Ruta a la base de datos."""
        env_uri = os.getenv("FERRUM_DATABASE_URI")
        if env_uri:
            return env_uri
        return f"sqlite:///{self.paths.sqlite_db_path.resolve().as_posix()}"


# Objeto global listo para importar
settings = ConfigurationManager()