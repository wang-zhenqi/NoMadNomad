# Story 3：SQLite 数据层 — GWT 测试点

与 `[docs/iteration_plan.md](../iteration_plan.md)` 中「故事 3」验收对齐；实现映射见 `tests/integration/test_sqlite_repositories.py`。


| ID    | Given              | When                                           | Then                                                                    |
| ----- | ------------------ | ---------------------------------------------- | ----------------------------------------------------------------------- |
| S3-01 | 内存库已 `init_schema` | `ProjectRepo.insert` 后 `get_by_id`             | `title`、`listing_html`、`listing_snapshot_json` 与写入一致                    |
| S3-02 | 已存在 `project`      | `RequirementAnalysisRepo.insert` / `get_by_id` | `analysis_json` 与 `RequirementAnalysis.model_dump()` 一致；`project_id` 正确 |
| S3-03 | 已存在 `project`      | `ProposalRepo.insert` / `get_by_id`            | `proposal_json` 与 `Proposal.model_dump()` 一致                            |
| S3-04 | 已存在 `project`      | `AgentRunRepo.insert` / `get_by_id`            | `agent_type`、`success`（0/1）、`trace_id`、payload JSON 一致                  |
| S3-05 | 已存在 `project`      | `AppEventRepo.insert` / `get_by_id`            | `event_type`、`level`、`trace_id`、`source`、`payload_json` 一致              |
| S3-06 | 临时目录下新库文件          | 两次 `connect_file` + `init_schema` 后插入 project  | 幂等无报错；可正常读写                                                             |
