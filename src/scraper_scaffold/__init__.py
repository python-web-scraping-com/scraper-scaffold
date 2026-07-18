"""scraper-scaffold — generate polite-by-default Python web scrapers."""

from .config import ENGINES, PARSERS, ConfigError, ProjectConfig
from .generator import GeneratedFile, ProjectExistsError, generate, render_project

__version__ = "0.1.0"

__all__ = [
    "ProjectConfig",
    "ConfigError",
    "ENGINES",
    "PARSERS",
    "GeneratedFile",
    "ProjectExistsError",
    "generate",
    "render_project",
    "__version__",
]
