"""BirthDex - birth & death registration verification for Bangladesh.

A small, dependency-light Flask application that verifies birth (UBRN) and
death (UDRN) registrations against the public BDRIS e-Verify portal.

The captcha is solved by a human: the API returns the captcha image, the
caller sends the answer back, and the record is returned.
"""

from __future__ import annotations

import logging
import os
from importlib.metadata import PackageNotFoundError, version as _dist_version

from flask import Flask, jsonify, request

from .config import get_settings
from .store import CaptchaStore

try:
    __version__ = _dist_version("birthdex")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "1.0.0"

log = logging.getLogger("birthdex")


def create_app(settings=None) -> Flask:
    settings = settings or get_settings()

    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
        template_folder="templates",
    )
    app.json.sort_keys = False
    app.config["SETTINGS"] = settings
    app.config["CAPTCHA_STORE"] = CaptchaStore(
        ttl=settings.captcha_ttl, capacity=settings.captcha_capacity
    )
    app.config["VERSION"] = __version__

    _configure_logging(settings.debug)

    from .api import bp as api_bp
    from .web import bp as web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    @app.after_request
    def add_cors_headers(response):
        response.headers.setdefault("Access-Control-Allow-Origin", settings.allow_origin)
        response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.setdefault(
            "Access-Control-Allow-Headers", "Content-Type, Accept"
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.errorhandler(404)
    def not_found(_err):
        if request.path.startswith("/api/"):
            return _json_error(404, "Unknown API endpoint.")
        return ("Not found", 404, {"Content-Type": "text/plain; charset=utf-8"})

    @app.errorhandler(405)
    def method_not_allowed(_err):
        resp = _json_error(405, f"Method {request.method} is not allowed here.")
        resp.headers["Allow"] = "GET, POST, OPTIONS"
        return resp

    @app.errorhandler(500)
    def server_error(_err):
        log.exception("unhandled error on %s", request.path)
        return _json_error(500, "Internal server error.")

    log.info("BirthDex %s ready (captcha: manual, sessions: %d)",
             __version__, settings.captcha_capacity)
    return app


def _json_error(code: int, message: str):
    response = jsonify(
        {
            "status": False,
            "success": False,
            "code": code,
            "message": message,
        }
    )
    response.status_code = code
    return response


def _configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        )
    logging.getLogger("birthdex").setLevel(level)
    if os.getenv("WERKZEUG_RUN_MAIN"):
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
