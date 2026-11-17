"""HTML pages and the health endpoint."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template

bp = Blueprint("web", __name__)


@bp.get("/")
def index():
    return render_template("index.html", version=current_app.config["VERSION"])


@bp.get("/health")
def health():
    settings = current_app.config["SETTINGS"]
    store = current_app.config["CAPTCHA_STORE"]
    return jsonify(
        {
            "status": True,
            "success": True,
            "code": 200,
            "message": "OK",
            "service": "birthdex",
            "version": current_app.config["VERSION"],
            "captcha": "manual",
            "sessions": {
                "active": store.count(),
                "capacity": store.capacity,
                "ttl_seconds": settings.captcha_ttl,
            },
            "endpoints": [
                "/",
                "/health",
                "/api/verify",
                "/api/captcha/<id>.png",
            ],
        }
    )
