# Phase 4–6 构建报告

> 本报告随每个 Phase 更新。所有数据均为合成样本，不包含真实财务数据。

## Phase 4：真实 Policy QA RAG

- 状态：通过（第 1 轮修复后）。
- 测试：`17 passed`。
- 修复：显式关闭 SQLite 连接，Windows 临时数据库删除验证通过。
- 真实实现：SQLite 持久化向量库、OpenAI LLM/Embedding Adapter、文档 ingest/chunk/upsert/retrieve/answer。
- Fake 保留：缺 Key、SDK 或 Provider 异常时自动 fallback。
- 外部调用：当前环境未检测到 API Key，不执行真实请求。
- Fallback：发生；Embedding 与 LLM 均自动使用 Fake，向量库使用真实 SQLite。

## Phase 5

- 状态：通过（第 1 轮修复后）。
- 测试：`19 passed`，无警告。
- 修复：测试枚举使用别名，消除 pytest 误收集警告。
- 真实实现：SQLite Repository、三类 POC 记录持久化、JSON/CSV/Markdown 导出。
- Streamlit：新增历史测试记录简单列表，UI 不包含持久化业务逻辑。

## Phase 6

- 状态：通过（首轮）。
- 测试：`25 passed`。
- 合成基线：正常=`pass`、异常=`reject`、边界=`needs_review`。
- 真实实现：合成 JSON 字段规范化、日期/抬头/金额/计算/阈值/必填/重复九类确定性规则。
- 安全边界：所有输出仅为 Agent 建议，UI 明示不构成审批、拒绝或付款动作。

## Phase 4–6 阶段结论

- 完成 Phase：4、5、6 均通过验收。
- 真实实现：SQLite 向量库、SQLite Repository、确定性发票规则、结构化导出。
- 仍为 Fake：当前 LLM 与 Embedding（环境无 API Key）；OCR 未接入。
- Fallback：已发生且符合预期；缺 Key 时整体测试不中断。
- Streamlit：最终 HTTP 启动探针返回 200。
- pytest：Phase 6 验收为 `25 passed`；完成 Phase 7–9 后最终回归为 `31 passed`。
- 后续执行：Phase 7–9 已完成，详见 `docs/overnight-build-report-phase-7-9.md`。
