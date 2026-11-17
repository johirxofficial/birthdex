# Changelog

All notable changes to BirthDex are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project uses [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-11-17

First public release.

### Added

- Manual captcha verification flow for birth (UBRN) and death (UDRN)
  registrations on the BDRIS e-Verify portal.
- JSON API: `GET|POST /api/verify` and `GET /api/captcha/<id>.png`.
- Flat single-page web UI (no frameworks, no modals, no build step).
- Single-use, TTL-bound in-memory captcha sessions (`CAPTCHA_TTL`,
  `CAPTCHA_CAPACITY`).
- Wrong captcha answers return `422` together with a freshly generated captcha.
- Result-page parser for the bilingual (Bangla/English) record layout.
- `birthdex` console command (Waitress WSGI server) and `python -m birthdex`.
- Installable package with bundled templates and static assets.
- Windows `run.bat`, Linux/macOS `run.sh`, Dockerfile and Docker Compose setup.
- Test suite (43 tests, offline) and GitHub Actions CI for Linux, Windows,
  macOS, packaging and Docker.
- Documentation: API reference, deployment guide, project guidelines,
  release process and a Telegram sharing kit.

### Notes

- No OCR, ML captcha solving or third-party solving services — by design.
- No database and no persistence of any record data.

[1.0.0]: https://github.com/johirxofficial/birthdex/releases/tag/v1.0.0
