# NoMadNomad

AI 驱动的自由职业者全流程项目管理工具：从 Upwork 投标到项目交付的自动化与 AI 辅助工作流。

## 技术栈

- **后端**: FastAPI 0.104+
- **前端**: Streamlit 1.29+
- **AI**: LangChain + LangGraph
- **数据**: SQLite 3.45+（可选 sqlite-vec）
- **日志**: loguru（结构化日志 + 关键事件落库）

## 环境要求

- Python 3.11.1
- [asdf](https://asdf-vm.com/)（推荐，用于管理 Python 版本）
- [Poetry](https://python-poetry.org/)（依赖管理）

## 本地开发

### 1. 安装语言与工具版本（asdf）

```bash
asdf plugin add python
asdf install   # 根据 .tool-versions 安装 Python 3.11.1
```

### 2. 安装依赖（Poetry）

```bash
poetry install
```

### 3. 安装 pre-commit（提交前检查）

```bash
poetry run pre-commit install
```

之后每次 `git commit` 会自动运行 black、isort、mypy 等检查。

### 4. 运行服务

```bash
# 启动 FastAPI 后端（默认 http://localhost:8000）
poetry run serve-api

# 另开终端：启动 Streamlit 前端（默认 http://localhost:8501）
poetry run streamlit run streamlit_app/app.py
```

### 4.1 预览 Story 1 + 2 流水线（HTML → 快照 → 契约）

在**仓库根目录**执行（默认读取 `resources/demo/demo_requirement.html`）。若提示找不到命令，先执行一次 `poetry install` 以注册脚本入口。

```bash
poetry run preview-job-html
```

指定其它 Upwork 导出 HTML：

```bash
poetry run preview-job-html --html path/to/job.html
```

### 4.1.1 预览 Story 4（HTML → 快照 → 需求分析 Agent）

在仓库根目录执行。默认读取 `resources/demo/demo_requirement.html`。需已配置 `NOMADNOMAD_LLM_API_KEY`（见 `src/nomadnomad/config/llm_settings.py`）；**离线/CI** 可加 `--mock-llm`，用快照推导的 JSON 模拟 LLM，不发起 HTTP。

```bash
poetry run preview-requirement-analysis
poetry run preview-requirement-analysis --html path/to/job.html
poetry run preview-requirement-analysis --mock-llm
```

### 4.2 初始化 SQLite（Story 3 DDL）

幂等建表；默认写入 `data/nomadnomad.sqlite`（可通过环境变量 `NOMADNOMAD_SQLITE_PATH` 或位置参数覆盖）。

```bash
poetry run init-sqlite-db
poetry run init-sqlite-db /path/to/nomadnomad.sqlite
```

### 5. 运行测试

```bash
poetry run pytest
```

## 开发规范

- **TDD（强制）**: 按 `Red -> Green -> Refactor` 开发，先写失败测试，再写最小实现，最后重构。
- **AI 结对流程**: Cursor 已配置 **`.cursor/rules/nomadnomad-pairing.mdc`**（默认生效）；详细步骤见 **[docs/agent_playbook_tdd_refactor.md](docs/agent_playbook_tdd_refactor.md)**。根目录 **[AGENTS.md](AGENTS.md)** 为入口索引。
- **日志规范**: 统一使用 `loguru` 输出结构化日志（建议 JSON），记录关键上下文（如 `trace_id`、`project_id`、`event_type`）。
- **关键日志落库**: 关键业务事件除控制台/文件外需持久化到 SQLite（建议 `app_events`），用于后续代码分析与运营分析。
- **质量门禁**: 提交前需通过 `pytest` 与 pre-commit（black/isort/mypy）。

## 项目结构

```
NoMadNomad/
├── src/nomadnomad/     # 后端核心包
│   ├── api/            # API 路由层
│   ├── services/       # 业务逻辑层
│   ├── agents/         # LangGraph Agent 编排与实现
│   ├── models/         # 领域数据模型（Pydantic），与解析/API 分离
│   ├── ingest/         # 解析入口；Upwork DOM 抽取见 ingest/upwork/
│   ├── preview/        # 本地演示：快照 → Story 2 示例载荷
│   ├── cli/            # 命令行（preview-job-html、preview-requirement-analysis 等）
│   ├── db/             # 数据访问层
│   └── main.py         # FastAPI 入口
├── streamlit_app/      # Streamlit 前端
├── tests/              # 单元与集成测试
├── docs/               # 项目文档
├── pyproject.toml      # Poetry 与工具配置
├── .tool-versions      # asdf 版本
├── .pre-commit-config.yaml
└── .gitignore
```

更多说明见 [docs/project_introduction.md](docs/project_introduction.md)。迭代计划与 Sprint Backlog 见 [docs/iteration_plan.md](docs/iteration_plan.md)。Story 1（HTML→快照）的 GWT 测试清单见 [docs/bdd/story_01_html_to_snapshot_gwt.md](docs/bdd/story_01_html_to_snapshot_gwt.md)。
