"""Input normalisation for registration numbers and dates."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

DOB_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d.%m.%Y")


def normalize_number(raw: str | None) -> Optional[str]:
    """Return the 17 digit UBRN/UDRN, or None if the input is not valid."""
    digits = re.sub(r"\D", "", raw or "")
    return digits if len(digits) == 17 else None


def normalize_dob(raw: str | None) -> Optional[str]:
    """Return an ISO date (YYYY-MM-DD), or None if the input is not a date."""
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in DOB_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def is_future(iso_date: str) -> bool:
    try:
        return date.fromisoformat(iso_date) > date.today()
    except ValueError:
        return False
