"""In-memory store for pending captcha sessions.

Each entry is single use: :meth:`take` removes it, :meth:`get` only peeks
(needed because the captcha image is served separately from the answer).
"""

from __future__ import annotations

import secrets
import threading
import time
from collections import OrderedDict
from typing import Any, Optional


class CaptchaStore:
    def __init__(self, ttl: int = 600, capacity: int = 200):
        self.ttl = ttl
        self.capacity = capacity
        self._items: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()
        self._lock = threading.Lock()

    def add(self, value: Any) -> str:
        """Store *value* and return a URL-safe id."""
        token = secrets.token_urlsafe(16)
        now = time.time()
        with self._lock:
            self._purge(now)
            while len(self._items) >= self.capacity:
                self._items.popitem(last=False)
            self._items[token] = (now + self.ttl, value)
        return token

    def get(self, token: str) -> Optional[Any]:
        """Return the value without consuming it, or None if missing/expired."""
        with self._lock:
            entry = self._items.get(token)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= time.time():
                self._items.pop(token, None)
                return None
            return value

    def take(self, token: str) -> Optional[Any]:
        """Remove and return the value, or None if missing/expired."""
        with self._lock:
            entry = self._items.pop(token, None)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= time.time():
            return None
        return value

    def count(self) -> int:
        with self._lock:
            self._purge(time.time())
            return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def _purge(self, now: float) -> None:
        expired = [key for key, (expires_at, _) in self._items.items()
                   if expires_at <= now]
        for key in expired:
            self._items.pop(key, None)
