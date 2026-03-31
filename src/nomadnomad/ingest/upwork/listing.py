"""职位卡片顶部与摘要、Connects 等 listing 级字段。"""

from __future__ import annotations

import re
from typing import Final

from bs4 import BeautifulSoup, Tag

from nomadnomad.ingest.upwork.dom_utils import bs4_find_attrs, classes_include, read_first_text
from nomadnomad.ingest.upwork.text import normalize_ws

_POSTED_ROW_CLASS: Final[tuple[str, ...]] = ("posted-on-line",)
_LOCATION_PARAGRAPH_CLASS: Final[tuple[str, ...]] = ("text-light-on-muted", "m-0")
_SUMMARY_BLOCK_ATTR: Final[dict[str, str]] = {"data-test": "Description"}

_CONNECTS_REQUIRED_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"Send a proposal for:\s*.*?(\d+)\s*Connects",
    re.I | re.DOTALL,
)
_CONNECTS_AVAILABLE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"Available Connects:\s*.*?(\d+)",
    re.I | re.DOTALL,
)


def extract_title(soup: BeautifulSoup) -> str | None:
    job_title_heading = soup.find("h4")
    if not isinstance(job_title_heading, Tag):
        return None
    title_span = job_title_heading.find("span", class_=classes_include("flex-1"))
    return read_first_text(title_span)


def extract_job_uid(soup: BeautifulSoup) -> str | None:
    job_uid_element = soup.find(attrs={"job-uid": True})
    if not isinstance(job_uid_element, Tag):
        return None
    uid_attr = job_uid_element.get("job-uid")
    return str(uid_attr) if uid_attr else None


def _find_posted_row(soup: BeautifulSoup) -> Tag | None:
    posted_row = soup.find("div", class_=classes_include(*_POSTED_ROW_CLASS))
    return posted_row if isinstance(posted_row, Tag) else None


def extract_posted_text(soup: BeautifulSoup) -> str | None:
    posted_row = _find_posted_row(soup)
    if posted_row is None:
        return None
    posted_raw = posted_row.get_text(" ", strip=True)
    return normalize_ws(posted_raw) if posted_raw else None


def extract_client_location_listing(soup: BeautifulSoup) -> str | None:
    """职位卡片顶部「地区」一行（如 Worldwide），非 About the client。"""
    posted_row = _find_posted_row(soup)
    if posted_row is None:
        return None
    parent_section = posted_row.find_parent("section")
    if not isinstance(parent_section, Tag):
        return None
    location_paragraph = parent_section.find("p", class_=classes_include(*_LOCATION_PARAGRAPH_CLASS))
    return read_first_text(location_paragraph)


def extract_summary(soup: BeautifulSoup) -> str | None:
    description_block = soup.find(attrs=bs4_find_attrs(_SUMMARY_BLOCK_ATTR))
    if not isinstance(description_block, Tag):
        return None
    summary_paragraph = description_block.find("p", class_=classes_include("multiline-text"))
    if not isinstance(summary_paragraph, Tag):
        return None
    return summary_paragraph.get_text("\n", strip=False).strip() or None


def extract_connects_required(html_text: str) -> int | None:
    pattern_match = _CONNECTS_REQUIRED_PATTERN.search(html_text)
    return int(pattern_match.group(1)) if pattern_match else None


def extract_connects_available(html_text: str) -> int | None:
    pattern_match = _CONNECTS_AVAILABLE_PATTERN.search(html_text)
    return int(pattern_match.group(1)) if pattern_match else None
