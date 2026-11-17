"""JSON API: the manual captcha verification flow."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import requests
from flask import Blueprint, Response, current_app, request, url_for

from . import portal
from .parser import looks_like_captcha_error, looks_like_not_found, parse_record
from .responses import envelope, send
from .validation import is_future, normalize_dob, normalize_number

log = logging.getLogger("birthdex.api")
bp = Blueprint("api", __name__, url_prefix="/api")

TYPES = ("birth", "death")


@bp.route("/verify", methods=["GET", "POST"])
def verify() -> Response:
    settings = current_app.config["SETTINGS"]
    store = current_app.config["CAPTCHA_STORE"]

    try:
        params = _read_params()
    except ValueError as exc:
        return send(envelope(400, str(exc), success=False), 400)

    kind = (_first(params, "type", "kind") or "birth").lower()
    if kind not in TYPES:
        return send(
            envelope(400, 'Parameter "type" must be "birth" or "death".', success=False),
            400,
        )

    raw_number = _first(params, "number", "num", "ubrn", "udrn")
    raw_dob = _first(params, "dob", "date", "birth_date", "death_date")

    if not raw_number or not raw_dob:
        return send(
            envelope(
                400,
                'Missing parameters. Send "number" (17 digits) and "dob" (YYYY-MM-DD).',
                success=False,
                usage="/api/verify?type=birth&number=19901234567890123&dob=1990-01-01",
            ),
            400,
        )

    number = normalize_number(raw_number)
    if not number:
        return send(
            envelope(
                422,
                '"number" must be a 17 digit registration number.',
                success=False,
                type=kind,
            ),
            422,
        )

    dob = normalize_dob(raw_dob)
    if not dob:
        return send(
            envelope(
                422,
                f'"dob" is not a valid date: {raw_dob}. Use YYYY-MM-DD.',
                success=False,
                type=kind,
                number=number,
            ),
            422,
        )
    if is_future(dob):
        return send(
            envelope(422, '"dob" cannot be in the future.', success=False,
                     type=kind, number=number),
            422,
        )

    answer = _first(params, "captcha", "answer")
    captcha_id = _first(params, "captcha_id", "session_id", "id")

    if not captcha_id and not answer:
        return _issue_captcha(kind, number, dob, 428,
                              "Captcha required. Read the captcha image, then "
                              "repeat the request with captcha_id and captcha.")

    if captcha_id and not answer:
        return send(
            envelope(400, 'Missing "captcha" answer for this captcha_id.',
                     success=False, type=kind, number=number, dob=dob),
            400,
        )

    if answer and not captcha_id:
        return send(
            envelope(400, 'The captcha answer needs its "captcha_id".',
                     success=False, type=kind, number=number, dob=dob),
            400,
        )

    session = store.take(captcha_id)
    if session is None:
        return send(
            envelope(410, "Captcha expired or unknown. Request a new one.",
                     success=False, type=kind, number=number, dob=dob),
            410,
        )

    if session.kind != kind:
        return send(
            envelope(410, "Captcha does not belong to this record type. "
                          "Request a new one.",
                     success=False, type=kind, number=number, dob=dob),
            410,
        )

    try:
        response = session.search(number, dob, answer, settings)
    except requests.Timeout:
        return send(
            envelope(504, "The BDRIS portal did not answer in time. Please retry.",
                     success=False, type=kind, number=number, dob=dob),
            504,
        )
    except requests.RequestException as exc:
        log.warning("portal request failed: %s", exc)
        return send(
            envelope(502, "Could not reach the BDRIS portal. Please retry.",
                     success=False, type=kind, number=number, dob=dob),
            502,
        )

    if response.status_code >= 500:
        return send(
            envelope(502, f"The BDRIS portal returned HTTP {response.status_code}. "
                          "Please retry later.",
                     success=False, type=kind, number=number, dob=dob),
            502,
        )

    html = response.text
    data = parse_record(html)

    if data:
        return send(
            envelope(
                200,
                f"{kind.capitalize()} record found.",
                success=True,
                type=kind,
                number=number,
                dob=dob,
                data=data,
            ),
            200,
        )

    if looks_like_captcha_error(html):
        return _issue_captcha(kind, number, dob, 422,
                              "That captcha answer was not accepted. "
                              "A new captcha is ready.")

    if looks_like_not_found(html):
        return send(
            envelope(404, f"No {kind} record matches this number and date.",
                     success=False, type=kind, number=number, dob=dob),
            404,
        )

    log.warning("unexpected portal page (%d bytes)", len(html))
    return send(
        envelope(502, "The portal returned an unexpected page. Please retry.",
                 success=False, type=kind, number=number, dob=dob),
        502,
    )


@bp.get("/captcha/<captcha_id>.png")
def captcha_image(captcha_id: str) -> Response:
    store = current_app.config["CAPTCHA_STORE"]
    session = store.get(captcha_id)
    if session is None:
        return send(
            envelope(410, "Captcha expired or unknown. Request a new one.",
                     success=False),
            410,
        )
    response = Response(session.captcha_bytes, mimetype=session.captcha_mime)
    response.headers["Cache-Control"] = "no-store, max-age=0, must-revalidate"
    return response


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _issue_captcha(kind: str, number: str, dob: str, code: int, message: str) -> Response:
    """Ask the caller for a captcha, attaching a fresh image and session id."""
    settings = current_app.config["SETTINGS"]
    store = current_app.config["CAPTCHA_STORE"]

    try:
        session = portal.open_session(kind, settings)
    except portal.PortalError as exc:
        log.warning("captcha session failed: %s", exc)
        return send(
            envelope(502, f"Could not start a captcha session with the portal: {exc}",
                     success=False, type=kind, number=number, dob=dob),
            502,
        )
    except requests.RequestException as exc:
        log.warning("captcha session network error: %s", exc)
        return send(
            envelope(502, "Could not reach the BDRIS portal for a captcha. "
                          "Please retry.",
                     success=False, type=kind, number=number, dob=dob),
            502,
        )

    captcha_id = store.add(session)
    verify_with = _absolute("api.verify") + "?" + urlencode(
        {
            "type": kind,
            "number": number,
            "dob": dob,
            "captcha_id": captcha_id,
            "captcha": "<your answer>",
        }
    )

    return send(
        envelope(
            code,
            message,
            success=False,
            type=kind,
            number=number,
            dob=dob,
            captcha={
                "id": captcha_id,
                "image_url": _absolute("api.captcha_image", captcha_id=captcha_id),
                "expires_in": settings.captcha_ttl,
            },
            verify_with=verify_with,
        ),
        code,
    )


def _absolute(endpoint: str, **values: Any) -> str:
    settings = current_app.config["SETTINGS"]
    if settings.public_base:
        return settings.public_base + url_for(endpoint, **values)
    return url_for(endpoint, _external=True, **values)


def _read_params() -> dict:
    if request.method == "POST":
        if request.is_json:
            data = request.get_json(silent=True)
            if data is None:
                raise ValueError("Request body must be valid JSON.")
            if not isinstance(data, dict):
                raise ValueError("JSON body must be an object.")
            return data
        return request.form.to_dict()
    return request.args.to_dict()


def _first(params: dict, *keys: str) -> str:
    lowered = {str(k).lower(): v for k, v in params.items()}
    for key in keys:
        value = lowered.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value not in (None, ""):
            return str(value)
    return ""
