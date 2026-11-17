"""Tiny helpers for the JSON envelope used by every endpoint."""

from __future__ import annotations

from flask import Response, jsonify


def envelope(code: int, message: str, *, success: bool, **extra) -> dict:
    """Build a response body with a stable key order."""
    body: dict = {
        "status": success,
        "success": success,
        "code": code,
        "message": message,
    }
    body.update(extra)
    return body


def send(body: dict, code: int) -> Response:
    return jsonify(body), code
