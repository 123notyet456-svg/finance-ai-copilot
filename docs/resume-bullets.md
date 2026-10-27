# Finance AI Copilot 简历材料

## 中文

### 项目简介

Finance AI Copilot 是一个面向财务制度问答与合成发票审核的 AI POC 价值验证系统。项目通过证据约束 RAG、确定性规则引擎、Port/Adapter 架构、冻结测试集、失败闭环和 Human-in-the-loop，判断系统是否具备进入小范围 Pilot 的条件，而不是仅展示理想 Demo。

### 项目 Bullet

- 设计并实现财务制度 Policy QA RAG 链路，结合向量相关度、引用直接支持度和城市/职级/金额条件门禁，使无依据问题稳定进入 `needs_review`，避免跨制度错误结论。
- 基于 Python 与 Pydantic 构建合成发票规则引擎，覆盖日期、抬头、金额、价税平衡、阈值、必填字段和重复检测，明确区分 Agent 建议与最终业务动作。
- 采用 Port/Adapter 与依赖注入解耦 LLM、Embedding、向量库和 Repository，限制 Provider SDK 仅存在于 Adapter，并实现缺 Key、超时或调用异常时的 Fake fallback。
- 建立 TestRecord、FailureCaseRecord 与 HumanReviewRecord 闭环，保留 Agent 原始输出和失败历史；将 `POLICY-005` 错误检索转化为通用证据门禁和永久回归测试。
- 完成 41 项 pytest、13/13 冻结 baseline、8 项模拟 Human-in-the-loop 流程验证和 Streamlit Dashboard，形成 `CONDITIONAL_GO` Pilot Gate，并明确真实财务评审与受控 Provider 验证前置条件。

### 面试口述版

“我做的不是一个自动审批机器人，而是一套财务 AI POC 验证系统。它有两个场景：制度问答和合成发票审核。我把 LLM、Embedding、向量库和存储通过 Port/Adapter 解耦，制度问答在生成前会检查引用是否直接支持城市、职级和金额条件；发票的日期和金额判断则全部由确定性规则处理。项目最有代表性的失败是北京住宿问题曾错误检索上海制度，我没有删掉样本或写 test ID 特例，而是增加通用证据门禁，并把失败保留为回归案例。现在自动测试 44 项、冻结 baseline 13/13，但我仍把 Gate 保持在 Conditional Go，因为模拟评审不等于财务专家背书，真实 Provider 的质量、延迟和成本也还没受控验证。”

## English

### Project Summary

Finance AI Copilot is a value-validation POC for finance policy Q&A and synthetic invoice review. It combines evidence-gated RAG, deterministic rules, Port/Adapter boundaries, frozen evaluations, failure tracking, and Human-in-the-loop records to determine whether an AI workflow is ready for a controlled pilot—not merely whether it can produce a convincing demo.

### Resume Bullets

- Built an evidence-gated finance policy RAG workflow that combines vector relevance with direct citation support and condition checks for city, employee level, and amount, routing unsupported questions to `needs_review`.
- Implemented a deterministic synthetic invoice review engine in Python and Pydantic covering date validity, buyer name, positive amounts, tax reconciliation, thresholds, required fields, and duplicate detection.
- Applied Port/Adapter architecture and dependency injection to isolate LLM, embedding, vector-store, and repository providers; kept provider SDKs out of business modules and added automatic Fake fallback for missing keys or provider failures.
- Created an auditable evaluation loop with TestRecord, FailureCaseRecord, and append-only HumanReviewRecord models, preserving original agent output and converting failures into permanent regression tests.
- Delivered 41 passing pytest tests, a 13/13 frozen baseline, an 8-item simulated HITL process validation, and a Streamlit dashboard, while maintaining a transparent `CONDITIONAL_GO` Pilot Gate.

### Interview Pitch

“I built Finance AI Copilot as a gated POC rather than an autonomous finance system. Policy answers must pass both retrieval confidence and direct evidence support before the LLM is called, while invoice checks remain deterministic. The architecture keeps provider SDKs in adapters and retains Fake fallbacks, so tests do not depend on external APIs. A key failure involved a Beijing policy question retrieving a Shanghai rule; instead of hardcoding the test or deleting it, I implemented a generic evidence gate and retained the failure as a fixed regression case. The project now has 41 passing tests and a 13/13 synthetic baseline, but the Pilot Gate remains Conditional Go because simulated review is not expert sign-off and controlled real-provider validation is still required.”

## 使用提醒

- 不要将 simulated review 表述为真实财务专家评审。
- 不要把 `CONDITIONAL_GO` 简化为 GO。
- 面试时主动说明样本规模、Fake Provider 和真实 OCR 尚未覆盖。
