"""Generate projects for every engine/parser combo and validate the output."""

from __future__ import annotations

import ast
import itertools
import re

import pytest

from scraper_scaffold import (
    ProjectConfig,
    ProjectExistsError,
    generate,
    render_project,
)
from scraper_scaffold.config import ConfigError

# (engine, is_async) pairs that are valid. requests has no async API.
VALID_ENGINE_MODES = [
    ("requests", False),
    ("httpx", False),
    ("httpx", True),
    ("playwright", False),
    ("playwright", True),
]
PARSERS = ["parsel", "beautifulsoup"]

ALL_COMBOS = [
    (engine, parser, is_async)
    for (engine, is_async), parser in itertools.product(VALID_ENGINE_MODES, PARSERS)
]

ROOT_FILES = ["pyproject.toml", "requirements.txt", "README.md", ".gitignore", ".env.example"]
PACKAGE_MODULES = [
    "__init__.py",
    "__main__.py",
    "settings.py",
    "models.py",
    "ratelimit.py",
    "cache.py",
    "robots.py",
    "logging_setup.py",
    "export.py",
    "fetcher.py",
    "parse.py",
    "spider.py",
]

# Matches an unreplaced __PLACEHOLDER__ token (upper-case) but not dunders
# like __init__ / __future__ (which start with a lowercase letter).
PLACEHOLDER_RE = re.compile(r"__[A-Z][A-Z0-9_]*__")


@pytest.mark.parametrize("engine,parser,is_async", ALL_COMBOS)
def test_generates_valid_project(tmp_path, engine, parser, is_async):
    cfg = ProjectConfig(name="demo", engine=engine, parser=parser, is_async=is_async)
    root = generate(cfg, tmp_path)

    assert root == tmp_path / "demo"
    for rel in ROOT_FILES:
        assert (root / rel).is_file(), f"missing {rel}"

    pkg = root / "src" / "demo"
    for module in PACKAGE_MODULES:
        assert (pkg / module).is_file(), f"missing {module}"
    assert (root / "tests" / "test_smoke.py").is_file()

    # Every generated .py file must be syntactically valid Python.
    py_files = list(root.rglob("*.py"))
    assert py_files
    for path in py_files:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        compile(source, str(path), "exec")


@pytest.mark.parametrize("engine,parser,is_async", ALL_COMBOS)
def test_no_unreplaced_placeholders(tmp_path, engine, parser, is_async):
    cfg = ProjectConfig(name="demo", engine=engine, parser=parser, is_async=is_async)
    root = generate(cfg, tmp_path)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        leftover = PLACEHOLDER_RE.findall(text)
        assert not leftover, f"{path} has unreplaced placeholders: {leftover}"


def test_render_project_is_pure(tmp_path):
    # render_project returns content without touching disk.
    cfg = ProjectConfig(name="demo", engine="httpx", parser="parsel")
    files = render_project(cfg)
    assert not (tmp_path / "demo").exists()
    paths = {f.path for f in files}
    assert "pyproject.toml" in paths
    assert "src/demo/fetcher.py" in paths


def test_dependencies_track_engine_and_parser(tmp_path):
    cfg = ProjectConfig(name="demo", engine="requests", parser="beautifulsoup")
    root = generate(cfg, tmp_path)
    reqs = (root / "requirements.txt").read_text()
    assert "requests>=" in reqs
    assert "beautifulsoup4>=" in reqs
    assert "tenacity>=" in reqs
    assert "httpx" not in reqs
    assert "parsel" not in reqs

    pyproject = (root / "pyproject.toml").read_text()
    assert 'name = "demo"' in pyproject
    assert "requests>=" in pyproject


def test_generated_readme_links_to_site(tmp_path):
    cfg = ProjectConfig(name="demo", engine="httpx", parser="parsel", is_async=True)
    root = generate(cfg, tmp_path)
    readme = (root / "README.md").read_text()
    # Backlinks are markdown text links, not bare URLs.
    assert "](https://python-web-scraping.com" in readme
    assert "Retrying failed requests with tenacity" in readme
    assert "Async scraping with asyncio & HTTPX" in readme  # async-only feature


def test_cache_flag_toggles_defaults(tmp_path):
    cfg = ProjectConfig(name="demo", engine="httpx", parser="parsel", cache=False)
    root = generate(cfg, tmp_path)
    settings = (root / "src" / "demo" / "settings.py").read_text()
    assert "cache_enabled: bool = False" in settings
    assert "CACHE_ENABLED=false" in (root / ".env.example").read_text()


def test_package_name_normalization():
    cfg = ProjectConfig(name="My Cool-Scraper", engine="httpx", parser="parsel")
    assert cfg.package_name == "my_cool_scraper"


def test_requests_async_rejected():
    with pytest.raises(ConfigError):
        ProjectConfig(name="x", engine="requests", is_async=True)


def test_unknown_engine_rejected():
    with pytest.raises(ConfigError):
        ProjectConfig(name="x", engine="curl")


def test_existing_directory_guard(tmp_path):
    cfg = ProjectConfig(name="demo", engine="httpx", parser="parsel")
    generate(cfg, tmp_path)
    with pytest.raises(ProjectExistsError):
        generate(cfg, tmp_path)
    # overwrite lets it proceed.
    generate(cfg, tmp_path, overwrite=True)
