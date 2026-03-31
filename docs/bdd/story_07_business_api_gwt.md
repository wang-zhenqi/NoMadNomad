# Story 7：业务 API（项目创建、分析、提案生成、查询）— GWT 测试点

与 [`docs/iteration_plan.md`](../iteration_plan.md) 中「故事 7」验收对齐；实现映射见下「测试文件映射」。

## 范围说明

- **项目创建**：支持 `listing_html`（解析为 `JobPostingSnapshot` 并持久化到 `projects.listing_snapshot_json`），或 `title + original_description`（构造最小快照并持久化），或直接提交 `job_posting_snapshot`。
- **分析触发**：`POST /projects/{id}/analyze` 基于项目已持久化的 `listing_snapshot_json` 调用需求分析 Agent，并写入 `requirement_analyses`（同时写入 `agent_runs`）。
- **提案触发**：`POST /projects/{id}/proposals` 基于该项目 **最新** `requirement_analysis` 生成提案，并写入 `proposals`（同时写入 `agent_runs`）。
- **查询**：`GET /projects/{id}` 返回项目基础信息，至少包含 `latest_requirement_analysis_id` 与 `latest_proposal_id`（若存在）；`GET /proposals/{id}` 返回提案内容（含 Markdown 字段）。
- **错误语义**：资源不存在返回 404；请求体校验失败返回 422；Agent/工作流失败返回 5xx（并包含可读错误信息）。

## GWT 表

| ID | Given | When | Then |
|----|-------|------|------|
| S7-01 | 使用内存库并已 `init_schema`；提供合法 `listing_html`（demo HTML） | `POST /projects` | 200；返回 `project_id`；`GET /projects/{id}` 能读到 `listing_snapshot_json` 已生成 |
| S7-02 | 已有项目且 `listing_snapshot_json` 存在；mock LLM 返回合法 RequirementAnalysis JSON | `POST /projects/{id}/analyze` | 200；返回 `requirement_analysis_id`；`GET /projects/{id}` 的 `latest_requirement_analysis_id` 等于该 id |
| S7-03 | 已有项目；且已存在至少 1 条 `requirement_analyses`；mock LLM 返回合法 Proposal JSON | `POST /projects/{id}/proposals` | 200；返回 `proposal_id`；`GET /proposals/{proposal_id}` 返回提案内容（含 Markdown 字段） |
| S7-04 | 不存在的 `project_id` | `POST /projects/{id}/analyze` 或 `POST /projects/{id}/proposals` 或 `GET /projects/{id}` | 404；错误信息包含 `project_id` |
| S7-05 | 创建项目请求体缺少必要字段（既无 `listing_html`，也无 `title+original_description`，也无 `job_posting_snapshot`） | `POST /projects` | 422；返回字段级校验错误或可读错误信息 |
| S7-06 | 一条端到端闭环：创建项目→分析→生成提案→查询项目与提案 | 依次调用上述接口 | 全链路 200；`GET /projects/{id}` 返回 `latest_*_id`；`GET /proposals/{id}` 返回内容 |

## 测试文件映射

| 文件 | 覆盖 ID |
|------|---------|
| `tests/integration/test_business_api.py` | S7-01 — S7-06 |

## 主要入口与路由

- `nomadnomad.main.create_app`
- `POST /projects`
- `POST /projects/{id}/analyze`
- `POST /projects/{id}/proposals`
- `GET /projects/{id}`
- `GET /proposals/{id}`
