"""BeautifulSoup 常用 DOM 辅助：具名 class 匹配，避免匿名 lambda 堆叠。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from bs4 import BeautifulSoup, Tag


def bs4_find_attrs(attrs: Mapping[str, str]) -> Any:
    """供 ``Tag.find(..., attrs=...)`` 使用：BeautifulSoup 类型存根对 ``attrs`` 的值类型较宽且 ``dict`` 不变，纯 ``str`` 在运行时可接受。"""
    return attrs


def class_tokens(class_value: object) -> frozenset[str]:
    """将 Tag 的 `class` 属性规范为 token 集合（支持 str / list）。"""
    if class_value is None:
        return frozenset()
    if isinstance(class_value, str):
        return frozenset(class_value.split())
    if isinstance(class_value, (list, tuple)):
        return frozenset(str(part) for part in class_value)
    return frozenset(str(class_value).split())


def classes_include(*required_tokens: str) -> Callable[[object], bool]:
    """生成 `class_=` 谓词：元素的 class 需同时包含给定 token。"""

    def _matches_all_required(class_value: object) -> bool:
        tokens = class_tokens(class_value)
        return bool(tokens) and all(required in tokens for required in required_tokens)

    return _matches_all_required


def read_first_text(tag: Tag | None, *, strip: bool = True) -> str | None:
    """安全读取节点文本；非 Tag 时返回 None。"""
    if not isinstance(tag, Tag):
        return None
    raw_text = tag.get_text(strip=strip)
    return raw_text or None


def find_strong_containing(soup: BeautifulSoup, substring: str) -> Tag | None:
    """在文档中查找文本包含子串的首个 <strong> 节点。"""
    for candidate_strong in soup.find_all("strong"):
        if isinstance(candidate_strong, Tag) and substring in candidate_strong.get_text():
            return candidate_strong
    return None
