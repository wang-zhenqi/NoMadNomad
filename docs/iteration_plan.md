# NoMadNomad 迭代计划与 Sprint Backlog

**文档类型**：迭代计划 / Sprint Backlog
**状态**：现行
**最后更新**：2026-03-12
**对应立项文档**：[project_introduction.md](project_introduction.md)

---

## 1. 当前仓库现状

| 维度 | 现状 |
|------|------|
| **后端** | FastAPI 已搭好；`/health` 可用；`nomadnomad.api.routes` 仅通用路由；无业务路由与 DB。 |
| **包结构** | `src/nomadnomad/` 下已有 `api/`、`services/`、`agents/`、`db/` 空包，无实现。 |
| **前端** | `streamlit_app/app.py` 存在，为占位或最简页；未与后端业务 API 打通。 |
| **数据** | 无 SQLite 初始化、无表结构、无 aiosqlite 封装。 |
| **Agent** | 未接入 LangGraph/LangChain；无需求分析/提案生成实现。 |
| **测试** | `tests/conftest.py` 提供 `TestClient`；`tests/unit/test_health.py` 覆盖 `/health`；pytest cov-fail-under=80。 |
| **工程** | Poetry、black、isort、mypy(strict)、pre-commit 已配置；无 CI 配置（如 GitHub Actions）。 |

**结论**：本期以「需求分析 → 提案生成」闭环为核心，先立契约与数据层，再实现工作流与 API，最后补最简 UI 与可观测。

---

## 2. 迭代节奏与约定

- **Sprint 长度**：2 周。
- **看板列**：Backlog → Ready → In Progress → Review → Done。
- **WIP**：In Progress 最多 3 项。
- **DoD（Definition of Done）**：满足验收标准、通过相关测试、通过 pre-commit（black/isort/mypy）、已合并或已提交到对应分支。

---

## 3. 本期迭代目标（Sprint 1）

**一句话**：交付「Upwork 文本 → 需求分析（JSON）→ 提案（Markdown）→ 落库与可查」的 MVP 闭环，并具备可回归测试与运行记录。

**本迭代不做**：看板/甘特图、Trello/Jira 导出、Prometheus/Grafana、Upwork 自动抓取、向量检索、语言润色/任务拆解 Agent。

---

## 4. Sprint Backlog（按执行顺序）

### 故事 1：定义分析与提案的契约（Schema + 校验）

- **作为** 开发者
- **我希望** 需求分析输出与提案输出有明确的 Pydantic Schema 与校验逻辑
- **以便** 下游 API 与 Agent 可稳定解析、测试可断言、失败可提示

**验收标准：**

- [ ] `RequirementAnalysis`（或等价）Schema 定义：含技术栈、关键需求、预算/时间线、复杂度/风险等字段；类型与必填/可选明确。
- [ ] `Proposal`（或等价）Schema 定义：含标题、正文（Markdown）、可选变量等；与文档中「提案」概念一致。
- [ ] 提供校验函数或方法：给定 dict/str 可校验并返回结构化对象或清晰错误信息。
- [ ] 至少 1 个单元测试：合法输入通过、非法输入得到预期错误。

**技术任务：**

- [ ] 在 `nomadnomad` 下新增 `schemas/` 或 `models/`，放置 Pydantic 模型（可区分「API 请求/响应」与「领域」）。
- [ ] 实现校验封装（如 `parse_requirement_analysis(raw: str | dict) -> RequirementAnalysis`）。
- [ ] 编写对应单元测试。

**估算**：4–6 h
**优先级**：P0

---

### 故事 2：SQLite 数据层与表结构

- **作为** 开发者
- **我希望** 项目、需求分析、提案、Agent 运行记录持久化到 SQLite
- **以便** 工作流可落库、可查询、可追溯

**验收标准：**

- [ ] 具备 `projects`、`requirement_analyses`、`proposals`、`agent_runs` 四张表（字段与立项/数据设计一致；SQLite 用 `TEXT` 存 JSON 或 BLOB 视选型而定）。
- [ ] 提供初始化脚本或应用启动时执行 DDL，保证本地/CI 可重复建库。
- [ ] 封装 aiosqlite 连接与基础「按 id 查询 / 插入」接口（至少 projects、requirement_analyses、proposals、agent_runs 各一例）。
- [ ] 至少 1 个集成测试：插入后能按 id 查出且字段一致（或等价）。

**技术任务：**

- [ ] 在 `nomadnomad/db/` 下实现 DDL（可单文件或按表拆分）、连接管理（如单例或依赖注入）。
- [ ] 实现 repositories 或类似（ProjectRepo, RequirementAnalysisRepo, ProposalRepo, AgentRunRepo）的薄封装。
- [ ] 测试用内存 SQLite 或临时文件，保证无副作用。

**估算**：6–8 h
**优先级**：P0

---

### 故事 3：需求分析 Agent（单节点）

- **作为** 用户
- **我希望** 输入一段 Upwork 任务描述后，系统能产出结构化的需求分析结果
- **以便** 后续提案生成与人工编辑有据可依

**验收标准：**

- [ ] 实现「需求分析」单节点：输入为原始文本，输出为符合 Schema 的 `RequirementAnalysis`（或等价）。
- [ ] 调用 LLM 时使用结构化输出（如 JSON mode 或强约束 Prompt），失败时能捕获并记录，可重试或返回明确错误。
- [ ] 每次调用写入 `agent_runs`（agent_type、project_id、input/output、success、duration_ms、error_message 等）。
- [ ] 至少 1 个集成/单元测试：mock LLM 返回固定 JSON，验证解析与 Schema 一致；或使用确定性 fixture。

**技术任务：**

- [ ] 在 `nomadnomad/agents/` 下实现需求分析 Agent（可 LangChain + LLM，或直接 httpx 调 API）。
- [ ] 与 `nomadnomad/db` 的 AgentRunRepo 集成，记录每次运行。
- [ ] 配置通过环境变量或 settings（如 API key、model name），不写死密钥。

**估算**：8–12 h
**优先级**：P0

---

### 故事 4：提案生成 Agent（单节点）

- **作为** 用户
- **我希望** 在已有需求分析结果的基础上，系统能生成一份提案草稿（Markdown）
- **以便** 我只需少量编辑即可投递

**验收标准：**

- [ ] 实现「提案生成」单节点：输入为 `RequirementAnalysis`（或 id 查库），输出为符合 `Proposal` Schema 的 Markdown 内容。
- [ ] 调用 LLM 时约束输出格式（如仅返回 Markdown 段落），并做基本校验（非空、长度合理）。
- [ ] 每次调用写入 `agent_runs`。
- [ ] 至少 1 个集成/单元测试：mock LLM 返回固定 Markdown，验证解析与写入一致。

**技术任务：**

- [ ] 在 `nomadnomad/agents/` 下实现提案生成 Agent；与 AgentRunRepo 集成。
- [ ] 与故事 1 的 Schema 对齐（Proposal 的字段与存储一致）。

**估算**：6–10 h
**优先级**：P0

---

### 故事 5：LangGraph 编排「分析 → 提案」并落库

- **作为** 开发者
- **我希望** 用 LangGraph 编排「需求分析 → 提案生成」两节点，且中间与最终结果写入 DB
- **以便** 一次请求即可完成从原文到提案草稿的流水线

**验收标准：**

- [ ] LangGraph 图：节点 1 为需求分析，节点 2 为提案生成；边为「分析成功 → 提案」；失败可终止并记录。
- [ ] 输入：项目 id 或原始描述；若仅有描述则先创建 project 与 requirement_analysis，再生成 proposal 并写入 proposals 表。
- [ ] 输出：返回 project_id、requirement_analysis_id、proposal_id（或最新 proposal 版本）及简要状态。
- [ ] 至少 1 个集成测试：从粘贴文本到生成提案并查库，mock LLM 或使用测试用 key。

**技术任务：**

- [ ] 在 `nomadnomad/agents/` 或 `nomadnomad/services/` 下实现 graph 构建与 invoke；与 db 的 repo 在关键节点交互。
- [ ] 确保 agent_runs 中能区分 requirement_analyzer 与 proposal_generator 两次调用。

**估算**：8–10 h
**优先级**：P0

---

### 故事 6：业务 API（项目创建、分析、提案生成、查询）

- **作为** 前端或调用方
- **我希望** 通过 REST API 创建项目、触发分析、触发提案生成、查询项目/分析/提案
- **以便** Streamlit 或其它客户端能完成闭环

**验收标准：**

- [ ] `POST /projects`：创建项目（必填如 title、original_description；返回 id 等）。
- [ ] `POST /projects/{id}/analyze`：对已存在项目执行需求分析并落库；返回分析 id 或最新分析摘要。
- [ ] `POST /projects/{id}/proposals`：基于最新需求分析生成提案并落库；返回 proposal id 或版本。
- [ ] `GET /projects/{id}`：返回项目详情（可含最新分析、最新提案摘要）。
- [ ] `GET /projects/{id}/proposals/{proposal_id}`（或 `/proposals/{id}`）：返回单份提案内容（如 Markdown）。
- [ ] 上述接口在失败时返回合理 HTTP 状态码与错误信息；与 Schema 校验错误区分。

**技术任务：**

- [ ] 在 `nomadnomad/api/` 下新增路由模块（如 `projects.py`、`proposals.py`），注入依赖（db、graph 或 service）。
- [ ] 在 `main.py` 或路由入口中 include_router；保持 `/health` 不变。
- [ ] 为上述端点编写至少 1 个集成测试（如创建项目 → 分析 → 生成提案 → 查询）。

**估算**：6–8 h
**优先级**：P0

---

### 故事 7：最简 Streamlit 闭环页面

- **作为** 用户
- **我希望** 在浏览器中粘贴 Upwork 描述、点击「分析」再「生成提案」，并能看到结果与编辑/保存入口
- **以便** 不依赖 curl/Postman 也能跑通 MVP

**验收标准：**

- [ ] 一页内：文本输入区、「创建项目并分析」或「分析」按钮、「生成提案」按钮、分析结果展示区、提案 Markdown 展示区。
- [ ] 调用后端 `POST /projects`、`POST /projects/{id}/analyze`、`POST /projects/{id}/proposals` 与查询接口；后端 URL 可配置（如环境变量）。
- [ ] 保存：至少能将当前提案内容提交到后端更新（若后端提供 PATCH/PUT 提案接口）；或本迭代仅「展示 + 复制」，保存放到下一迭代。

**技术任务：**

- [ ] 在 `streamlit_app/app.py` 中实现上述流程；使用 httpx 或 requests 调后端。
- [ ] 错误提示（如分析失败、提案生成失败）在页面上可见。

**估算**：4–6 h
**优先级**：P0

---

### 故事 8：可观测与回归基线

- **作为** 开发者/运维
- **我希望** Agent 调用有运行记录、关键路径有自动化测试、CI 能跑测试
- **以便** 后续迭代可回归、问题可排查

**验收标准：**

- [ ] 每次需求分析与提案生成均写入 `agent_runs`（已在故事 3/4/5 中覆盖；本故事可补充「耗时、token 数」等若易获取）。
- [ ] 存在一条「从创建项目到生成提案」的集成测试（真实或 mock LLM），并在 CI 中执行。
- [ ] 若使用 GitHub Actions：push/PR 时运行 pytest；可选 black/isort/mypy。

**技术任务：**

- [ ] 补充集成测试（如 `tests/integration/test_workflow.py`），覆盖「创建项目 → 分析 → 提案」至少一条路径。
- [ ] 添加 `.github/workflows/ci.yml`（或等价），运行 `poetry install` 与 `poetry run pytest`。

**估算**：4–6 h
**优先级**：P0

---

## 5. 本迭代 Backlog 汇总

| 故事 ID | 简述 | 估算(h) | 优先级 |
|--------|------|---------|--------|
| 1 | Schema + 校验（需求分析、提案） | 4–6 | P0 |
| 2 | SQLite 数据层与表结构 | 6–8 | P0 |
| 3 | 需求分析 Agent（单节点） | 8–12 | P0 |
| 4 | 提案生成 Agent（单节点） | 6–10 | P0 |
| 5 | LangGraph 编排分析→提案并落库 | 8–10 | P0 |
| 6 | 业务 API（项目/分析/提案 CRUD 与触发） | 6–8 | P0 |
| 7 | 最简 Streamlit 闭环页 | 4–6 | P0 |
| 8 | 可观测与回归基线（agent_runs + 集成测试 + CI） | 4–6 | P0 |

**总估算**：约 46–66 h（按 2 周 Sprint，约 20–33 h/周 可排期；可根据实际产能裁剪或拆分为多 Sprint）。

---

## 6. 依赖关系与建议顺序

1. **故事 1** 无依赖，优先做。
2. **故事 2** 依赖 1（Schema 决定部分表字段）；可与 1 并行准备 DDL。
3. **故事 3、4** 依赖 1、2（需要 Schema 与 DB 写 agent_runs）。
4. **故事 5** 依赖 3、4、2。
5. **故事 6** 依赖 5、2。
6. **故事 7** 依赖 6。
7. **故事 8** 可与 5、6 并行，建议在 6 之后收尾（集成测试覆盖完整 API）。

---

## 7. 后续迭代（Sprint 2+）预览

- 提案版本历史、编辑与保存的完整 API。
- 语言润色 Agent（P1）。
- 任务拆解 Agent（P1）。
- 项目管理看板（Backlog/Ready/In Progress/Done）与基础 UI（P2）。
- 监控与告警（基础指标端点、可选 Prometheus）。

---

**文档状态**：现行
**下一步**：按 Backlog 顺序将故事拆分为具体任务，放入看板并开始 Sprint 1。
