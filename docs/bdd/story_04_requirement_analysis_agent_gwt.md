# Story 4：需求分析 Agent（单节点）— GWT 测试点

与 [`docs/iteration_plan.md`](../iteration_plan.md) 中「故事 4」验收对齐；实现映射见下「测试文件映射」。

## 范围说明

- **输入**：`JobPostingSnapshot` **或** 规范化文本（`normalized_job_text`），二者**互斥**；同时提供或皆不提供时失败。
- **输出**：`RequirementAnalysis`（经 `parse_requirement_analysis` 校验）；每次运行写入 `agent_runs`（含 `agent_type=requirement_analyzer`、input/output JSON、`success`、`duration_ms`、`error_message`、`trace_id`）。
- **LLM**：结构化 JSON（系统 Prompt + `JsonCompletionClient`）；真实 HTTP 见 `OpenAiCompatibleJsonChatClient` + `LlmSettings`（`NOMADNOMAD_LLM_*`）。
- **重试**：仅当**解析** `RequirementAnalysis` 失败时，对同一用户输入再请求一次 LLM（附加修复提示）；HTTP 等异常不重试。

## GWT 表

| ID | Given | When | Then |
|----|-------|------|------|
| S4-01 | 内存库已 `init_schema`；已插入 `project`；mock LLM 返回合法 `RequirementAnalysis` JSON | `run_requirement_analysis_agent(..., snapshot=..., llm_client=mock)` | 返回 `analysis` 非空；`agent_runs` 行 `success=1`；`input_payload_json` 含快照线索；`output_payload_json` 与 `analysis.model_dump()` 一致；`trace_id`、`duration_ms` 有值 |
| S4-02 | 同上库与 project；mock **两次**返回 Schema 非法（如 `technology_stack` 类型错误） | `run_requirement_analysis_agent(..., normalized_job_text=..., llm_client=mock)` | `analysis` 为空；`error_message` 非空；`agent_runs` 行 `success=0` |
| S4-03 | mock 首次返回非 JSON 字符串、第二次返回合法 JSON | `run_requirement_analysis_agent(..., snapshot=...)` | 最终成功；LLM 被调用 **2** 次；`agent_runs` 成功 |
| S4-04 | `LlmSettings` 含 `llm_api_key`；httpx 返回 HTTP 200 且 `choices[0].message.content` 为 JSON 字符串 | `OpenAiCompatibleJsonChatClient.complete_json` | 返回内容与 `message.content` 一致；请求指向 `.../chat/completions` |
| S4-05 | 同时传入 `snapshot` 与 `normalized_job_text` | `run_requirement_analysis_agent` | 抛出 `ValueError`（消息含 *exactly one*）；**不**写入 `agent_runs` |
| S4-06 | `LlmSettings(llm_api_key=None)` | `OpenAiCompatibleJsonChatClient.complete_json` | 抛出 `RuntimeError`，消息提示 `NOMADNOMAD_LLM_API_KEY` |

## 测试文件映射

| 文件 | 覆盖 ID |
|------|---------|
| `tests/integration/test_requirement_analysis_agent.py` | S4-01、S4-02、S4-03、S4-05 |
| `tests/unit/agents/test_openai_json_chat_client.py` | S4-04、S4-06 |
| `tests/unit/cli/test_preview_requirement_analysis.py` | CLI：mock 成功、缺文件、无 API key |

## 手动预览（CLI）

| 命令 | 说明 |
|------|------|
| `poetry run preview-requirement-analysis` | 默认 demo HTML，真实 LLM（需 `NOMADNOMAD_LLM_API_KEY`） |
| `poetry run preview-requirement-analysis --mock-llm` | 离线：模拟 LLM，不请求网络 |
| `poetry run preview-proposal-generation [--mock-llm]` | 在 Story 5 完成后：串联「分析 → 提案」端到端（见 Story 5 GWT） |

## 主要入口与类型

- `nomadnomad.agents.requirement_analysis_agent.run_requirement_analysis_agent`
- `nomadnomad.agents.llm.json_chat_client.OpenAiCompatibleJsonChatClient`
- `nomadnomad.config.llm_settings.LlmSettings`
