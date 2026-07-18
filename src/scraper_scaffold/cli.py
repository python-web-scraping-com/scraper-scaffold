"""Command-line interface for scraper-scaffold."""

from __future__ import annotations

from pathlib import Path

import click

from . import __version__
from .config import ENGINES, PARSERS, ConfigError, ProjectConfig
from .generator import ProjectExistsError, generate


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="scraper-scaffold")
def main() -> None:
    """Generate a polite-by-default Python web scraper project.

    Like create-react-app, but for scrapers: the generated project ships with
    rate limiting, retries, robots.txt honoring, on-disk caching and a
    descriptive User-Agent already wired in — so you start from responsible
    foundations instead of a blank file.
    """


@main.command()
@click.argument("name")
@click.option(
    "--engine",
    type=click.Choice(sorted(ENGINES)),
    default=None,
    help="HTTP / browser engine for the fetch layer.",
)
@click.option(
    "--parser",
    type=click.Choice(sorted(PARSERS)),
    default=None,
    help="HTML parser for the parse layer.",
)
@click.option(
    "--async/--sync",
    "is_async",
    default=None,
    help="Generate an async or synchronous scraper (async needs httpx/playwright).",
)
@click.option(
    "--cache/--no-cache",
    "cache",
    default=None,
    help="Enable on-disk HTTP response caching by default.",
)
@click.option(
    "--directory",
    "-d",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Parent directory to create the project in.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Write into the target directory even if it already exists.",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Accept all defaults without prompting (non-interactive).",
)
def new(
    name: str,
    engine: str | None,
    parser: str | None,
    is_async: bool | None,
    cache: bool | None,
    directory: Path,
    overwrite: bool,
    yes: bool,
) -> None:
    """Create a new scraper project called NAME.

    Fully non-interactive when every option is supplied (ideal for CI);
    otherwise you are prompted for the ones you left out.

    \b
    Examples:
      scraper-scaffold new price-watch --engine httpx --parser parsel --async -y
      scraper-scaffold new blog-crawler --engine requests --sync --no-cache -y
    """
    if engine is None:
        engine = "httpx" if yes else click.prompt(
            "Engine", type=click.Choice(sorted(ENGINES)), default="httpx"
        )
    if parser is None:
        parser = "parsel" if yes else click.prompt(
            "Parser", type=click.Choice(sorted(PARSERS)), default="parsel"
        )
    if is_async is None:
        # requests has no async API, so only offer async where it is valid.
        if engine == "requests":
            is_async = False
        else:
            is_async = False if yes else click.confirm("Async scraper?", default=False)
    if cache is None:
        cache = True if yes else click.confirm("On-disk HTTP cache?", default=True)

    try:
        cfg = ProjectConfig(
            name=name, engine=engine, parser=parser, is_async=is_async, cache=cache
        )
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        root = generate(cfg, directory, overwrite=overwrite)
    except ProjectExistsError as exc:
        raise click.ClickException(
            f"{exc}\nPass --overwrite to write into it anyway."
        ) from exc

    _report(cfg, root)


def _report(cfg: ProjectConfig, root: Path) -> None:
    click.secho(f"Created {cfg.name} ", fg="green", nl=False)
    click.echo(f"({cfg.engine} / {cfg.parser} / {cfg.mode})")
    click.echo(f"  -> {root}")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  cd {root}")
    click.echo("  python -m venv .venv && . .venv/bin/activate")
    click.echo('  pip install -e ".[dev]"')
    if cfg.engine == "playwright":
        click.echo("  playwright install chromium")
    click.echo(f"  python -m {cfg.package_name}   # runs the example spider")


@main.command(name="list")
def list_options() -> None:
    """List the available engines and parsers."""
    click.secho("Engines", bold=True)
    for name, desc in ENGINES.items():
        click.echo(f"  {name:<12} {desc}")
    click.echo("")
    click.secho("Parsers", bold=True)
    for name, desc in PARSERS.items():
        click.echo(f"  {name:<14} {desc}")
    click.echo("")
    click.secho("Modes", bold=True)
    click.echo("  --sync / --async   (async requires httpx or playwright)")
    click.echo("  --cache / --no-cache")


if __name__ == "__main__":
    main()
