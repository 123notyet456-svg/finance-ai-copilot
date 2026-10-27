# Finance AI Copilot 项目指标

> 指标日期：2026-06-30。所有数据均为合成样本；模拟评审不代表真实财务专家意见。

| 指标 | 当前值 | 说明 |
|---|---:|---|
| pytest | 44 passed | 全量自动化测试通过 |
| 冻结 baseline | 13/13 | 10 个制度问题 + 3 个合成发票 |
| Policy QA | 10/10 | 4 个可回答问题，6 个无依据拒答问题 |
| Invoice Audit | 3/3 | 正常、异常、边界 |
| Pilot Gate | `CONDITIONAL_GO` | 不得表述为 GO |
| 模拟人工评审 | 8 | simulated_non_expert，仅验证流程 |
| 模拟 confirmed | 7 | 不计入真实评审覆盖率 |
| 模拟 cannot_determine | 1 | 异常发票缺原始来源证据 |
| needs_more_info | 0 | 当前模拟批次 |
| overridden | 0 | 当前模拟批次 |
| 越权业务动作 | 0 | 未发现自动审批/拒绝/付款 |
| 真实 pending review | 8 retained | 未因模拟评审删除或完成 |
| 真实人工评审完成 | 0 | 仍是 Pilot 前置条件 |
| 未关闭高严重度失败 | 0 | 历史失败仍保留 |
| `FAIL-POLICY-005` | fixed | 北京/上海证据错配回归案例 |
| Fake fallback | available | 缺 Key 或 Provider 异常时可用 |
| 硬编码 API Key | 0 | Key 仅允许来自环境变量 |
| 真实财务数据 | 0 | 仅合成样本 |
| 自动审批/拒绝/付款 | 0 | 所有输出仅为建议 |
| Streamlit 探针 | HTTP 200 | 本地启动验证通过 |

## 指标解释

13/13 证明当前冻结小样本可以稳定回归，不代表真实业务准确率。`CONDITIONAL_GO` 表示工程链路和风险路由具备继续验证价值，但真实财务评审、受控 Provider baseline 和更大测试集尚未完成。

> **Simulated review / 模拟评审 / 非真实财务专家确认。** 模拟 confirmed 只确认流程表现，不确认财务结论。
