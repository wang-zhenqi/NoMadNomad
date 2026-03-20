"""契约校验入口（与 ``models`` 中的领域模型配合使用）。"""

from nomadnomad.schemas.contract_parse import parse_proposal, parse_requirement_analysis

__all__ = [
    "parse_proposal",
    "parse_requirement_analysis",
]
