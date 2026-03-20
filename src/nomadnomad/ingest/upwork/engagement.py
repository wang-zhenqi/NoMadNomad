"""用工形态、预算、项目类型（features 列表块）。"""

from __future__ import annotations

import re
from typing import Final

from bs4 import BeautifulSoup, Tag

from nomadnomad.ingest.upwork.dom_utils import classes_include, read_first_text
from nomadnomad.models.job_posting_snapshot import JobBudget, JobEngagement

_DOLLAR_AMOUNT: Final[re.Pattern[str]] = re.compile(r"\$?\s*([\d,.]+)")


def _engagement_features_list(soup: BeautifulSoup) -> Tag | None:
    features_ul = soup.select_one("ul.features.list-unstyled.m-0")
    return features_ul if isinstance(features_ul, Tag) else None


def _parse_two_dollar_amounts(budget_list_item: Tag) -> tuple[float, float] | None:
    amounts: list[float] = []
    for amount_strong in budget_list_item.find_all("strong"):
        amount_match = _DOLLAR_AMOUNT.search(amount_strong.get_text())
        if not amount_match:
            continue
        try:
            amounts.append(float(amount_match.group(1).replace(",", "")))
        except ValueError:
            continue
    if len(amounts) < 2:
        return None
    return amounts[0], amounts[1]


def extract_budget(soup: BeautifulSoup) -> JobBudget | None:
    features_list = _engagement_features_list(soup)
    if features_list is None:
        return None
    feature_items = features_list.find_all("li", recursive=False)
    if len(feature_items) < 4:
        return None
    budget_list_item = feature_items[3]
    if not isinstance(budget_list_item, Tag):
        return None
    min_max_pair = _parse_two_dollar_amounts(budget_list_item)
    if min_max_pair is None:
        return None
    min_usd, max_usd = min_max_pair
    rate_basis_div = budget_list_item.find("div", class_=classes_include("description"))
    basis_label = read_first_text(rate_basis_div)
    basis_normalized = basis_label.lower() if basis_label else None
    return JobBudget(min_usd=min_usd, max_usd=max_usd, basis=basis_normalized)


def extract_project_type(soup: BeautifulSoup) -> str | None:
    for label_strong in soup.find_all("strong"):
        if not isinstance(label_strong, Tag):
            continue
        if "Project Type:" not in label_strong.get_text():
            continue
        value_span = label_strong.find_next_sibling("span")
        return read_first_text(value_span)
    return None


def _duration_text_from_strong(duration_strong: Tag) -> str | None:
    desktop_duration_span = duration_strong.find("span", class_=classes_include("d-lg-inline", "d-none"))
    if isinstance(desktop_duration_span, Tag):
        return read_first_text(desktop_duration_span)
    return duration_strong.get_text(" ", strip=True) or None


def extract_engagement(soup: BeautifulSoup) -> JobEngagement | None:
    features_list = _engagement_features_list(soup)
    if features_list is None:
        return None
    feature_items = features_list.find_all("li", recursive=False)
    if len(feature_items) < 3:
        return None
    hours_strong = feature_items[0].find("strong")
    duration_strong = feature_items[1].find("strong")
    experience_strong = feature_items[2].find("strong")
    hours_text = read_first_text(hours_strong) if isinstance(hours_strong, Tag) else None
    duration_text = _duration_text_from_strong(duration_strong) if isinstance(duration_strong, Tag) else None
    experience_text = read_first_text(experience_strong) if isinstance(experience_strong, Tag) else None
    return JobEngagement(
        hours_per_week_text=hours_text,
        duration_text=duration_text,
        experience_level_text=experience_text,
        project_type_text=extract_project_type(soup),
    )
