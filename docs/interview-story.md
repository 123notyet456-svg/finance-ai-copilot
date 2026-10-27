# Finance AI Copilot 面试故事（STAR）

## Situation｜业务背景

财务团队有两类典型重复劳动：一类是员工反复咨询差旅、报销和发票制度，财务人员需要不断搜索文档并解释条款；另一类是发票基础审核，需要反复核对日期、抬头、金额、税额和必填字段。

这类场景很适合 AI 辅助，但风险也很明确：制度问答可能产生无依据结论，发票审核可能错误放行，高风险结果如果没有人工兜底就不能进入真实业务。

## Task｜我的任务

我的目标不是直接做一个生产系统，而是构建一个 v0.1 POC，回答三个问题：

1. AI 能否在制度问答和发票基础审核中提供可验证价值？
2. 失败是否能被识别、记录并稳定路由到人工复核？
3. 当前质量、安全和工程边界是否足以进入小范围 Pilot？

因此我把成功标准定义为：可运行、可测试、可引用、可拒答、可追溯、可人工覆盖，并最终输出明确的 Pilot Gate。

## Action｜关键行动

### 1. 从业务假设和风险边界开始

我先定义 POC 范围、冻结样本、模块指标和硬门槛。系统只提供 Agent 建议，不自动审批、不自动拒绝、不自动付款；所有数据都使用合成样本。

### 2. 构建证据约束的 Policy QA RAG

链路包含文档校验、SHA-256、切分、Embedding、SQLite 向量检索、Prompt 构建和结构化引用。为了防止高分错误检索，我增加了 evidence support checker 与 retrieval confidence gate：城市、职级、金额等条件必须被同一证据直接支持，否则不调用 LLM，直接返回 `needs_review`。

### 3. 用确定性规则处理发票审核

日期是否超期或位于未来、抬头是否匹配、金额是否为正、价税是否平衡、阈值、必填字段和重复检测都由 Python 规则处理。LLM 不负责这些高确定性判断，也不执行任何业务动作。

### 4. 用 Port / Adapter 隔离基础设施

业务模块只依赖 LLM、Embedding、VectorStore 和 Repository Port。OpenAI SDK 只存在于 Adapter；缺 Key、SDK 异常或调用失败时自动回退到 Fake，确保测试和演示不依赖外部服务。

### 5. 建立测试、失败与人工复核闭环

每次运行都形成 TestRecord。失败转化为 FailureCaseRecord，并关联回归测试。人工评审使用追加式 HumanReviewRecord，不覆盖 Agent 原始输出。

`POLICY-005` 曾因错误检索把北京问题匹配到上海制度。修复时我没有删除样本或硬编码 test ID，而是增加通用证据门禁；历史失败保留并标记为 fixed。

### 6. 用 Pilot Gate 而不是主观 Demo 作结论

Gate 综合模块通过率、未关闭高严重度失败、真实人工复核覆盖和 Provider 状态。即使自动 baseline 全部通过，只要真实财务评审或真实 Provider 验证缺失，就不能升级为 GO。

## Result｜结果

- pytest：44 passed。
- 冻结 baseline：13/13。
- Policy QA：10/10；6 个无依据问题进入 `needs_review`。
- Invoice Audit：3/3。
- 未关闭高严重度失败：0；`FAIL-POLICY-005` 保留且为 fixed。
- Human-in-the-loop 流程完成 8 项模拟演练：confirmed 7、cannot_determine 1。
- 未发现自动审批、自动拒绝或自动付款等越权输出。
- Streamlit HTTP 200。
- Pilot Gate：`CONDITIONAL_GO`。

> **Simulated review / 模拟评审 / 非真实财务专家确认。** 8 项模拟评审只证明流程可用，不代表财务专家背书；8 项真实 pending review 仍完整保留。

## Reflection｜复盘

这个项目最重要的结果不是 13/13，而是系统能够暴露不确定性并拒绝越权。没有直接给 GO，是因为：

- 冻结集规模仍有限；
- 真实财务专家尚未完成独立评审；
- 当前环境无受控 API Key，真实 Provider 的质量、延迟和成本尚未验证；
- OCR/Vision 和真实票据证据不在 v0.1 范围。

下一步应优先完成真实财务评审和受控 Provider baseline，而不是继续堆叠功能。只有证据、评审和运行指标都满足门槛，才有资格进入小范围 Pilot。
