"""Configuration model describing the scraper project to generate."""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Supported HTTP / browser engines and a one-line description for ``list``.
ENGINES: dict[str, str] = {
    "requests": "Classic synchronous HTTP client — simple and battle-tested.",
    "httpx": "Modern HTTP client with sync *and* async support (default).",
    "playwright": "Headless browser for JavaScript-heavy, client-rendered pages.",
}

#: Supported HTML parsers.
PARSERS: dict[str, str] = {
    "parsel": "Scrapy's selector library — CSS + XPath, backed by lxml (default).",
    "beautifulsoup": "BeautifulSoup 4 — forgiving, beginner-friendly HTML parsing.",
}

#: Engines that cannot run in async mode.
_SYNC_ONLY_ENGINES = {"requests"}

_PACKAGE_RE = re.compile(r"[^0-9a-zA-Z_]+")


class ConfigError(ValueError):
    """Raised when a requested project configuration is invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    """A validated description of the project to scaffold."""

    name: str
    engine: str = "httpx"
    parser: str = "parsel"
    is_async: bool = False
    cache: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ConfigError("project name must not be empty")
        if self.engine not in ENGINES:
            raise ConfigError(
                f"unknown engine {self.engine!r}; choose from {', '.join(sorted(ENGINES))}"
            )
        if self.parser not in PARSERS:
            raise ConfigError(
                f"unknown parser {self.parser!r}; choose from {', '.join(sorted(PARSERS))}"
            )
        if self.is_async and self.engine in _SYNC_ONLY_ENGINES:
            raise ConfigError(
                f"the {self.engine!r} engine has no async API; "
                "use --sync, or pick --engine httpx/playwright for async"
            )

    @property
    def mode(self) -> str:
        """``"async"`` or ``"sync"``."""
        return "async" if self.is_async else "sync"

    @property
    def package_name(self) -> str:
        """A valid Python package identifier derived from :attr:`name`."""
        cleaned = _PACKAGE_RE.sub("_", self.name.strip()).strip("_").lower()
        if not cleaned:
            cleaned = "scraper"
        if cleaned[0].isdigit():
            cleaned = f"_{cleaned}"
        return cleaned

    @property
    def user_agent(self) -> str:
        """A descriptive, honest default User-Agent for the generated scraper."""
        return (
            f"{self.package_name}/0.1 "
            f"(+https://github.com/your-org/{self.package_name}; "
            "polite scraper built with scraper-scaffold)"
        )
