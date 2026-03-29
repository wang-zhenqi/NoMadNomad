# Story 6：LangGraph 编排「分析 → 提案」— GWT 测试点

与 [`docs/iteration_plan.md`](../iteration_plan.md) 中「故事 6」验收对齐；实现映射见下「测试文件映射」。

## 范围说明

- **图结构**：节点 1 需求分析（调用 `run_requirement_analysis_agent`），节点 2 提案生成（调用 `run_proposal_generation_agent`）；边为「分析成功且已落库 `requirement_analyses` → 提案」；任一步失败则终止（不执行后续节点）。
- **落库**：分析成功后写入 `requirement_analyses`；提案成功后写入 `proposals`；两次 Agent 调用各写一条 `agent_runs`，`agent_type` 分别为 `requirement_analyzer` 与 `proposal_generator`。
- **输入（三选一）**：`listing_html`（先经 Story 1 解析）、`job_posting_snapshot`（直接建项目）、`project_id`（从 `projects.listing_snapshot_json` 加载快照）。同时提供多项或皆不提供 → `ValueError`。
- **输出**：`project_id`、`requirement_analysis_id`、`proposal_id`、`status`（`success` / `failed_analysis` / `failed_proposal`）、`error_message`；可选携带两次 `agent_run_id` 便于断言。

## GWT 表

| ID | Given | When | Then |
|----|-------|------|------|
| S6-01 | 内存库已 `init_schema`；`resources/demo/demo_requirement.html` 字符串；mock LLM 依次返回合法 RequirementAnalysis JSON、合法 Proposal JSON | `run_analyze_proposal_workflow(..., listing_html=..., llm_client=mock)` | `status=success`；`requirement_analysis_id` 与 `proposal_id` 非空；`requirement_analyses` / `proposals` 行可 `get_by_id`；`agent_runs` 两条且 `agent_type` 分别为 `requirement_analyzer`、`proposal_generator` |
| S6-02 | 同上；mock **仅**返回无法通过 `RequirementAnalysis` 校验的 JSON（如 `technology_stack` 非数组，两次） | 同上 | `status=failed_analysis`；无 `requirement_analyses` 插入；无提案；分析侧 `agent_runs` 仍写入失败记录（与 Story 4 一致） |
| S6-03 | 已解析的 `JobPostingSnapshot`（由 golden HTML 解析）；mock 两次合法 JSON | `run_analyze_proposal_workflow(..., job_posting_snapshot=..., llm_client=mock)` | 与 S6-01 同样成功落库与双 `agent_type` |
| S6-04 | 已插入 `projects`（含 `listing_snapshot_json`）；mock 两次合法 JSON | `run_analyze_proposal_workflow(..., project_id=..., llm_client=mock)` | `status=success`；`project_id` 与插入一致；双表与 `agent_runs` 符合预期 |
| S6-05 | 同时传入 `listing_html` 与 `job_posting_snapshot` | `run_analyze_proposal_workflow` | `ValueError`（消息含 *exactly one*） |
| S6-06 | 分析成功；mock 第二次（提案）均无法解析为 Proposal | `run_analyze_proposal_workflow` | `status=failed_proposal`；`requirement_analysis_id` 已落库；无 `proposals` 行 |

## 测试文件映射

| 文件 | 覆盖 ID |
|------|---------|
| `tests/integration/test_analyze_proposal_workflow.py` | S6-01 — S6-06 |

## 主要入口与类型

- `nomadnomad.agents.analyze_proposal_workflow.run_analyze_proposal_workflow`
- `nomadnomad.agents.analyze_proposal_workflow.AnalyzeProposalWorkflowOutcome`

## 手动预览（CLI）

与 Story 5 相同：`poetry run preview-proposal-generation`（含 `--mock-llm`）在 Story 6 落地后应经 **LangGraph 编排** 写入 `requirement_analyses` 与 `proposals`；详见 `README.md` 本地开发小节。
