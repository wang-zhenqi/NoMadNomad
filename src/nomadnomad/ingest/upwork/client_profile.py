"""About the client 区块 → ClientProfile。"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag
from pydantic.dataclasses import dataclass

from nomadnomad.ingest.upwork.dom_utils import classes_include, read_first_text
from nomadnomad.ingest.upwork.text import normalize_ws
from nomadnomad.models.job_posting_snapshot import ClientProfile


@dataclass
class _ClientProfileDraft:
    """聚合 About the client 各子块解析结果（Pydantic dataclass），再一次性构造 ClientProfile。"""

    payment_verified: bool = False
    rating_value: float | None = None
    reviews_text: str | None = None
    country: str | None = None
    city: str | None = None
    jobs_posted_text: str | None = None
    hire_stats_text: str | None = None
    total_spent_text: str | None = None
    avg_hourly_rate_paid_text: str | None = None
    industry: str | None = None
    company_size_text: str | None = None
    member_since_text: str | None = None

    def to_model(self) -> ClientProfile:
        return ClientProfile(
            payment_verified=self.payment_verified,
            rating_value=self.rating_value,
            reviews_text=self.reviews_text,
            country=self.country,
            city=self.city,
            jobs_posted_text=self.jobs_posted_text,
            hire_stats_text=self.hire_stats_text,
            total_spent_text=self.total_spent_text,
            avg_hourly_rate_paid_text=self.avg_hourly_rate_paid_text,
            industry=self.industry,
            company_size_text=self.company_size_text,
            member_since_text=self.member_since_text,
        )


def _fill_payment_and_rating(draft: _ClientProfileDraft, client_section: Tag) -> None:
    draft.payment_verified = bool(client_section.select_one(".payment-verified"))
    rating_value_element = client_section.select_one(".air3-rating-value-text")
    if isinstance(rating_value_element, Tag):
        rating_match = re.search(r"([\d.]+)", rating_value_element.get_text())
        if rating_match:
            draft.rating_value = float(rating_match.group(1))
    rating_block = client_section.find(attrs={"data-testid": "buyer-rating"})
    if not isinstance(rating_block, Tag):
        return
    for review_span in rating_block.find_all("span", class_=classes_include("nowrap")):
        review_line = review_span.get_text(strip=True)
        if "review" in review_line.lower():
            draft.reviews_text = review_line
            return


def _fill_location(draft: _ClientProfileDraft, client_section: Tag) -> None:
    location_list_item = client_section.find("li", attrs={"data-qa": "client-location"})
    if not isinstance(location_list_item, Tag):
        return
    country_strong = location_list_item.find("strong")
    draft.country = read_first_text(country_strong)
    city_spans = location_list_item.find_all("span", class_=classes_include("nowrap"))
    if city_spans:
        draft.city = read_first_text(city_spans[0])


def _fill_job_posting_stats(draft: _ClientProfileDraft, client_section: Tag) -> None:
    stats_list_item = client_section.find("li", attrs={"data-qa": "client-job-posting-stats"})
    if not isinstance(stats_list_item, Tag):
        return
    jobs_posted_strong = stats_list_item.find("strong")
    draft.jobs_posted_text = read_first_text(jobs_posted_strong)
    hire_summary_div = stats_list_item.find("div")
    draft.hire_stats_text = read_first_text(hire_summary_div)


def _fill_spend_and_rate(draft: _ClientProfileDraft, client_section: Tag) -> None:
    spend_strong = client_section.find("strong", attrs={"data-qa": "client-spend"})
    if isinstance(spend_strong, Tag):
        draft.total_spent_text = normalize_ws(spend_strong.get_text(" ", strip=True))
    hourly_rate_strong = client_section.find("strong", attrs={"data-qa": "client-hourly-rate"})
    if isinstance(hourly_rate_strong, Tag):
        draft.avg_hourly_rate_paid_text = normalize_ws(hourly_rate_strong.get_text(" ", strip=True))


def _fill_company_profile(draft: _ClientProfileDraft, client_section: Tag) -> None:
    company_list_item = client_section.find("li", attrs={"data-qa": "client-company-profile"})
    if not isinstance(company_list_item, Tag):
        return
    industry_strong = company_list_item.find("strong", attrs={"data-qa": "client-company-profile-industry"})
    draft.industry = read_first_text(industry_strong)
    company_size_div = company_list_item.find("div", attrs={"data-qa": "client-company-profile-size"})
    draft.company_size_text = read_first_text(company_size_div)


def _fill_member_since(draft: _ClientProfileDraft, client_section: Tag) -> None:
    contract_date_list_item = client_section.find("li", attrs={"data-qa": "client-contract-date"})
    if not isinstance(contract_date_list_item, Tag):
        return
    member_since_element = contract_date_list_item.find("small")
    draft.member_since_text = read_first_text(member_since_element)


def extract_client_profile(soup: BeautifulSoup) -> ClientProfile | None:
    client_section = soup.find(attrs={"data-test": "about-client-container"})
    if not isinstance(client_section, Tag):
        return None
    draft = _ClientProfileDraft()
    _fill_payment_and_rating(draft, client_section)
    _fill_location(draft, client_section)
    _fill_job_posting_stats(draft, client_section)
    _fill_spend_and_rate(draft, client_section)
    _fill_company_profile(draft, client_section)
    _fill_member_since(draft, client_section)
    return draft.to_model()
