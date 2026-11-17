"""Allow ``python -m birthdex`` to start the server."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
