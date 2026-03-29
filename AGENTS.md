# Agent / AI 协作说明（NoMadNomad）

本仓库使用 **Cursor Project Rules** 固化结对流程：

- **规则文件**：`.cursor/rules/nomadnomad-pairing.mdc`（`alwaysApply: true`）
- **详细步骤与清单**：[`docs/agent_playbook_tdd_refactor.md`](docs/agent_playbook_tdd_refactor.md)
- **Backlog 与验收**：[`docs/iteration_plan.md`](docs/iteration_plan.md)

实现功能时默认：**读 Story → GWT 测试规划 → Red → Green → Refactor（Fowler）→ pytest 全绿**。Story 收尾时若扩展了端到端可验路径，按 playbook **§7** 评估是否更新/新增 `README` 与 `poetry run preview-*` 等 CLI。用户说「跳过 TDD」等指令时可偏离默认流程。
