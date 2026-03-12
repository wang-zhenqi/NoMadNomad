# NoMadNomad

AI 驱动的自由职业者全流程项目管理工具：从 Upwork 投标到项目交付的自动化与 AI 辅助工作流。

## 技术栈

- **后端**: FastAPI 0.104+
- **前端**: Streamlit 1.29+
- **AI**: LangChain + LangGraph
- **数据**: SQLite 3.45+（可选 sqlite-vec）

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

### 5. 运行测试

```bash
poetry run pytest
```

## 项目结构

```
NoMadNomad/
├── src/nomadnomad/     # 后端核心包
│   ├── api/            # API 路由层
│   ├── services/       # 业务逻辑层
│   ├── agents/         # LangGraph Agent 编排与实现
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

更多说明见 [docs/project_introduction.md](docs/project_introduction.md)。
