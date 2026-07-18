"""Render a :class:`~scraper_scaffold.config.ProjectConfig` into files on disk.

Templates are plain text shipped as package data (see the ``templates/``
directory) and loaded with :mod:`importlib.resources`.  Substitution is a
deliberately dumb ``str.replace`` of ``__UPPER_CASE__`` tokens so the templates
themselves stay valid, readable Python with no fragile brace-escaping.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from .config import ProjectConfig

SITE = "https://python-web-scraping.com"

#: Third-party runtime dependencies keyed by engine / parser.
_ENGINE_DEPS = {
    "requests": "requests>=2.31",
    "httpx": "httpx>=0.27",
    "playwright": "playwright>=1.40",
}
_PARSER_DEPS = {
    "parsel": "parsel>=1.8",
    "beautifulsoup": "beautifulsoup4>=4.12",
}
_COMMON_DEPS = ("tenacity>=8.2", "python-dotenv>=1.0")

# Which variant template implements each engine/mode-specific module.
_FETCHER_TEMPLATES = {
    ("requests", "sync"): "fetcher_requests.py.tmpl",
    ("httpx", "sync"): "fetcher_httpx_sync.py.tmpl",
    ("httpx", "async"): "fetcher_httpx_async.py.tmpl",
    ("playwright", "sync"): "fetcher_playwright_sync.py.tmpl",
    ("playwright", "async"): "fetcher_playwright_async.py.tmpl",
}
_PARSE_TEMPLATES = {
    "parsel": "parse_parsel.py.tmpl",
    "beautifulsoup": "parse_bs4.py.tmpl",
}
_SPIDER_TEMPLATES = {
    "sync": "spider_sync.py.tmpl",
    "async": "spider_async.py.tmpl",
}


@dataclass
class GeneratedFile:
    """A single rendered file: its path relative to the project root, plus text."""

    path: str
    content: str


class ProjectExistsError(FileExistsError):
    """Raised when the target project directory already exists and is not empty."""


def _dependencies(cfg: ProjectConfig) -> list[str]:
    return [*_COMMON_DEPS, _ENGINE_DEPS[cfg.engine], _PARSER_DEPS[cfg.parser]]


def _link(text: str, path: str) -> str:
    return f"[{text}]({SITE}{path})"


def _feature_links(cfg: ProjectConfig) -> str:
    """Build the generated README's feature list, each linked to a site guide."""
    parser_label = "parsel" if cfg.parser == "parsel" else "BeautifulSoup"
    lines = [
        "- **Descriptive User-Agent** — identifies your bot honestly instead of "
        "spoofing a browser. "
        + _link(
            "How to rotate User-Agents in Python",
            "/advanced-scraping-techniques-anti-bot-evasion/rotating-proxies-and-managing-ip-blocks/how-to-rotate-user-agents-in-python/",
        )
        + ".",
        "- **`robots.txt` honoring** — checks *allowed* and reads `Crawl-delay` "
        "before every request. "
        + _link(
            "Complete Guide to Python Web Scraping",
            "/the-complete-guide-to-python-web-scraping/",
        )
        + ".",
        "- **Rate limiting** — a token-bucket limiter keeps you at a polite "
        "requests/second. "
        + _link(
            "How to scrape a static website without getting blocked",
            "/the-complete-guide-to-python-web-scraping/handling-pagination-and-infinite-scroll/how-to-scrape-a-static-website-without-getting-blocked/",
        )
        + ".",
        "- **Retries with backoff + jitter** — powered by `tenacity`, and it "
        "respects `Retry-After` on `429`/`503`. "
        + _link(
            "Retrying failed requests with tenacity",
            "/scaling-python-web-scrapers/asynchronous-scraping-with-asyncio-and-httpx/retrying-failed-requests-with-tenacity/",
        )
        + ".",
        "- **On-disk HTTP cache** — re-runs read from disk instead of re-hitting "
        "the site. "
        + _link(
            "Scaling Python Web Scrapers",
            "/scaling-python-web-scrapers/",
        )
        + ".",
        f"- **{parser_label} parse layer** — turn HTML into structured rows. "
        + _link(
            "Parsing HTML with BeautifulSoup",
            "/the-complete-guide-to-python-web-scraping/parsing-html-with-beautifulsoup/",
        )
        + ".",
        "- **CSV / JSONL export** — write results in a portable format. "
        + _link(
            "Storing and exporting scraped data",
            "/scaling-python-web-scrapers/storing-and-exporting-scraped-data/",
        )
        + ".",
        "- **Proxy-ready settings** — plug in a proxy pool when a site pushes "
        "back. "
        + _link(
            "Rotating proxies and managing IP blocks",
            "/advanced-scraping-techniques-anti-bot-evasion/rotating-proxies-and-managing-ip-blocks/",
        )
        + ".",
    ]
    if cfg.is_async:
        lines.append(
            "- **Async I/O** — concurrent fetching with `asyncio`. "
            + _link(
                "Async scraping with asyncio & HTTPX",
                "/scaling-python-web-scrapers/asynchronous-scraping-with-asyncio-and-httpx/",
            )
            + "."
        )
    if cfg.engine == "playwright":
        lines.append(
            "- **Headless browser** — render JavaScript with Playwright. "
            + _link(
                "Playwright for modern web automation",
                "/advanced-scraping-techniques-anti-bot-evasion/using-playwright-for-modern-web-automation/",
            )
            + "."
        )
    return "\n".join(lines)


def _context(cfg: ProjectConfig) -> dict[str, str]:
    deps = _dependencies(cfg)
    toml_deps = "\n".join(f'    "{d}",' for d in deps)
    requirements = "\n".join(deps) + "\n"
    return {
        "PROJECT_NAME": cfg.name,
        "PACKAGE_NAME": cfg.package_name,
        "ENGINE": cfg.engine,
        "PARSER": cfg.parser,
        "MODE": cfg.mode,
        "USER_AGENT": cfg.user_agent,
        "CACHE_DEFAULT": "True" if cfg.cache else "False",
        "CACHE_DEFAULT_ENV": "true" if cfg.cache else "false",
        "DEPENDENCIES": toml_deps,
        "REQUIREMENTS": requirements,
        "FEATURE_LINKS": _feature_links(cfg),
        "SITE": SITE,
        "YEAR": "2026",
    }


def _render(template_name: str, context: dict[str, str]) -> str:
    raw = (
        resources.files("scraper_scaffold")
        .joinpath("templates", template_name)
        .read_text(encoding="utf-8")
    )
    for key, value in context.items():
        raw = raw.replace(f"__{key}__", value)
    return raw


def _manifest(cfg: ProjectConfig) -> list[tuple[str, str]]:
    """Return ``(template_name, output_relative_path)`` pairs for this config."""
    pkg = cfg.package_name
    src = f"src/{pkg}"
    fetcher = _FETCHER_TEMPLATES[(cfg.engine, cfg.mode)]
    parse = _PARSE_TEMPLATES[cfg.parser]
    spider = _SPIDER_TEMPLATES[cfg.mode]
    return [
        # Root files.
        ("pyproject.toml.tmpl", "pyproject.toml"),
        ("requirements.txt.tmpl", "requirements.txt"),
        ("README.md.tmpl", "README.md"),
        ("gitignore.tmpl", ".gitignore"),
        ("env.example.tmpl", ".env.example"),
        # Package.
        ("pkg_init.py.tmpl", f"{src}/__init__.py"),
        ("pkg_main.py.tmpl", f"{src}/__main__.py"),
        ("settings.py.tmpl", f"{src}/settings.py"),
        ("models.py.tmpl", f"{src}/models.py"),
        ("ratelimit.py.tmpl", f"{src}/ratelimit.py"),
        ("cache.py.tmpl", f"{src}/cache.py"),
        ("robots.py.tmpl", f"{src}/robots.py"),
        ("logging_setup.py.tmpl", f"{src}/logging_setup.py"),
        ("export.py.tmpl", f"{src}/export.py"),
        (fetcher, f"{src}/fetcher.py"),
        (parse, f"{src}/parse.py"),
        (spider, f"{src}/spider.py"),
        # Tests.
        ("test_smoke.py.tmpl", "tests/test_smoke.py"),
        ("tests_init.py.tmpl", "tests/__init__.py"),
    ]


def render_project(cfg: ProjectConfig) -> list[GeneratedFile]:
    """Render every file for *cfg* in memory (no disk writes)."""
    context = _context(cfg)
    return [
        GeneratedFile(path=out, content=_render(template, context))
        for template, out in _manifest(cfg)
    ]


def generate(cfg: ProjectConfig, dest: str | Path, *, overwrite: bool = False) -> Path:
    """Generate the project into ``dest/<name>`` and return the project root.

    Raises :class:`ProjectExistsError` if the target exists and is non-empty,
    unless *overwrite* is true.
    """
    root = Path(dest) / cfg.name
    if root.exists() and any(root.iterdir()) and not overwrite:
        raise ProjectExistsError(f"{root} already exists and is not empty")

    for gen in render_project(cfg):
        target = root / gen.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(gen.content, encoding="utf-8")
    return root
