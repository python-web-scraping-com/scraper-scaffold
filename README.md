# scraper-scaffold

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/python-web-scraping-com/scraper-scaffold/actions/workflows/ci.yml/badge.svg)](https://github.com/python-web-scraping-com/scraper-scaffold/actions/workflows/ci.yml)

> Generate a **polite-by-default** Python web scraper project — like
> `create-react-app`, but for scrapers.

Most scrapers start life as a single `requests.get()` in a blank file, and the
responsible bits — rate limiting, retries, `robots.txt`, caching, an honest
User-Agent — get bolted on later (or never). `scraper-scaffold` flips that
around: it generates a complete, runnable project with all of that already
wired in, so you start from responsible foundations.

## What the generated project gives you

Every scaffolded project ships with a fetch layer that already does the right
things:

- **Descriptive User-Agent** — identifies your bot honestly instead of spoofing.
- **`robots.txt` honoring** — checks *allowed* and applies `Crawl-delay` before fetching.
- **Rate limiting** — a token-bucket limiter caps your requests/second.
- **Retries with exponential backoff + jitter** — via `tenacity`, respecting `Retry-After` on `429`/`503`.
- **On-disk HTTP cache** — re-runs read from disk instead of re-hitting the site.
- **Parse + export layers** — turn HTML into rows and write CSV/JSONL.
- **Env-configurable settings, structured logging, and an offline smoke test.**

You choose the engine and parser; the generated code, dependencies, README and
tests are tailored to your choices.

## Install

`scraper-scaffold` is not on PyPI — install it from source, straight from GitHub.
Since it's a command-line tool, [`pipx`](https://pipx.pypa.io) keeps it isolated:

```bash
pipx install git+https://github.com/python-web-scraping-com/scraper-scaffold.git
```

Or with plain `pip`:

```bash
pip install git+https://github.com/python-web-scraping-com/scraper-scaffold.git
```

Requires Python 3.9+.

## Usage

```bash
# Interactive — prompts for anything you don't pass as a flag:
scraper-scaffold new my-scraper

# Fully non-interactive (great for CI / scripts):
scraper-scaffold new price-watch --engine httpx --parser parsel --async -y
scraper-scaffold new blog-crawler --engine requests --sync --no-cache -y

# See what's available:
scraper-scaffold list
```

### Options for `new`

| Option | Choices | Default |
| ------ | ------- | ------- |
| `--engine` | `requests`, `httpx`, `playwright` | `httpx` |
| `--parser` | `parsel`, `beautifulsoup` | `parsel` |
| `--async / --sync` | — | `--sync` |
| `--cache / --no-cache` | — | `--cache` |
| `--directory, -d` | parent directory to create the project in | `.` |
| `--yes, -y` | accept defaults, never prompt | off |

`requests` is synchronous only; use `httpx` or `playwright` for `--async`.

### What you get

```
my-scraper/
├── pyproject.toml          # deps tailored to your engine/parser
├── requirements.txt
├── README.md               # links each feature to a how-to guide
├── .env.example            # every setting, documented
├── .gitignore
├── src/my_scraper/
│   ├── settings.py         # env-configurable settings
│   ├── fetcher.py          # session, rate limit, retries, cache, robots
│   ├── ratelimit.py        # token-bucket limiter (sync + async)
│   ├── cache.py            # on-disk response cache
│   ├── robots.py           # robots.txt parsing
│   ├── parse.py            # HTML -> rows (edit the selectors here)
│   ├── export.py           # CSV / JSONL writers
│   ├── logging_setup.py    # structured logging
│   └── spider.py           # example crawl loop + entrypoint
└── tests/
    └── test_smoke.py       # offline, deterministic
```

Then:

```bash
cd my-scraper
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m my_scraper          # runs the example spider
```

## Use as a library

```python
from scraper_scaffold import ProjectConfig, generate

cfg = ProjectConfig(name="my-scraper", engine="httpx", parser="parsel", is_async=True)
project_root = generate(cfg, ".")
```

## How it works

Templates are shipped as package data and rendered with a deliberately simple
`__TOKEN__` substitution — so the templates themselves stay valid, readable
Python. The generator picks the right engine/parser/mode variants and computes
the dependency list and README feature links for your configuration.

## Going deeper

`scraper-scaffold` gets you a responsible starting point; these guides from
[python-web-scraping.com](https://python-web-scraping.com) explain the *why* and
take each piece further:

- [The Complete Guide to Python Web Scraping](https://python-web-scraping.com/the-complete-guide-to-python-web-scraping/) — fundamentals, from HTTP to parsing.
- [How to scrape a static website without getting blocked](https://python-web-scraping.com/the-complete-guide-to-python-web-scraping/handling-pagination-and-infinite-scroll/how-to-scrape-a-static-website-without-getting-blocked/) — rate limiting and politeness in practice.
- [Retrying failed requests with tenacity](https://python-web-scraping.com/scaling-python-web-scrapers/asynchronous-scraping-with-asyncio-and-httpx/retrying-failed-requests-with-tenacity/) — the retry strategy baked into the fetcher.
- [Async scraping with asyncio & HTTPX](https://python-web-scraping.com/scaling-python-web-scrapers/asynchronous-scraping-with-asyncio-and-httpx/) — for the `--async` projects.
- [How to rotate User-Agents in Python](https://python-web-scraping.com/advanced-scraping-techniques-anti-bot-evasion/rotating-proxies-and-managing-ip-blocks/how-to-rotate-user-agents-in-python/) — beyond a single descriptive UA.
- [Rotating proxies and managing IP blocks](https://python-web-scraping.com/advanced-scraping-techniques-anti-bot-evasion/rotating-proxies-and-managing-ip-blocks/) — when a site pushes back.
- [Parsing HTML with BeautifulSoup](https://python-web-scraping.com/the-complete-guide-to-python-web-scraping/parsing-html-with-beautifulsoup/) — for the `--parser beautifulsoup` projects.
- [Playwright for modern web automation](https://python-web-scraping.com/advanced-scraping-techniques-anti-bot-evasion/using-playwright-for-modern-web-automation/) — for the `--engine playwright` projects.
- [Storing and exporting scraped data](https://python-web-scraping.com/scaling-python-web-scrapers/storing-and-exporting-scraped-data/) — beyond CSV/JSONL.

## Development

```bash
git clone https://github.com/python-web-scraping-com/scraper-scaffold.git
cd scraper-scaffold
pip install -e ".[dev]"
pytest
```

The test suite is offline and deterministic: it generates a project for every
engine/parser/mode combination into a temporary directory and asserts that the
expected files exist and that every generated `.py` file compiles.

## License

MIT — see [LICENSE](LICENSE).
