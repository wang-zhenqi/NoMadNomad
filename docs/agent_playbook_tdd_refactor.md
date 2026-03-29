# AI 结对执行手册：Story → GWT → TDD → 重构

供人类与 Cursor Agent 共用。与 **`.cursor/rules/nomadnomad-pairing.mdc`** 配套；规则文件保持简短，**细节以本文为准**。

---

## 1. 读 Story（输入）

- 打开 **`docs/iteration_plan.md`**，定位当前 **Story 编号**与：
  - 用户故事（作为/我希望/以便）
  - **验收标准**（checkbox）
  - 技术任务、依赖故事
- 若存在 **`docs/bdd/story_XX_*.md`**，一并阅读，作为 GWT 权威来源之一。

**产出（口头或回复中列出）**：本 Story 的 **P0 验收项** 与 **明确不在范围内** 的事项。

---

## 2. 规划测试（GWT / 测试点）

在写任何实现代码前：

1. 用 **Given / When / Then** 列出测试场景：
   - 至少 **1 条主路径（happy path）**
   - **2+ 条失败/边界路径**（非法输入、缺字段、外部依赖失败等）
2. 标明建议的 **测试文件路径**（如 `tests/unit/...`、`tests/integration/...`）。
3. 与 **golden fixture**（如 `resources/demo/...`）对齐时，写清 **fixture 名称与断言字段**。
4. **将 GWT 写入仓库**：在 `docs/bdd/` 下**新建或更新** `story_<NN>_<topic>_gwt.md`（Markdown 表格 + 与 `tests/` 的映射说明）；与 **`.cursor/rules/nomadnomad-pairing.mdc`** 第 2 步一致。纯文档勘误、与用户约定「跳过 GWT 文档」时可省略。

**产出**：编号列表（如 S2-01…），便于映射到 `test_*` 函数名；且 **bdd 文档与迭代计划 Story 编号一致**。

---

## 3. TDD — Red

- 只新增或修改 **测试**，使 **`poetry run pytest` 出现预期失败**（断言失败或未实现导入错误均可，但失败应**可读**）。
- 优先写 **最小失败用例**，避免一次写 20 个空壳。

---

## 4. TDD — Green

- 写 **最少** 生产代码使测试通过。
- 不顺便做「大重构」或跨 Story 功能。
- 完成后 **`poetry run pytest`** 全绿。

---

## 5. TDD — Refactor（《重构》导向）

在测试全绿前提下，**小步**进行，每步仍可 `pytest`：

| 坏味道（示例） | 常见手法 |
|----------------|----------|
| 过长函数/文件 | 提炼函数、搬移、按职责拆模块 |
| 重复代码 | 形成函数或小型工具模块（如 `dom_utils`） |
| 过长 if-elif | 表驱动、策略元组、草稿对象 + `to_model()` |
| 职责混乱 | 模型与解析分离（`models/` vs `ingest/`） |
| 命名含糊 | 具名参数、领域词汇（如 `value_cell_text`、`client_section`） |

**禁止**：为「好看」改变对外行为；若需改行为，先补/改测试再改实现。

---

## 6. 质量闸门（收尾）

```bash
poetry run pytest
poetry run mypy src/nomadnomad   # 改了类型或新模块时建议执行
poetry run black src tests
poetry run isort src tests
```

若项目已配置 pre-commit，提交前 **`poetry run pre-commit run --all-files`**（或仅对改动文件）。

---

## 7. 回复模板（Agent 建议）

结束时用简短中文包含：

1. **完成的 Story / 子任务**
2. **新增或修改的测试文件**
3. **主要代码位置**（包/模块）
4. **若做了重构**：坏味道 → 手法 → 行为不变说明

---

## 8. 与本仓库文档的关系

| 文档 | 用途 |
|------|------|
| `docs/iteration_plan.md` | Backlog、DoD、日志与 TDD 约定 |
| `docs/project_introduction.md` | 愿景、范围、技术约束 |
| `docs/bdd/*.md` | 具体 Story 的 GWT 表（如 `story_01_*`、`story_02_*`） |
| `README.md` | 本地命令与结构 |

---

**版本**：与仓库迭代同步；若流程变更，请同时更新 **`.cursor/rules/nomadnomad-pairing.mdc`** 中「文档锚点」或核心顺序描述。
