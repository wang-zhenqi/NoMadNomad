# Story 1：HTML → 职位快照 — GWT 测试点清单

**对应迭代文档**：[iteration_plan.md](../iteration_plan.md) 中「故事 1」验收标准与 Backlog。

**建议测试文件**：`tests/unit/ingest/test_upwork_job_html_to_snapshot.py`（或 `tests/unit/parsers/...`，与实现包路径一致即可）

**Fixture**：`resources/demo/demo_requirement.html`（golden）

---

## 行为场景（Given / When / Then）


| ID    | Given                                             | When                       | Then                                                                                  |
| ----- | ------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------- |
| S1-01 | 内容为 `resources/demo/demo_requirement.html` 的完整字符串 | 调用 `parse_upwork_job_html` | 返回 `JobPostingSnapshot`；`title` 为「Automated Image Solving (LLM or Human-in-the-loop)」 |
| S1-02 | 同上                                                | 调用解析                       | `job_uid == "2034153922546495276"`                                                    |
| S1-03 | 同上                                                | 调用解析                       | `summary_text` 包含「Python-based system」与「within 5s」（或与归一化后的 golden 全文一致）               |
| S1-04 | 同上                                                | 调用解析                       | `mandatory_skills` 包含 `Automation` 与 `Python`                                         |
| S1-05 | 同上                                                | 调用解析                       | `screening_questions` 长度为 2，且与页面问题原文一致（空白归一化后）                                        |
| S1-06 | 同上                                                | 调用解析                       | `budget` 体现 $10–$40 hourly（如 `min_usd=10`, `max_usd=40`, `basis=hourly`）              |
| S1-07 | 同上                                                | 调用解析                       | engagement 相关字段含 Less than 30 hrs/week、1–3 months、Intermediate（原文或枚举）                 |
| S1-08 | 同上                                                | 调用解析                       | `client.payment_verified is True`；`rating_value` 为 5.0；`country` 含 United States      |
| S1-09 | 同上                                                | 调用解析                       | activity 中 proposals 为「50+」或等价；`interviewing_count == 8`（若建模）                         |
| S1-10 | 空字符串                                              | 调用解析                       | 约定错误或 `ParseError`，消息明确                                                               |
| S1-11 | 无结构纯文本                                            | 调用解析                       | 封装为解析失败，不暴露裸 `AttributeError`                                                         |
| S1-12 | 合法 HTML 但缺少标题节点                                   | 调用解析                       | 与文档一致：失败或 `title is None`（二选一，写死策略）                                                   |
| S1-13 | 同一 HTML                                           | 连续解析两次                     | 输出确定性一致（可 `model_dump()` 或 JSON 比较）                                                   |


---

## TDD 执行顺序建议

1. S1-10、S1-11（负面路径，接口与错误类型先定型）
2. S1-01（最小 green：能返回模型且有 title）
3. S1-02～S1-09（golden 全量字段）
4. S1-12、S1-13（边界与确定性）
