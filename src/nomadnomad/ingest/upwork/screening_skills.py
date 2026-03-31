"""投标问题与技能标签。"""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from nomadnomad.ingest.upwork.dom_utils import classes_include, find_strong_containing
from nomadnomad.ingest.upwork.text import normalize_ws


def _mandatory_skills_container(mandatory_skills_heading: Tag) -> Tag | None:
    column_div = mandatory_skills_heading.find_parent("div", class_=classes_include("span-md-12"))
    if isinstance(column_div, Tag):
        return column_div
    next_sibling_div = mandatory_skills_heading.find_next_sibling("div")
    return next_sibling_div if isinstance(next_sibling_div, Tag) else None


def extract_screening_questions(soup: BeautifulSoup) -> list[str]:
    questions_ordered_list = soup.find("ol", class_=classes_include("list-styled"))
    if not isinstance(questions_ordered_list, Tag):
        return []
    questions: list[str] = []
    for question_item in questions_ordered_list.find_all("li", recursive=False):
        if not isinstance(question_item, Tag):
            continue
        question_text = normalize_ws(question_item.get_text(" ", strip=True))
        if question_text:
            questions.append(question_text)
    return questions


def extract_mandatory_skills(soup: BeautifulSoup) -> list[str]:
    mandatory_skills_heading = find_strong_containing(soup, "Mandatory skills")
    if mandatory_skills_heading is None:
        return []
    skills_section = _mandatory_skills_container(mandatory_skills_heading)
    if skills_section is None:
        return []
    skills_list_div = skills_section.find("div", class_=classes_include("skills-list"))
    if not isinstance(skills_list_div, Tag):
        return []
    skill_names: list[str] = []
    for line_clamp_node in skills_list_div.select(".air3-line-clamp"):
        skill_label = normalize_ws(line_clamp_node.get_text(strip=True))
        if skill_label:
            skill_names.append(skill_label)
    return skill_names
