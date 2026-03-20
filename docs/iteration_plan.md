# NoMadNomad 迭代计划与 Sprint Backlog

**文档类型**：迭代计划 / Sprint Backlog
**状态**：现行
**最后更新**：2026-03-20（Story 2：需求分析 / 提案 Schema + `schemas` 校验入口）
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

**结论**：本期以「**HTML → 职位快照** → 需求分析 → 提案生成」闭环为核心；先从不依赖 LLM 的结构化抽取做起，再立契约与数据层，再实现 Agent、API 与最简 UI。

---

## 2. 迭代节奏与约定

- **Sprint 长度**：2 周。
- **看板列**：Backlog → Ready → In Progress → Review → Done。
- **WIP**：In Progress 最多 3 项。
- **DoD（Definition of Done）**：满足验收标准、通过相关测试、通过 pre-commit（black/isort/mypy）、已合并或已提交到对应分支。
- **开发方法**：严格 TDD（Red -> Green -> Refactor）。每个故事先写失败测试，再写最小实现，最后重构并保持测试通过。
- **日志规范**：统一使用 `loguru` 输出结构化日志（JSON）；关键业务日志除文件/控制台外需落 SQLite，用于后续代码分析、运营分析与排障复盘。

---

## 3. 本期迭代目标（Sprint 1）

**一句话**：交付「Upwork 职位 HTML → **结构化快照** → 需求分析（JSON）→ 提案（Markdown）→ 落库与可查」的 MVP 闭环，并具备可回归测试与运行记录。

**本迭代不做**：看板/甘特图、Trello/Jira 导出、Prometheus/Grafana、Upwork 自动抓取、向量检索、语言润色/任务拆解 Agent。

---

## 4. Sprint Backlog（按执行顺序）

### 故事 1：HTML → 职位快照（Upwork 详情卡片解析）

- **作为** 开发者
- **我希望** 将用户从 Upwork 复制的职位详情 HTML 解析为稳定的结构化快照（Pydantic）
- **以便** 下游需求分析、雇主画像与提案生成使用统一输入，并可对解析结果做回归测试（不依赖 LLM）

**验收标准：**

- [ ] 定义 `JobPostingSnapshot`（或等价命名）Pydantic 模型：覆盖当前 MVP 所需字段（见下方「快照字段建议」），缺失平台字段时用 `None` 或空集合并文档说明。
- [ ] 提供 `parse_upwork_job_html(html: str) -> JobPostingSnapshot`（或等价 API）：输入为 UTF-8 字符串；输出通过模型校验。
- [ ] 使用仓库内 **golden fixture**：`resources/demo/demo_requirement.html` 的解析结果与人工基线断言一致（标题、Summary、技能、预算区间、投标问题、About the client 关键信息等）。
- [ ] 非法输入可预期失败：空字符串、非 HTML、或缺少关键节点时返回明确异常或 `ParseError`（类型与消息稳定，便于测试）。
- [ ] TDD：先写失败测试再实现；至少包含 golden + 1 条负面用例。

**快照字段建议（可按实现迭代增减，但变更需更新测试与文档）：**

- **meta**：`source_type`（如 `upwork_job_card`）、可选 `parser_version`
- **identifiers**：`job_uid`（来自 `job-uid` 属性，若存在）
- **listing**：`title`、`posted_text`、`client_location_text`（如 Worldwide）、`summary_text`
- **engagement**：`hours_per_week_text`、`duration_text`、`experience_level_text`、`budget`（如 `min_usd`/`max_usd`/`basis` hourly）、`project_type_text`
- **connects**：`connects_required`、`connects_available`（能解析则填，否则 `None`）
- **screening_questions**：`list[str]`（提案必答问题）
- **skills**：`mandatory_skills: list[str]`（及预留 `preferred` 空列表）
- **activity**：`proposals_text`、`last_viewed_by_client_text`、`interviewing_count`、`invites_sent` 等（能解析则结构化，否则保留原文片段）
- **client**：`payment_verified`、`rating_value`、`reviews_text`、`country`、`city`、`jobs_posted_text`、`hire_stats_text`、`total_spent_text`、`avg_hourly_rate_paid_text`、`industry`、`company_size_text`、`member_since_text`

**技术任务：**

- [ ] 新增依赖：HTML 解析（推荐 `beautifulsoup4` + `lxml` 或 `html.parser`，在 `pyproject.toml` 中锁定）。
- [ ] 实现模块建议：领域模型放 `nomadnomad/models/`；解析入口 `nomadnomad/ingest/upwork_job_html_parser.py`；DOM 抽取按页面区块拆在 `nomadnomad/ingest/upwork/` 子包内。
- [ ] 选择器/CSS 路径与 Upwork 前端变更风险：在代码与文档中注明「基于当前 DOM 约定」；测试用 golden 文件锁定行为。
- [ ] 可选：`loguru` 记录 `html_parse_started` / `html_parse_completed` / `html_parse_failed`（完整落库可在故事 9 接上 `app_events`）。

**GWT 测试点规划（行为验收，实现时映射为 pytest 用例名）**

| ID | Given | When | Then |
|----|-------|------|------|
| S1-01 | 内容为 `resources/demo/demo_requirement.html` 的完整字符串 | 调用 `parse_upwork_job_html` | 返回 `JobPostingSnapshot`；`title` 为「Automated Image Solving (LLM or Human-in-the-loop)」 |
| S1-02 | 同上 | 调用解析 | `job_uid == "2034153922546495276"`（字符串，与 HTML 属性一致） |
| S1-03 | 同上 | 调用解析 | `summary_text` 包含「Python-based system」与「within 5s」等关键句（或完整 Summary 段落与 golden 归一化后一致） |
| S1-04 | 同上 | 调用解析 | `mandatory_skills` 包含 `Automation` 与 `Python`（顺序可固定或集合相等） |
| S1-05 | 同上 | 调用解析 | `screening_questions` 长度为 2，且每条与 HTML 中投标问题原文一致（空白归一化后） |
| S1-06 | 同上 | 调用解析 | `budget` 体现 $10–$40 hourly（具体字段以 Schema 为准，如 `min_usd=10`, `max_usd=40`, `basis=hourly`） |
| S1-07 | 同上 | 调用解析 | `engagement` 含 Less than 30 hrs/week、1–3 months、Intermediate 等原文或规范化枚举 |
| S1-08 | 同上 | 调用解析 | `client.payment_verified is True`；`rating_value` 与页面一致（如 5.0）；`country` 含 United States |
| S1-09 | 同上 | 调用解析 | `activity` 中 proposals 为「50+」或结构化等价；`interviewing_count == 8`（若字段存在） |
| S1-10 | 空字符串 | 调用解析 | 抛出约定异常或返回 `ParseError`，消息明确（如 empty input） |
| S1-11 | 非 HTML 纯文本且无结构 | 调用解析 | 失败可预期；不抛出裸 `AttributeError`（应封装为解析错误） |
| S1-12 | 合法 HTML 但缺少职位标题节点 | 调用解析 | 失败或 `title is None` 的策略在文档与测试中二选一并固定 |
| S1-13 | 两次解析同一 HTML | 连续调用 | 输出相等或可序列化 JSON 一致（确定性，无当前时间污染快照） |

**估算**：6–10 h（视 DOM 健壮性与字段完整度而定）
**优先级**：P0

---

### 故事 2：定义分析与提案的契约（Schema + 校验）

- **作为** 开发者
- **我希望** 需求分析输出与提案输出有明确的 Pydantic Schema 与校验逻辑
- **以便** 下游 API 与 Agent 可稳定解析、测试可断言、失败可提示

**验收标准：**

- [x] `RequirementAnalysis`（或等价）Schema 定义：含技术栈、关键需求、预算/时间线、复杂度/风险等字段；类型与必填/可选明确；**可选**与 `JobPostingSnapshot` 的关联字段（如 `source_job_uid`）。
- [x] `Proposal`（或等价）Schema 定义：含标题、正文（Markdown）、可选变量等；与文档中「提案」概念一致。
- [x] 提供校验函数或方法：给定 dict/str 可校验并返回结构化对象或清晰错误信息。
- [x] 至少 1 个单元测试：合法输入通过、非法输入得到预期错误。

**技术任务：**

- [x] 在 `nomadnomad` 下新增 `schemas/` 或 `models/`，放置 Pydantic 模型（可区分「API 请求/响应」与「领域」）。
- [x] 实现校验封装（如 `parse_requirement_analysis(raw: str | dict) -> RequirementAnalysis`）。
- [x] 编写对应单元测试。

**估算**：4–6 h
**优先级**：P0

---

### 故事 3：SQLite 数据层与表结构

- **作为** 开发者
- **我希望** 项目、需求分析、提案、Agent 运行记录持久化到 SQLite
- **以便** 工作流可落库、可查询、可追溯

**验收标准：**

- [ ] 具备 `projects`、`requirement_analyses`、`proposals`、`agent_runs` 四张表（字段与立项/数据设计一致；SQLite 用 `TEXT` 存 JSON 或 BLOB 视选型而定）。
- [ ] 新增关键日志表（建议 `app_events`）：记录结构化日志关键字段（如 `event_type`、`level`、`trace_id`、`project_id`、`source`、`payload_json`、`created_at`）。
- [ ] 提供初始化脚本或应用启动时执行 DDL，保证本地/CI 可重复建库。
- [ ] 封装 aiosqlite 连接与基础「按 id 查询 / 插入」接口（至少 projects、requirement_analyses、proposals、agent_runs 各一例）。
- [ ] 至少 1 个集成测试：插入后能按 id 查出且字段一致（或等价）。

**技术任务：**

- [ ] 在 `nomadnomad/db/` 下实现 DDL（可单文件或按表拆分）、连接管理（如单例或依赖注入）。
- [ ] 实现 repositories 或类似（ProjectRepo, RequirementAnalysisRepo, ProposalRepo, AgentRunRepo）的薄封装。
- [ ] 增加 `AppEventRepo`（或等价）用于关键日志落库。
- [ ] 测试用内存 SQLite 或临时文件，保证无副作用。

**估算**：6–8 h
**优先级**：P0

---

### 故事 4：需求分析 Agent（单节点）

- **作为** 用户
- **我希望** 输入一段 Upwork 任务描述后，系统能产出结构化的需求分析结果
- **以便** 后续提案生成与人工编辑有据可依

**验收标准：**

- [ ] 实现「需求分析」单节点：输入为 **`JobPostingSnapshot` 或由其拼接的规范化文本**，输出为符合 Schema 的 `RequirementAnalysis`（或等价）。
- [ ] 调用 LLM 时使用结构化输出（如 JSON mode 或强约束 Prompt），失败时能捕获并记录，可重试或返回明确错误。
- [ ] 每次调用写入 `agent_runs`（agent_type、project_id、input/output、success、duration_ms、error_message 等）。
- [ ] 至少 1 个集成/单元测试：mock LLM 返回固定 JSON，验证解析与 Schema 一致；或使用确定性 fixture。

**技术任务：**

- [ ] 在 `nomadnomad/agents/` 下实现需求分析 Agent（可 LangChain + LLM，或直接 httpx 调 API）。
- [ ] 与 `nomadnomad/db` 的 AgentRunRepo 集成，记录每次运行（依赖故事 3）。
- [ ] 配置通过环境变量或 settings（如 API key、model name），不写死密钥。

**估算**：8–12 h
**优先级**：P0

---

### 故事 5：提案生成 Agent（单节点）

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
- [ ] 与故事 2 的 Schema 对齐（Proposal 的字段与存储一致）。

**估算**：6–10 h
**优先级**：P0

---

### 故事 6：LangGraph 编排「分析 → 提案」并落库

- **作为** 开发者
- **我希望** 用 LangGraph 编排「需求分析 → 提案生成」两节点，且中间与最终结果写入 DB
- **以便** 一次请求即可完成从原文到提案草稿的流水线

**验收标准：**

- [ ] LangGraph 图：节点 1 为需求分析，节点 2 为提案生成；边为「分析成功 → 提案」；失败可终止并记录。
- [ ] 输入：项目 id、**职位 HTML**、或已解析的 `JobPostingSnapshot`；若仅有 HTML 则先经故事 1 解析为快照，再创建 project 与 requirement_analysis，再生成 proposal 并写入 proposals 表。
- [ ] 输出：返回 project_id、requirement_analysis_id、proposal_id（或最新 proposal 版本）及简要状态。
- [ ] 至少 1 个集成测试：从粘贴 **HTML 或快照** 到生成提案并查库，mock LLM 或使用测试用 key。

**技术任务：**

- [ ] 在 `nomadnomad/agents/` 或 `nomadnomad/services/` 下实现 graph 构建与 invoke；与 db 的 repo 在关键节点交互。
- [ ] 确保 agent_runs 中能区分 requirement_analyzer 与 proposal_generator 两次调用。

**估算**：8–10 h
**优先级**：P0

---

### 故事 7：业务 API（项目创建、分析、提案生成、查询）

- **作为** 前端或调用方
- **我希望** 通过 REST API 创建项目、触发分析、触发提案生成、查询项目/分析/提案
- **以便** Streamlit 或其它客户端能完成闭环

**验收标准：**

- [ ] `POST /projects`：创建项目（必填如 **原始 HTML** 或 `listing_html` + 可选已解析字段；或 `title` + `original_description`；返回 id 等）；服务端可对 HTML 调用故事 1 生成快照并持久化。
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

### 故事 8：最简 Streamlit 闭环页面

- **作为** 用户
- **我希望** 在浏览器中粘贴 Upwork **职位 HTML（或描述）**、点击「分析」再「生成提案」，并能看到结果与编辑/保存入口
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

### 故事 9：可观测与回归基线

- **作为** 开发者/运维
- **我希望** Agent 调用有运行记录、关键路径有自动化测试、CI 能跑测试
- **以便** 后续迭代可回归、问题可排查

**验收标准：**

- [ ] 每次需求分析与提案生成均写入 `agent_runs`（已在故事 4/5/6 中覆盖；本故事可补充「耗时、token 数」等若易获取）。
- [ ] 统一使用 `loguru`，生产与开发环境均输出结构化日志（JSON），至少覆盖 API 请求、Agent 调用、数据库写入、异常。
- [ ] 关键日志落 SQLite（`app_events` 或等价），且支持按 `project_id`、`trace_id`、`event_type` 查询。
- [ ] 存在一条「从创建项目到生成提案」的集成测试（真实或 mock LLM），并在 CI 中执行。
- [ ] 若使用 GitHub Actions：push/PR 时运行 pytest；可选 black/isort/mypy。

**技术任务：**

- [ ] 补充集成测试（如 `tests/integration/test_workflow.py`），覆盖「**HTML/快照** → 创建项目 → 分析 → 提案」至少一条路径。
- [ ] 新增日志基础设施（如 `nomadnomad/observability/logging.py`）：初始化 `loguru`、绑定上下文字段（`trace_id` / `project_id` / `agent_type`）。
- [ ] 定义关键事件字典（如 `project_created`、`analysis_started`、`analysis_completed`、`proposal_generated`、`agent_failed`），并在服务层统一埋点。
- [ ] 添加 `.github/workflows/ci.yml`（或等价），运行 `poetry install` 与 `poetry run pytest`。

**估算**：4–6 h
**优先级**：P0

---

## 5. 本迭代 Backlog 汇总

| 故事 ID | 简述 | 估算(h) | 优先级 |
|--------|------|---------|--------|
| 1 | HTML → 职位快照（Upwork 卡片解析 + `JobPostingSnapshot`） | 6–10 | P0 |
| 2 | Schema + 校验（需求分析、提案） | 4–6 | P0 |
| 3 | SQLite 数据层与表结构 | 6–8 | P0 |
| 4 | 需求分析 Agent（单节点） | 8–12 | P0 |
| 5 | 提案生成 Agent（单节点） | 6–10 | P0 |
| 6 | LangGraph 编排分析→提案并落库 | 8–10 | P0 |
| 7 | 业务 API（项目/分析/提案 CRUD 与触发） | 6–8 | P0 |
| 8 | 最简 Streamlit 闭环页 | 4–6 | P0 |
| 9 | 可观测与回归基线（agent_runs + 集成测试 + CI） | 4–6 | P0 |

**总估算**：约 52–76 h（按 2 周 Sprint，约 26–38 h/周 可排期；可根据实际产能裁剪或拆分为多 Sprint）。

---

## 6. 依赖关系与建议顺序

1. **故事 1**（HTML → 快照）无外部故事依赖，**Sprint 首选**。
2. **故事 2**（Schema）可与 1 并行；若 `RequirementAnalysis` 需嵌入快照引用，建议在 1 的 `JobPostingSnapshot` 稳定后再冻结字段。
3. **故事 3**（SQLite）依赖 2（领域 Schema）；**projects 等表建议预留 `listing_snapshot_json`（或等价）** 以持久化故事 1 输出。
4. **故事 4、5** 依赖 1、2、3（输入快照 + 校验 + `agent_runs` 落库）。
5. **故事 6** 依赖 4、5、3。
6. **故事 7** 依赖 6、3（API + DB）。
7. **故事 8** 依赖 7。
8. **故事 9** 可与 6、7 并行；建议在 7 之后收尾（集成测试覆盖完整 API 与 HTML 入口）。

---

## 7. 后续迭代（Sprint 2+）预览

- 提案版本历史、编辑与保存的完整 API。
- 语言润色 Agent（P1）。
- 任务拆解 Agent（P1）。
- 项目管理看板（Backlog/Ready/In Progress/Done）与基础 UI（P2）。
- 监控与告警（基础指标端点、可选 Prometheus）。

---

**文档状态**：现行
**下一步**：按 TDD 方式将 Backlog 顺序拆成「测试任务 -> 实现任务 -> 重构任务」，放入看板并开始 Sprint 1。
