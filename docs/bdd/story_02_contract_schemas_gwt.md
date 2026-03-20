# Story 2：需求分析与提案契约（GWT）

对应 [`docs/iteration_plan.md`](../iteration_plan.md) 故事 2。

## 范围冻结与延后

当前 GWT 仅覆盖**已实现**的 Schema 与 `parse_*` 行为；Story 2 在本 Sprint **不再扩展**字段。更丰富的契约（投标问答结构化、`Proposal` 分块等）记在迭代计划 **[§8 延后 Backlog](../iteration_plan.md)**（文中「## 8. 延后 Backlog」一节）。

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

## Story 1 + 2 集成

| ID | Given | When | Then |
|----|-------|------|------|
| I2-01 | `resources/demo/demo_requirement.html` 全文 | `parse_upwork_job_html` → 由快照字段组装的 dict → `parse_requirement_analysis`；再 `json.dumps` 二次解析 | `source_job_uid` 等与快照一致；预算/时间线/风险等断言与 golden 快照对齐 |
| I2-02 | 同上快照 | 用快照标题与 `job_uid` 组装 `Proposal` dict → `parse_proposal` | 标题与正文中可追溯 `job_uid` 与职位标题 |

测试文件：`tests/integration/test_snapshot_to_contract_pipeline.py`。
