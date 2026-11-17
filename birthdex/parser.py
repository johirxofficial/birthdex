"""Parser for the BDRIS result page.

The portal renders the record inside HTML tables. Two layouts are handled:

* a fixed meta table (registration date / office / issue date and
  date of birth / registration number / sex), and
* a label/value table where each row repeats the field in Bangla and English,
  e.g. ``[label_bn, value_bn, label_en, value_en]``.
"""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

# Longest labels first so "মাতার নাম" wins over "নাম".
FIELD_ALIASES = (
    (("পিতার জাতীয়তা", "পিতার জাতীয়তা", "father nationality", "father's nationality"),
     "father_nationality"),
    (("মাতার জাতীয়তা", "মাতার জাতীয়তা", "mother nationality", "mother's nationality"),
     "mother_nationality"),
    (("পিতার নাম", "father name", "father's name"), "father_name"),
    (("মাতার নাম", "mother name", "mother's name"), "mother_name"),
    (("জন্মস্থান", "place of birth"), "birth_place"),
    (("জন্ম তারিখ", "date of birth"), "date_of_birth"),
    (("নিবন্ধন কার্যালয়", "নিবন্ধন কার্যালয়", "registration office"), "registration_office"),
    (("ইস্যুর তারিখ", "issue date", "issuance date"), "issuance_date"),
    (("নিবন্ধনের তারিখ", "registration date"), "registration_date"),
    (("লিঙ্গ", "gender", "sex"), "sex"),
    (("নিবন্ধিত ব্যক্তির নাম", "registered person name", "name of registered person"), "name"),
    (("নাম", "name"), "name"),
)

MULTI_VALUE_FIELDS = {
    "name",
    "birth_place",
    "mother_name",
    "father_name",
    "mother_nationality",
    "father_nationality",
}

SINGLE_VALUE_FIELDS = {
    "registration_date",
    "registration_office",
    "issuance_date",
    "date_of_birth",
    "birth_registration_number",
    "sex",
}

NOT_FOUND_MARKERS = (
    "no record found",
    "record not found",
    "no data found",
    "কোনো তথ্য পাওয়া যায়নি",
    "কোন তথ্য পাওয়া যায়নি",
    "পাওয়া যায়নি",
)

CAPTCHA_ERROR_MARKERS = (
    "captcha is not valid",
    "captcha not valid",
    "invalid captcha",
    "incorrect captcha",
    "captcha does not match",
)


def parse_record(html: str | bytes) -> Optional[dict]:
    """Return the record fields, or None if the page is not a result page."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return None

    data: dict[str, str] = {}

    # Fixed meta table: row 2 and row 4 carry the summary values.
    meta_rows = [[cell.get_text(" ", strip=True) for cell in tr.find_all(["td", "th"])]
                 for tr in tables[0].find_all("tr")]
    if len(meta_rows) >= 5:
        if len(meta_rows[2]) >= 3:
            data.setdefault("registration_date", meta_rows[2][0])
            data.setdefault("registration_office", meta_rows[2][1])
            data.setdefault("issuance_date", meta_rows[2][2])
        if len(meta_rows[4]) >= 3:
            data.setdefault("date_of_birth", meta_rows[4][0])
            data.setdefault("birth_registration_number", meta_rows[4][1])
            data.setdefault("sex", meta_rows[4][2])

    # Label driven pass: handles both [label, value] and the bilingual layout.
    for table in tables:
        for row in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
            for index in range(0, len(cells) - 1, 2):
                field = match_field(cells[index])
                value = cells[index + 1]
                if not field or not value:
                    continue
                language = "bn" if _has_bengali(cells[index]) else "en"
                data.setdefault(f"{field}_{language}", value)

    cleaned = {
        key: value
        for key, value in data.items()
        if value and _keep(key)
    }
    return cleaned or None


def match_field(label: str) -> Optional[str]:
    text = re.sub(r"\s+", " ", label or "").strip().strip(":：").lower()
    if not text:
        return None
    for aliases, field in FIELD_ALIASES:
        for alias in aliases:
            if text == alias.lower() or text.startswith(alias.lower()):
                return field
    if "নাম" in text and "মাতার" not in text and "পিতার" not in text:
        return "name"
    if "name" in text and "mother" not in text and "father" not in text:
        return "name"
    return None


def looks_like_captcha_error(html: str | bytes) -> bool:
    text = _text(html).lower()
    return "captcha" in text and any(marker in text for marker in CAPTCHA_ERROR_MARKERS)


def looks_like_not_found(html: str | bytes) -> bool:
    text = _text(html)
    low = text.lower()
    return any(marker in low for marker in NOT_FOUND_MARKERS) or any(
        marker in text for marker in NOT_FOUND_MARKERS if _has_bengali(marker)
    )


def _keep(key: str) -> bool:
    base = key
    for suffix in ("_bn", "_en"):
        if key.endswith(suffix):
            base = key[: -len(suffix)]
    return base in MULTI_VALUE_FIELDS or key in SINGLE_VALUE_FIELDS


def _has_bengali(text: str) -> bool:
    return bool(re.search(r"[\u0980-\u09FF]", text or ""))


def _text(html: str | bytes) -> str:
    if isinstance(html, bytes):
        html = html.decode("utf-8", "ignore")
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
