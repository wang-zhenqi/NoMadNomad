"""职位页「Activity on this job」区块。"""

from __future__ import annotations

from collections.abc import Callable

from bs4 import BeautifulSoup, Tag
from pydantic.dataclasses import dataclass

from nomadnomad.ingest.upwork.dom_utils import classes_include, read_first_text
from nomadnomad.models.job_posting_snapshot import JobActivity


@dataclass
class _ActivityDraft:
    """解析过程中累积 activity 字段（Pydantic dataclass，与领域 BaseModel 一致）。"""

    proposals_text: str | None = None
    last_viewed_by_client_text: str | None = None
    interviewing_count: int | None = None
    invites_sent: int | None = None
    unanswered_invites: int | None = None

    def to_model(self) -> JobActivity:
        return JobActivity(
            proposals_text=self.proposals_text,
            last_viewed_by_client_text=self.last_viewed_by_client_text,
            interviewing_count=self.interviewing_count,
            invites_sent=self.invites_sent,
            unanswered_invites=self.unanswered_invites,
        )


def _parse_optional_int(text: str) -> int | None:
    return int(text) if text.isdigit() else None


def _set_proposals(draft: _ActivityDraft, value_cell_text: str) -> None:
    draft.proposals_text = value_cell_text or None


def _set_last_viewed(draft: _ActivityDraft, value_cell_text: str) -> None:
    draft.last_viewed_by_client_text = value_cell_text or None


def _set_interviewing(draft: _ActivityDraft, value_cell_text: str) -> None:
    draft.interviewing_count = _parse_optional_int(value_cell_text)


def _set_invites_sent(draft: _ActivityDraft, value_cell_text: str) -> None:
    draft.invites_sent = _parse_optional_int(value_cell_text)


def _set_unanswered_invites(draft: _ActivityDraft, value_cell_text: str) -> None:
    draft.unanswered_invites = _parse_optional_int(value_cell_text)


# 按「标题包含子串」匹配；顺序：先匹配更长的专属文案，避免误伤
_ACTIVITY_ROW_RULES: tuple[tuple[str, Callable[[_ActivityDraft, str], None]], ...] = (
    ("Proposals", _set_proposals),
    ("Last viewed", _set_last_viewed),
    ("Interviewing", _set_interviewing),
    ("Invites sent", _set_invites_sent),
    ("Unanswered invites", _set_unanswered_invites),
)


def _read_activity_value_cell(list_item: Tag) -> str:
    value_span = list_item.find("span", class_="value")
    value_div = list_item.find("div", class_="value")
    if isinstance(value_span, Tag):
        return value_span.get_text(strip=True)
    if isinstance(value_div, Tag):
        return value_div.get_text(strip=True)
    return ""


def _apply_activity_row(draft: _ActivityDraft, row_title_text: str, value_cell_text: str) -> None:
    for title_keyword, apply_to_draft in _ACTIVITY_ROW_RULES:
        if title_keyword in row_title_text:
            apply_to_draft(draft, value_cell_text)
            return


def extract_activity(soup: BeautifulSoup) -> JobActivity | None:
    activity_list = soup.find("ul", class_=classes_include("client-activity-items"))
    if not isinstance(activity_list, Tag):
        return None
    draft = _ActivityDraft()
    for list_item in activity_list.find_all("li", class_=classes_include("ca-item")):
        if not isinstance(list_item, Tag):
            continue
        title_span = list_item.find("span", class_=classes_include("title"))
        row_title_text = read_first_text(title_span) or ""
        value_cell_text = _read_activity_value_cell(list_item)
        _apply_activity_row(draft, row_title_text, value_cell_text)
    return draft.to_model()
