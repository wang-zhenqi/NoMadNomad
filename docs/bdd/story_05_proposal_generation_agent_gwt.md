# Story 5：提案生成 Agent（单节点）— GWT 测试点

与 [`docs/iteration_plan.md`](../iteration_plan.md) 中「故事 5」验收对齐；实现映射见下「测试文件映射」。

## 范围说明

- **输入**：`RequirementAnalysis` **或** `requirement_analysis_id`（从 DB 加载），二者**互斥**；同时提供或皆不提供时失败；按 id 加载时行不存在则 `ValueError`，**不**写入 `agent_runs`。
- **输出**：`Proposal`（经 `parse_proposal` 校验；`body_markdown` 为 Markdown）；成功后对正文长度做上限校验（合理长度，超限视同解析失败）。
- **LLM**：结构化 JSON（系统 Prompt + `JsonCompletionClient`）；与 Story 4 一致：**解析**失败时最多再请求一次 LLM（修复提示）；HTTP 等异常不重试。
- **落库**：每次调用写入 `agent_runs`（`agent_type=proposal_generator`、input/output JSON、`success`、`duration_ms`、`error_message`、`trace_id`）。

## GWT 表

| ID | Given | When | Then |
|----|-------|------|------|
| S5-01 | 内存库已 `init_schema`；已插入 `project`；mock LLM 返回合法 `Proposal` JSON | `run_proposal_generation_agent(..., requirement_analysis=..., llm_client=mock)` | 返回 `proposal` 非空；`agent_runs` 行 `success=1`；`input_payload_json` 含分析线索；`output_payload_json` 与 `proposal.model_dump()` 一致；`trace_id`、`duration_ms` 有值 |
| S5-02 | 同上；mock **两次**返回无法解析为 `Proposal` 的 JSON | `run_proposal_generation_agent(..., llm_client=mock)` | `proposal` 为空；`error_message` 非空；`agent_runs` 行 `success=0` |
| S5-03 | mock 首次返回非 JSON、第二次返回合法 JSON | `run_proposal_generation_agent(...)` | 最终成功；LLM 被调用 **2** 次；`agent_runs` 成功 |
| S5-04 | 已插入 `requirement_analyses` 行；mock 返回合法 Proposal JSON | `run_proposal_generation_agent(..., requirement_analysis_id=..., llm_client=mock)` | 成功；`input_payload_json` 含该 id 或解析后的分析内容 |
| S5-05 | 同时传入 `requirement_analysis` 与 `requirement_analysis_id` | `run_proposal_generation_agent` | 抛出 `ValueError`（消息含 *exactly one*）；**不**写入 `agent_runs` |
| S5-06 | 不传入 `requirement_analysis` 与 `requirement_analysis_id` | `run_proposal_generation_agent` | 抛出 `ValueError`；**不**写入 `agent_runs` |
| S5-07 | `requirement_analysis_id` 指向不存在的行 | `run_proposal_generation_agent` | 抛出 `ValueError`（含 not found）；**不**写入 `agent_runs` |

## 测试文件映射

| 文件 | 覆盖 ID |
|------|---------|
| `tests/integration/test_proposal_generation_agent.py` | S5-01、S5-02、S5-03、S5-04、S5-05、S5-06、S5-07 |
| `tests/unit/cli/test_preview_proposal_generation.py` | CLI：`--mock-llm` 成功、缺文件、无 API key |

## 主要入口与类型

- `nomadnomad.agents.proposal_generation_agent.run_proposal_generation_agent`
- `nomadnomad.agents.proposal_generation_agent.PROPOSAL_GENERATION_AGENT_TYPE`

## 手动预览（CLI）

| 命令 | 说明 |
|------|------|
| `poetry run preview-proposal-generation` | 默认 demo HTML，真实 LLM（需 `NOMADNOMAD_LLM_API_KEY`）；串联 Story 4 → Story 5 |
| `poetry run preview-proposal-generation --mock-llm` | 离线：两次结构化输出均由快照推导 JSON 模拟，不发起 HTTP |

与 Story 4 的 `preview-requirement-analysis` 相比，本命令覆盖 **分析 + 提案** 的端到端；单独验证需求分析 Agent 仍可用后者。
