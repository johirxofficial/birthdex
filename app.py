"""BirthDex entry point.

Run locally::

    python app.py

or with a production server::

    birthdex --host 0.0.0.0 --port 5002 --threads 8
"""

from __future__ import annotations

import logging

from birthdex import create_app
from birthdex.config import get_settings

app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    logging.getLogger("birthdex").info(
        "BirthDex listening on http://%s:%d", settings.host, settings.port
    )
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        threaded=True,
    )
