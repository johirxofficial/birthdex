"""Console entry point: ``birthdex`` starts the server with Waitress."""

from __future__ import annotations

import argparse
import logging
import os

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="birthdex",
        description="Birth & death registration verification for Bangladesh "
                    "(manual captcha, no OCR).",
    )
    parser.add_argument(
        "-H", "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Bind address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=int(os.getenv("PORT", "5002") or 5002),
        help="HTTP port (default: 5002)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=int(os.getenv("THREADS", "8") or 8),
        help="Worker threads (default: 8)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("DEBUG", "").strip().lower() in ("1", "true", "yes", "on"),
        help="Enable Flask debug mode (development only)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"BirthDex {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    os.environ["HOST"] = args.host
    os.environ["PORT"] = str(args.port)
    if args.debug:
        os.environ["DEBUG"] = "1"

    # Rebuild settings with the CLI overrides.
    from .config import get_settings

    get_settings.cache_clear()

    from . import create_app

    app = create_app()
    log = logging.getLogger("birthdex")
    log.info("BirthDex %s on http://%s:%d", __version__, args.host, args.port)

    if args.debug:
        app.run(host=args.host, port=args.port, debug=True, threaded=True)
        return 0

    from waitress import serve

    serve(app, host=args.host, port=args.port, threads=max(2, args.threads))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
