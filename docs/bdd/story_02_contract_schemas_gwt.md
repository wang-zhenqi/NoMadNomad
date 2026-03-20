# Story 2：需求分析与提案契约（GWT）

对应 [`docs/iteration_plan.md`](../iteration_plan.md) 故事 2。

## 测试点映射

| ID | Given | When | Then |
|----|-------|------|------|
| S2-01 | 含技术栈、关键需求等字段的合法 dict | `parse_requirement_analysis` | 返回 `RequirementAnalysis`，字段一致 |
| S2-02 | 与 S2-01 等价的 JSON 字符串 | `parse_requirement_analysis` | 与 dict 路径结果一致 |
| S2-03 | 非合法 JSON 字符串 | `parse_requirement_analysis` | `ValueError`，消息含 `invalid JSON` |
| S2-04 | dict 中 `technology_stack` 类型错误 | `parse_requirement_analysis` | `pydantic.ValidationError` |
| S2-05 | 含 `title`、`body_markdown`、`template_variables` 的合法 dict | `parse_proposal` | 返回 `Proposal` |
| S2-06 | 合法 Proposal 的 JSON 字符串 | `parse_proposal` | 字段解析正确 |
| S2-07 | `title` 为空字符串 | `parse_proposal` | `ValidationError` |
| S2-08 | JSON 根为数组等非 object | `parse_proposal` | `ValueError`，消息含 `object` |

实现映射：`tests/unit/schemas/test_contract_parse.py`。
