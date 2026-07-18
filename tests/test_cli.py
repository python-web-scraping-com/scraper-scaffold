"""CLI tests — non-interactive generation must work end to end (for CI)."""

from __future__ import annotations

from click.testing import CliRunner

from scraper_scaffold.cli import main


def test_list_shows_engines_and_parsers():
    result = CliRunner().invoke(main, ["list"])
    assert result.exit_code == 0
    assert "httpx" in result.output
    assert "playwright" in result.output
    assert "parsel" in result.output
    assert "beautifulsoup" in result.output


def test_new_non_interactive(tmp_path):
    result = CliRunner().invoke(
        main,
        [
            "new", "shop-crawler",
            "--engine", "httpx",
            "--parser", "parsel",
            "--async",
            "--no-cache",
            "-y",
            "-d", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    project = tmp_path / "shop-crawler"
    assert (project / "pyproject.toml").is_file()
    assert (project / "src" / "shop_crawler" / "fetcher.py").is_file()


def test_new_uses_defaults_with_yes(tmp_path):
    result = CliRunner().invoke(main, ["new", "demo", "-y", "-d", str(tmp_path)])
    assert result.exit_code == 0, result.output
    # Defaults: httpx / parsel / sync.
    assert (tmp_path / "demo" / "src" / "demo" / "spider.py").is_file()


def test_new_requests_async_conflict(tmp_path):
    result = CliRunner().invoke(
        main,
        ["new", "demo", "--engine", "requests", "--async", "-y", "-d", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "async" in result.output.lower()


def test_new_existing_directory_errors(tmp_path):
    first = CliRunner().invoke(main, ["new", "demo", "-y", "-d", str(tmp_path)])
    assert first.exit_code == 0, first.output
    second = CliRunner().invoke(main, ["new", "demo", "-y", "-d", str(tmp_path)])
    assert second.exit_code != 0
    assert "overwrite" in second.output.lower()


def test_new_interactive_prompts(tmp_path):
    # No flags: click prompts. Feed answers on stdin.
    result = CliRunner().invoke(
        main,
        ["new", "demo", "-d", str(tmp_path)],
        input="httpx\nparsel\nn\ny\n",  # engine, parser, async?, cache?
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "demo" / "pyproject.toml").is_file()
