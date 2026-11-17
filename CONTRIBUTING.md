# Contributing to BirthDex

Thanks for taking the time to contribute. BirthDex is small on purpose — a
focused, dependency-light tool — and contributions that keep it that way are
the most welcome.

## Before you start

1. Read [docs/GUIDELINES.md](docs/GUIDELINES.md) for the architecture and code
   rules.
2. Check open issues to avoid duplicate work.
3. For larger changes, open an issue first so we can agree on the approach.

## Non-negotiable rules

- **The captcha is manual.** Pull requests that add OCR, ML captcha solvers,
  third-party solving APIs or headless-browser automation of the captcha will
  be closed.
- **Respect the portal.** No bulk scraping, no concurrency amplification, no
  attempts to bypass rate limits or authentication.
- **No personal data in the repository.** Test fixtures must use synthetic
  records, never real citizens' data.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
python app.py
```

The test suite stubs the portal client, so it runs offline.

## Coding standards

- Python 3.10+, type hints on public functions, `from __future__ import annotations`.
- Keep modules single-purpose (`portal`, `parser`, `store`, `api`, `web`).
- No new runtime dependency without a clear justification in the PR.
- Front-end: plain HTML/CSS/JS, no framework, no build step, no popups/modals.
- Flat design, system fonts, keyboard accessible, mobile friendly.

Formatting is intentionally boring: 4 spaces, ~100 character lines, double
quotes. Run `python -m compileall` and the tests before pushing.

## Commit messages

Use short imperative subjects with a scope:

```
api: return a fresh captcha on a wrong answer
ui: keep the type switch in sync after reset
docs: document PUBLIC_BASE_URL for reverse proxies
tests: cover single-use captcha sessions
```

## Pull request checklist

- [ ] Tests added or updated, `python -m pytest -q` is green.
- [ ] No new dependency, or the dependency is justified.
- [ ] Docs updated (`README.md`, `docs/*`) when behaviour changes.
- [ ] Captcha remains manual; no personal data in code, tests or fixtures.
- [ ] The diff stays focused — no unrelated refactors.

## Reporting bugs

Include:

- What you did, what you expected, what happened.
- HTTP status and response body (redact personal data).
- Python version, OS, and whether you run it locally, via Docker or behind a
  proxy.

Never paste a real birth/death record or a real registration number in a public
issue. Use the synthetic example `19901234567890123 / 1990-01-01` pattern with
different digits.

## License

By contributing you agree that your contribution is licensed under the
[MIT License](LICENSE).
