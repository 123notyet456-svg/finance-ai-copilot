# Finance AI Copilot 后续路线

路线原则：先关闭 Gate 条件，再扩展功能；每个 Phase 都需要冻结输入、结构化记录、pytest 和明确验收标准。

## Phase 14：真实财务专家评审

目标：由授权财务人员独立处理当前 8 项 pending review。

- 核对输入、引用、规则命中和 Agent 建议。
- 对异常发票补充可核验原始合成凭证。
- 用真实 HumanReviewRecord 记录 confirmed / overridden / cannot_determine。
- 不复用模拟评审作为专家结论。

验收：真实评审身份、时间、依据和决定可追溯；Gate 的人工复核条件由真实记录计算。

## Phase 15：受控真实 Provider 验证

目标：在非敏感合成数据上验证真实 LLM 与 Embedding。

- API Key 只从环境变量读取。
- 真实调用只通过 Adapter。
- 保留 Fake fallback、超时和失败记录。
- 记录质量、延迟、Token 和估算成本。

验收：缺 Key 或 Provider 失败时测试不中断；真实 baseline 与 Fake baseline 可比较。

## Phase 16：扩展冻结测试集到 20–50 题

目标：提高结论的代表性，覆盖直接事实、条件、无依据、冲突、版本和对抗问题。

- 由财务专家审核问题与标准答案。
- 增加引用直接支持性评分。
- 保留全部历史失败和回归样本。

验收：冻结 manifest、版本和评审记录完整；Policy QA 达到既定门槛。

## Phase 17：发票审核 OCR / Vision 接入

目标：通过 OCRPort 接入真实或受控 Vision Adapter。

- 先使用脱敏或合成票据。
- 保存字段原值、规范化值、证据位置和置信度。
- 低置信、字段缺失和多票同图必须进入人工复核。

验收：OCR 失败不会产生确定性放行；字段准确率和风险召回可量化。

## Phase 18：FastAPI Pilot 服务化

目标：复用现有 Service，增加受控 Pilot API。

- FastAPI 只作为新接口，不重写业务模块。
- 增加鉴权、审计日志、请求 ID、数据保留和监控。
- 明确超时、重试、限流和降级策略。

验收：Streamlit 与 API 使用同一 Service；权限与数据边界通过评审。

## Phase 19：小范围 Pilot

目标：在明确用户、数据范围和人工责任人的前提下验证真实业务价值。

- 限定用户与任务范围。
- 所有高风险动作保持人工确认。
- 比较人工耗时、修改成本、质量、延迟和费用。
- 定期复盘失败案例与回归结果。

验收：安全硬门槛、质量指标、人工责任、成本与数据治理全部满足后，才讨论扩大范围。

## 当前不可跳过的顺序

```text
真实财务评审
  -> 受控 Provider 验证
  -> 扩展冻结集
  -> OCR / Vision
  -> FastAPI Pilot 服务化
  -> 小范围 Pilot
```

当前 Gate 保持 `CONDITIONAL_GO`；任何路线文档都不得提前表述为 GO。

