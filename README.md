# BirthDex

**Birth & death registration verification for Bangladesh — self-hosted, open source, human captcha only.**

[![CI](https://github.com/johirxofficial/birthdex/actions/workflows/ci.yml/badge.svg)](https://github.com/johirxofficial/birthdex/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](pyproject.toml)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed?logo=docker&logoColor=white)](Dockerfile)
[![No OCR](https://img.shields.io/badge/captcha-manual-0f766e)](docs/GUIDELINES.md)

BirthDex verifies a birth (UBRN) or death (UDRN) registration against the public
[BDRIS e-Verify](https://everify.bdris.gov.bd) portal and returns the record as
clean JSON.

The captcha is **never** solved by software. The API hands you the image, a
human types what it says, and the record comes back. No OCR, no OCR keys, no
third-party solving services, no headless browser.

```
GET /api/verify?type=birth&number=19901234567890123&dob=1990-01-01
→ 428  captcha required  +  captcha { id, image_url }

GET /api/verify?type=birth&number=19901234567890123&dob=1990-01-01&captcha_id=...&captcha=38
→ 200  birth record found + data { name_en, father_name_en, ... }
```

---

## Contents

- [Features](#features)
- [Install](#install)
- [Usage](#usage)
- [How it works](#how-it-works)
- [Configuration](#configuration)
- [Project layout](#project-layout)
- [Development](#development)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Legal & privacy](#legal--privacy)
- [License](#license)

---

## Features

- **Manual captcha flow** — two requests per lookup, no OCR anywhere.
- **Flat, lightweight UI** — one page, under 20 KB of CSS + JS, no framework,
  no modals, no build step.
- **Runs anywhere** — Windows, Linux, macOS, Docker, any Python 3.10+ host.
- **Small API surface** — `/api/verify` and `/api/captcha/<id>.png`.
- **Clean JSON** — `status / success / code / message` plus `data`, `captcha`
  or `verify_with` depending on the step.
- **Session hygiene** — captcha sessions are single-use, TTL bound (10 minutes
  by default) and capped in memory.
- **Nothing stored** — no database, no disk writes, no record cache.
- **Tested** — 43 offline tests, plus CI on Linux, Windows, macOS, packaging
  and Docker.

## Install

BirthDex needs **Python 3.10+** and outbound HTTPS to `everify.bdris.gov.bd`.
No database, no API keys, no configuration required.

### pipx (recommended for a CLI install)

```bash
pipx install git+https://github.com/johirxofficial/birthdex.git
birthdex            # http://localhost:5002
```

> Once the package is on PyPI (see
> [docs/RELEASING.md](docs/RELEASING.md#3-optional-pypi-with-trusted-publishing)),
> the same command becomes `pipx install birthdex`.

### pip (inside a virtual environment)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: . .venv/bin/activate
pip install "git+https://github.com/johirxofficial/birthdex.git"
birthdex
```

### Docker

```bash
docker run -d --name birthdex -p 5002:5002 --restart unless-stopped birthdex:latest
# or, from a checkout:
docker compose up --build -d
```

### From source

```bash
git clone https://github.com/johirxofficial/birthdex.git
cd birthdex
pip install -e .        # or: pip install -e ".[dev]" for tests
birthdex
```

One-click runners for a source checkout:

| Platform | Command |
|---|---|
| Windows | `run.bat` |
| Linux / macOS | `./run.sh` |

Both create `.venv`, install dependencies and start the server on port `5002`.

### Verify the install

```bash
curl http://localhost:5002/health
```

## Usage

Open <http://localhost:5002> for the web UI:

1. Pick **Birth** or **Death**, enter the 17-digit registration number and the
   date.
2. The portal captcha appears inline — type what you see.
3. The record renders as a flat table; **Copy JSON** copies the full response.

Command line:

```bash
birthdex --host 0.0.0.0 --port 5002 --threads 8
birthdex --version
python -m birthdex          # equivalent
python app.py               # source checkout
```

### API in one minute

```bash
# Step 1 — ask for a captcha
curl "http://localhost:5002/api/verify?type=birth&number=19901234567890123&dob=1990-01-01"

# Step 2 — send the answer (captcha_id from step 1)
curl "http://localhost:5002/api/verify?type=birth&number=19901234567890123&dob=1990-01-01&captcha_id=<id>&captcha=38"
```

Full reference: **[docs/API.md](docs/API.md)**.

## How it works

```
 Browser / API client                 BirthDex                    BDRIS portal
 ─────────────────────                ────────                    ────────────
 1. number + date  ──────────────▶  open portal session  ──────▶  GET page
                                        token + captcha id        ◀── HTML
                                        captcha image             ◀── GIF
    ◀── 428 captcha {id, image}         (kept in memory)

 2. captcha answer ──────────────▶  POST search form       ──────▶  POST
    ◀── 200 data / 422 new captcha   parse result table      ◀── HTML
```

- A captcha session lives in memory for 10 minutes and is used once.
- A wrong answer returns **422 with a fresh captcha**, so retrying is one step.
- Nothing is persisted: no record data, no captcha images on disk.

## Configuration

Environment variables (a `.env` file is loaded automatically):

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `5002` | HTTP port |
| `THREADS` | `8` | Waitress worker threads (`birthdex` command) |
| `DEBUG` | `0` | Flask debug mode (local only) |
| `CAPTCHA_TTL` | `600` | Seconds a captcha session stays valid |
| `CAPTCHA_CAPACITY` | `200` | Max pending sessions kept in memory |
| `CONNECT_TIMEOUT` | `10` | Portal connect timeout (seconds) |
| `READ_TIMEOUT` | `30` | Portal read timeout (seconds) |
| `ALLOW_ORIGIN` | `*` | CORS origin for browser clients |
| `PUBLIC_BASE_URL` | empty | Absolute URL used in captcha links behind a proxy |
| `PORTAL_BASE` | `https://everify.bdris.gov.bd` | Upstream portal (testing only) |

CLI flags `--host`, `--port`, `--threads` and `--debug` override the values
above.

## Project layout

```
birthdex/
├─ app.py                     # entry point for a source checkout
├─ birthdex/
│  ├─ __init__.py             # app factory, CORS, error handlers, version
│  ├─ cli.py                  # `birthdex` command (Waitress)
│  ├─ __main__.py             # `python -m birthdex`
│  ├─ api.py                  # /api/verify, /api/captcha/<id>.png
│  ├─ web.py                  # / and /health
│  ├─ portal.py               # BDRIS client (session, captcha, search POST)
│  ├─ parser.py               # result-page parser
│  ├─ store.py                # in-memory single-use captcha sessions
│  ├─ validation.py           # number / date normalisation
│  ├─ responses.py            # JSON envelope helpers
│  ├─ config.py               # environment settings + .env loader
│  ├─ templates/index.html    # single-page UI
│  └─ static/app.css, app.js  # flat stylesheet and vanilla JS
├─ tests/test_birthdex.py     # pytest suite (43 tests)
├─ docs/                      # API, deployment, guidelines, releasing, Telegram
├─ .github/                   # CI, release workflow, issue/PR templates
├─ pyproject.toml             # packaging (pip install birthdex)
├─ Dockerfile, docker-compose.yml
├─ run.bat, run.sh            # one-click local runners
├─ .env.example, .gitignore, .editorconfig, .gitattributes
├─ CHANGELOG.md, SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md
└─ LICENSE (MIT)
```

## Development

```bash
git clone https://github.com/johirxofficial/birthdex.git
cd birthdex
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
python app.py
```

The tests stub the portal, so they run offline and never touch BDRIS.
Style rules, module boundaries and the PR checklist live in
**[docs/GUIDELINES.md](docs/GUIDELINES.md)**.

## Deployment

Local network, Windows service with Waitress, Linux with Gunicorn + Nginx and
Docker instructions are in **[docs/DEPLOY.md](docs/DEPLOY.md)**.

> The captcha store is in-memory. Run one process with multiple threads
> (the `birthdex` command does this), or add a shared store before scaling to
> several workers.

## Documentation

| Document | Contents |
|---|---|
| [docs/API.md](docs/API.md) | Endpoints, response shapes, examples, status codes |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Local, LAN, production, Docker, troubleshooting |
| [docs/GUIDELINES.md](docs/GUIDELINES.md) | Architecture rules, coding standards, testing, PR checklist |
| [docs/RELEASING.md](docs/RELEASING.md) | Versioning, tags, CI, PyPI trusted publishing |
| [docs/TELEGRAM.md](docs/TELEGRAM.md) | Ready-to-post announcement and sharing kit |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |
| [SECURITY.md](SECURITY.md) | Reporting vulnerabilities |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

## Contributing

Issues and pull requests are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/GUIDELINES.md](docs/GUIDELINES.md) first.

Two rules are non-negotiable:

1. **The captcha stays manual.** OCR, ML models or third-party solving
   services will not be merged.
2. **Be a good citizen of the portal.** No bulk scraping, no load amplification,
   no bypassing rate limits.

## Legal & privacy

BirthDex is an independent open-source project. It is **not affiliated with**,
endorsed by, or supported by BDRIS or the Government of Bangladesh.

- Records contain personal data. Only look up records you are entitled to see
  and do not store or republish them without a lawful basis.
- BirthDex itself does not persist records or captcha images.
- You are responsible for complying with Bangladeshi law and the portal's terms
  of use when you self-host or use this software.

## License

[MIT](LICENSE) © 2026 BirthDex contributors
