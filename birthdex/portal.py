"""Minimal client for the BDRIS e-Verify portal.

The portal flow is a classic ASP.NET MVC form:

1. ``GET`` the verification page -> anti-forgery token + captcha id + image.
2. ``POST`` the search form with the token, the registration number, the date
   and the captcha answer.

The captcha text is entered by a human, so this module never tries to read the
image. It only keeps the portal session alive until the answer arrives.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Settings

PAGES = {
    "birth": "/",
    "death": "/UDRNVerification",
}

SEARCH = {
    "birth": "/UBRNVerification/Search",
    "death": "/UDRNVerification/Search",
}

MIME_SIGNATURES = (
    (b"GIF8", "image/gif"),
    (b"\x89PNG", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"<svg", "image/svg+xml"),
)


class PortalError(RuntimeError):
    """The portal answered with something unusable."""


@dataclass
class PortalSession:
    """One portal visit: token, captcha id and the downloaded captcha image."""

    kind: str
    http: requests.Session = field(repr=False)
    page_url: str
    search_url: str
    token: str
    captcha_id: str
    captcha_url: str
    captcha_bytes: bytes
    captcha_mime: str = "image/gif"
    created_at: float = field(default_factory=time.time)

    def search(self, number: str, dob: str, answer: str, settings: Settings) -> requests.Response:
        return self.http.post(
            self.search_url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": settings.portal_base,
                "Referer": self.page_url,
            },
            data={
                "__RequestVerificationToken": self.token,
                "UBRN": number,
                "BirthDate": dob,
                "CaptchaDeText": self.captcha_id,
                "CaptchaInputText": answer,
            },
            timeout=settings.portal_timeout,
            allow_redirects=True,
        )


def sniff_mime(data: bytes) -> str:
    for signature, mime in MIME_SIGNATURES:
        if data.startswith(signature):
            return mime
    return "image/gif"


def _http_client(settings: Settings) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=1,
        backoff_factor=0.6,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": settings.user_agent,
            "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
        }
    )
    return session


def open_session(kind: str, settings: Settings) -> PortalSession:
    """Load the verification page and download a fresh captcha image."""
    if kind not in PAGES:
        raise ValueError(f"Unsupported record type: {kind}")

    http = _http_client(settings)
    page_url = settings.portal_base + PAGES[kind]

    try:
        page = http.get(page_url, timeout=settings.portal_timeout)
        page.raise_for_status()
    except requests.RequestException as exc:
        raise PortalError(f"Could not load the portal page: {exc}") from exc

    soup = BeautifulSoup(page.content, "html.parser")

    token_input = soup.find("input", {"name": "__RequestVerificationToken"})
    if not token_input or not token_input.get("value"):
        raise PortalError("The portal did not return an anti-forgery token.")

    captcha_img = soup.find("img", {"id": "CaptchaImage"})
    if not captcha_img or not captcha_img.get("src"):
        raise PortalError("The portal did not return a captcha image.")

    hidden = soup.find("input", {"name": "CaptchaDeText"})
    src = captcha_img["src"]
    captcha_url = urljoin(page_url, src)

    captcha_de_text = (hidden.get("value") if hidden else None) or _query_param(src, "t")
    if not captcha_de_text:
        raise PortalError("The portal did not return a captcha id.")

    try:
        image = http.get(
            captcha_url,
            headers={
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": page_url,
            },
            timeout=settings.portal_timeout,
        )
        image.raise_for_status()
    except requests.RequestException as exc:
        raise PortalError(f"Could not download the captcha image: {exc}") from exc

    if len(image.content) < 100:
        raise PortalError("The captcha image was empty.")

    return PortalSession(
        kind=kind,
        http=http,
        page_url=page_url,
        search_url=settings.portal_base + SEARCH[kind],
        token=token_input["value"].strip(),
        captcha_id=captcha_de_text,
        captcha_url=captcha_url,
        captcha_bytes=image.content,
        captcha_mime=sniff_mime(image.content),
    )


def _query_param(url: str, name: str) -> str:
    if f"{name}=" not in url:
        return ""
    tail = url.split(f"{name}=", 1)[1]
    return tail.split("&", 1)[0]
