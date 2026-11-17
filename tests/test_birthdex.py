"""Test suite for BirthDex (pytest).

Run with::

    python -m pytest -q

The portal is never contacted: the tests replace ``portal.open_session`` and
feed canned HTML pages into the flow.
"""

from __future__ import annotations

import pytest

from birthdex import create_app
from birthdex.config import Settings
from birthdex.parser import looks_like_captcha_error, looks_like_not_found, parse_record
from birthdex.store import CaptchaStore
from birthdex.validation import is_future, normalize_dob, normalize_number

RESULT_HTML = """
<html><body>
<table>
  <tr><td>header</td></tr>
  <tr><td>sub</td></tr>
  <tr><td>2 January 2008</td><td>Example Union Parishad</td><td>2 January 2008</td></tr>
  <tr><td>middle</td></tr>
  <tr><td>1 January 1990</td><td>19901234567890123</td><td>MALE</td></tr>
</table>
<table>
  <tr><td>নিবন্ধিত ব্যক্তির নাম</td><td>মোঃ রহিম উদ্দিন</td><td>Registered Person Name</td><td>MD RAHIM UDDIN</td></tr>
  <tr><td>জন্মস্থান</td><td>ঢাকা</td><td>Place of Birth</td><td>DHAKA</td></tr>
  <tr><td>পিতার নাম</td><td>মোঃ করিম মিয়া</td><td>Father Name</td><td>MD KARIM MIA</td></tr>
  <tr><td>মাতার নাম</td><td>রহিমা বেগম</td><td>Mother Name</td><td>RAHIMA BEGUM</td></tr>
</table>
</body></html>
"""

CAPTCHA_HTML = "<html><body><p>The Captcha is not valid.</p></body></html>"
NOT_FOUND_HTML = "<html><body><p>No record found for the given information.</p></body></html>"


class FakeResponse:
    def __init__(self, html: str, status: int = 200):
        self.text = html
        self.content = html.encode()
        self.status_code = status


class FakePortalSession:
    def __init__(self, kind: str = "birth", html: str = RESULT_HTML):
        self.kind = kind
        self.html = html
        self.captcha_bytes = b"GIF89a" + b"\x00" * 160
        self.captcha_mime = "image/gif"
        self.answers: list[str] = []

    def search(self, number: str, dob: str, answer: str, settings) -> FakeResponse:
        self.answers.append(answer)
        return FakeResponse(self.html)


@pytest.fixture()
def app():
    application = create_app(Settings())
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def store(app):
    return app.config["CAPTCHA_STORE"]


def json_of(response):
    return response.get_json()


def use_portal(monkeypatch, html: str = RESULT_HTML, kind: str = "birth"):
    session = FakePortalSession(kind=kind, html=html)
    monkeypatch.setattr("birthdex.api.portal.open_session", lambda k, s: session)
    return session


# --------------------------------------------------------------------------- #
# Health and pages
# --------------------------------------------------------------------------- #

def test_health(client):
    code = client.get("/health")
    body = json_of(code)
    assert code.status_code == 200
    assert body["status"] is True
    assert body["captcha"] == "manual"
    assert body["service"] == "birthdex"


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "BirthDex" in html
    assert "Step 1" in html


def test_unknown_api_returns_json(client):
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert json_of(response)["success"] is False


def test_unknown_page_returns_404(client):
    assert client.get("/missing").status_code == 404


def test_method_not_allowed(client):
    response = client.put("/api/verify")
    assert response.status_code == 405
    assert response.headers["Allow"] == "GET, POST, OPTIONS"


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def test_missing_parameters(client):
    response = client.get("/api/verify")
    assert response.status_code == 400
    assert "Missing parameters" in json_of(response)["message"]


def test_invalid_number(client):
    response = client.get("/api/verify?number=123&dob=2000-01-31")
    assert response.status_code == 422


def test_invalid_dob(client):
    response = client.get("/api/verify?number=19971234567890123&dob=31/13/2000")
    assert response.status_code == 422


def test_future_dob(client):
    response = client.get("/api/verify?number=19971234567890123&dob=2999-01-01")
    assert response.status_code == 422


def test_invalid_type(client):
    response = client.get("/api/verify?type=marriage&number=19971234567890123&dob=2000-01-31")
    assert response.status_code == 400


def test_bad_json_body(client):
    response = client.post("/api/verify", data="{not json", content_type="application/json")
    assert response.status_code == 400


# --------------------------------------------------------------------------- #
# Captcha flow
# --------------------------------------------------------------------------- #

def test_captcha_required(client, monkeypatch):
    use_portal(monkeypatch)
    response = client.get("/api/verify?number=19971234567890123&dob=2000-01-31")
    body = json_of(response)
    assert response.status_code == 428
    assert body["captcha"]["id"]
    assert "/api/captcha/" in body["captcha"]["image_url"]
    assert body["captcha"]["expires_in"] == 600
    assert "captcha_id=" in body["verify_with"]


def test_captcha_image(client, store):
    session = FakePortalSession()
    captcha_id = store.add(session)
    response = client.get(f"/api/captcha/{captcha_id}.png")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/gif"
    assert "no-store" in response.headers["Cache-Control"]


def test_captcha_image_unknown(client):
    assert client.get("/api/captcha/doesnotexist.png").status_code == 410


def test_successful_lookup(client, store):
    session = FakePortalSession()
    captcha_id = store.add(session)
    response = client.get(
        "/api/verify?number=19971234567890123&dob=2000-01-31"
        f"&captcha_id={captcha_id}&captcha=41"
    )
    body = json_of(response)
    assert response.status_code == 200
    assert body["data"]["name_en"] == "MD RAHIM UDDIN"
    assert body["data"]["birth_registration_number"] == "19901234567890123"
    assert session.answers == ["41"]


def test_wrong_captcha_reissues(client, store, monkeypatch):
    monkeypatch.setattr("birthdex.api.portal.open_session",
                        lambda k, s: FakePortalSession(html=CAPTCHA_HTML))
    captcha_id = store.add(FakePortalSession(html=CAPTCHA_HTML))
    response = client.get(
        "/api/verify?number=19971234567890123&dob=2000-01-31"
        f"&captcha_id={captcha_id}&captcha=99"
    )
    body = json_of(response)
    assert response.status_code == 422
    assert body["captcha"]["id"] != captcha_id


def test_record_not_found(client, store):
    captcha_id = store.add(FakePortalSession(html=NOT_FOUND_HTML))
    response = client.get(
        "/api/verify?number=19971234567890123&dob=2000-01-31"
        f"&captcha_id={captcha_id}&captcha=41"
    )
    assert response.status_code == 404


def test_session_is_single_use(client, store):
    captcha_id = store.add(FakePortalSession())
    url = ("/api/verify?number=19971234567890123&dob=2000-01-31"
           f"&captcha_id={captcha_id}&captcha=41")
    assert client.get(url).status_code == 200
    assert client.get(url).status_code == 410


def test_expired_or_unknown_session(client):
    response = client.get(
        "/api/verify?number=19971234567890123&dob=2000-01-31"
        "&captcha_id=deadbeef&captcha=41"
    )
    assert response.status_code == 410


def test_answer_without_id(client):
    response = client.get("/api/verify?number=19971234567890123&dob=2000-01-31&captcha=41")
    assert response.status_code == 400


def test_id_without_answer(client, store):
    captcha_id = store.add(FakePortalSession())
    response = client.get(
        "/api/verify?number=19971234567890123&dob=2000-01-31"
        f"&captcha_id={captcha_id}"
    )
    assert response.status_code == 400


def test_type_mismatch(client, store):
    captcha_id = store.add(FakePortalSession(kind="birth"))
    response = client.get(
        "/api/verify?type=death&number=19971234567890123&dob=2000-01-31"
        f"&captcha_id={captcha_id}&captcha=41"
    )
    assert response.status_code == 410


def test_post_json_body(client, store):
    captcha_id = store.add(FakePortalSession())
    response = client.post(
        "/api/verify",
        json={
            "type": "birth",
            "number": "19971234567890123",
            "dob": "2000-01-31",
            "captcha_id": captcha_id,
            "captcha": "41",
        },
    )
    assert response.status_code == 200


def test_aliases_are_accepted(client, store):
    captcha_id = store.add(FakePortalSession())
    response = client.get(
        "/api/verify?num=1997-1234-56789-0123&date=31/01/2000"
        f"&session_id={captcha_id}&answer=41"
    )
    assert response.status_code == 200


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

def test_parse_record_fields():
    data = parse_record(RESULT_HTML)
    assert data is not None
    assert data["name_bn"] == "মোঃ রহিম উদ্দিন"
    assert data["father_name_en"] == "MD KARIM MIA"
    assert data["mother_name_bn"] == "রহিমা বেগম"
    assert data["date_of_birth"] == "1 January 1990"
    assert data["sex"] == "MALE"
    assert data["registration_office"] == "Example Union Parishad"


def test_parse_record_ignores_non_result_pages():
    assert parse_record(CAPTCHA_HTML) is None
    assert parse_record("<html><body>hello</body></html>") is None


def test_error_detection():
    assert looks_like_captcha_error(CAPTCHA_HTML)
    assert not looks_like_captcha_error(NOT_FOUND_HTML)
    assert looks_like_not_found(NOT_FOUND_HTML)
    assert not looks_like_not_found(RESULT_HTML)


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("19971234567890123", "19971234567890123"),
        ("1997 1234 56789 0123", "19971234567890123"),
        ("1234", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_number(raw, expected):
    assert normalize_number(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2000-01-31", "2000-01-31"),
        ("31/01/2000", "2000-01-31"),
        ("31-01-2000", "2000-01-31"),
        ("2000/01/31", "2000-01-31"),
        ("31.01.2000", "2000-01-31"),
        ("2000-13-40", None),
        ("", None),
    ],
)
def test_normalize_dob(raw, expected):
    assert normalize_dob(raw) == expected


def test_is_future():
    assert is_future("2999-01-01") is True
    assert is_future("2000-01-01") is False


# --------------------------------------------------------------------------- #
# Store
# --------------------------------------------------------------------------- #

def test_store_take_is_single_use():
    store = CaptchaStore(ttl=60, capacity=2)
    token = store.add("value")
    assert store.get(token) == "value"
    assert store.take(token) == "value"
    assert store.take(token) is None


def test_store_respects_capacity():
    store = CaptchaStore(ttl=60, capacity=2)
    first = store.add("a")
    store.add("b")
    store.add("c")
    assert store.get(first) is None
    assert store.count() == 2


def test_store_expires():
    store = CaptchaStore(ttl=0, capacity=2)
    token = store.add("value")
    assert store.get(token) is None
