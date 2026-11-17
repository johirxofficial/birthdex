# Project guidelines

These rules keep BirthDex small, predictable and safe. They apply to every
change, including drive-by pull requests.

---

## 1. Product principles

1. **The captcha is human.** No OCR, no ML, no captcha-solving APIs, no
   headless-browser automation. This is a product decision, not a limitation.
2. **Two steps, one record.** Every lookup is: ask for a captcha, submit the
   answer, return the record.
3. **Nothing is stored.** No database, no record cache, no captcha images on
   disk. Pending captcha sessions live in memory and expire.
4. **Flat and quiet UI.** One page, inline states, no modals, no popups, no
   carousels, no spinners longer than a second.
5. **Small dependency surface.** Flask, requests, BeautifulSoup. Front-end has
   zero dependencies and no build step.

If a proposal conflicts with these, it needs a very good reason and a
maintainer discussion first.

---

## 2. Architecture

```
app.py                          source-checkout entry point (python app.py)
pyproject.toml                  packaging: deps, console script, package data
 └─ birthdex/
     ├─ __init__.py             app factory, CORS, error handlers, version
     ├─ cli.py                  `birthdex` command (Waitress)
     ├─ __main__.py             `python -m birthdex`
     ├─ web.py                  GET /, GET /health
     ├─ api.py                  GET|POST /api/verify, GET /api/captcha/<id>.png
     │   ├─ validation.py       number + date normalisation
     │   ├─ portal.py           BDRIS client (session, captcha download, POST)
     │   ├─ parser.py           result-page → dict
     │   ├─ store.py            in-memory single-use captcha sessions
     │   └─ responses.py        JSON envelope helpers
     ├─ config.py               environment settings + .env loader
     ├─ templates/index.html    UI shipped inside the package
     └─ static/app.css, app.js  flat stylesheet + vanilla JS
```

Rules:

- **`portal.py` never parses records.** It only fetches pages and returns
  responses or raises `PortalError`.
- **`parser.py` never performs network I/O.** It is pure and unit-tested with
  fixtures.
- **`api.py` owns the flow and the HTTP status codes.** No other module returns
  responses.
- **`store.py` owns lifetimes.** Single use, TTL, capacity — nothing else.
- **`config.py` is the only place that reads `os.environ`.**
- **Assets live inside the package.** Templates and static files must stay under
  `birthdex/` so that `pip install birthdex` ships a working UI. CI builds the
  wheel and asserts `/`, `/static/app.css` and `/static/app.js` all return 200.

### Request flow

```
verify()
  ├─ params → validation        (400 / 422)
  ├─ no captcha?      → _issue_captcha(428)
  ├─ captcha_id?      → store.take()          (410)
  ├─ portal session.search()                  (502 / 504)
  ├─ parser.parse_record()
  │    ├─ data        → 200
  │    ├─ captcha err → _issue_captcha(422)
  │    └─ not found   → 404
  └─ otherwise        → 502
```

---

## 3. Adding a new record type

The portal exposes more search forms; `birth` and `death` are wired today.
To add one (example: `marriage`):

1. `birthdex/portal.py`: add the page and search path to `PAGES` and `SEARCH`.
2. `birthdex/api.py`: add it to `TYPES`.
3. `birthdex/parser.py`: add label aliases if the page uses new field names.
4. `templates/index.html` + `static/app.js`: add a switch option and the date
   label.
5. `tests/test_birthdex.py`: add a success fixture, a not-found case and a type
   mismatch case.
6. `README.md` and `docs/API.md`: document it.

Never break the two existing types.

---

## 4. Coding standards

### Python

- Python 3.10+ syntax, `from __future__ import annotations` in every module.
- Type hints on public functions.
- 4-space indentation, ~100 character lines, double quotes.
- One responsibility per module; keep functions under ~50 lines.
- Custom exceptions carry context: `PortalError("...")` with a readable message.
- Log at the edge (`api.py`), not deep inside helpers, and never log personal
  data, captcha answers or full record payloads.

### Front-end

- Plain HTML, CSS and JS. No frameworks, no bundlers, no CDNs.
- Everything stays inline on the page — no modals, no dialogs, no popups.
- Use the CSS variables in `static/app.css`; no box shadows, no gradients.
- Build DOM with `textContent` (never `innerHTML` with data).
- Keyboard: every control reachable, visible focus, forms submit with Enter.
- Mobile: one column under 720 px, 44 px minimum tap targets.
- Messages go through the single `#alert` region (`role="alert"`).

### API design

- Keep the envelope: `status`, `success`, `code`, `message`.
- Additive changes only. Renaming or removing a field is a breaking change and
  needs a version bump and a note in the README.
- Status codes are fixed by `docs/API.md`; do not invent new ones.

---

## 5. Error handling

| Situation | Code | Where handled |
|---|---|---|
| Missing/invalid parameters | 400 | `api.verify` |
| Invalid number, invalid/future date | 422 | `api.verify` |
| Wrong captcha | 422 + new captcha | `api._issue_captcha` |
| Unknown/expired/used captcha | 410 | `api.verify` |
| Portal has no record | 404 | `api.verify` |
| Portal unreachable / bad page | 502 | `api.verify`, `api._issue_captcha` |
| Portal timeout | 504 | `api.verify` |
| Unknown API route | 404 | `__init__` handler |
| Unhandled exception | 500 | `__init__` handler |

Portal errors must never leak stack traces to clients. Include the exception
message only when it helps the caller act.

---

## 6. Security and privacy

- Do not add authentication bypasses, scraping modes or bulk endpoints.
- Do not write record data to disk, logs, telemetry or analytics.
- Do not put real records in tests, fixtures, screenshots or issues.
- Keep `CAPTCHA_CAPACITY` bounded; sessions are attacker-controllable input.
- Validate before touching the network: number shape, date format, type.
- Treat all portal HTML as untrusted input; parse, never execute.
- CORS is `*` by default because the API is read-only and data is personal —
  tighten `ALLOW_ORIGIN` if you serve a single known front-end.

---

## 7. Testing

- `python -m pytest -q` must pass; tests must run offline.
- Stub `portal.open_session` / `FakePortalSession.search`; never call BDRIS.
- Cover: validation edge cases, parser fixtures, every status code branch,
  single-use sessions, capacity/TTL, the image endpoint.
- New behaviour without a test is not done.
- Fixture data must be synthetic (the sample number is public-safe example data,
  but vary digits when adding new fixtures).

### Test map

| Area | Tests |
|---|---|
| Pages / health | `test_health`, `test_index_page`, `test_unknown_api_returns_json` |
| Validation | `test_missing_parameters` … `test_bad_json_body` |
| Captcha flow | `test_captcha_required` … `test_aliases_are_accepted` |
| Parser | `test_parse_record_fields`, `test_error_detection` |
| Store | `test_store_*` |

---

## 8. Documentation

Update documentation in the same pull request when you change:

- an endpoint, parameter, status code → `docs/API.md`
- a setting → `.env.example` + README table
- the run/deploy story → `docs/DEPLOY.md`
- the project structure → README layout section

---

## 9. Release checklist

1. `python -m pytest` — green.
2. `python -m compileall -q birthdex app.py`.
3. Bump the version in `pyproject.toml` and add a `CHANGELOG.md` entry.
4. `python -m build` and install the wheel in a clean venv; run
   `birthdex --version`.
5. Verify `GET /`, `/static/app.css`, `/static/app.js` and `/health` in the
   installed package.
6. Tag `vX.Y.Z`; the release workflow publishes the GitHub release (and PyPI
   when trusted publishing is enabled). See [RELEASING.md](RELEASING.md).
7. Verify both a successful lookup and a wrong-captcha retry on a real request.

---

## 10. Out of scope

- Automatic captcha solving of any kind.
- Bulk downloads, scraping pipelines, data dumps.
- Storing, indexing or reselling personal records.
- Anything that hides from the upstream service that automation is involved.
