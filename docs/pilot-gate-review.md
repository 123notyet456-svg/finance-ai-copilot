# Pilot Gate Review

> 仅基于合成样本 / 非真实数据；本结论不构成真实财务系统准入或审批。

## 结论：CONDITIONAL_GO

Phase 11 扩展冻结 baseline 总体通过率为 100%。当前版本可继续受控 POC 验证，但在条件项关闭前不得进入真实财务 Pilot。

| 模块 | 样本 | 通过 | 失败 | 通过率 | 应人工复核 | 已人工复核 |
|---|---:|---:|---:|---:|---:|---:|
| policy_qa | 10 | 10 | 0 | 100.00% | 6 | 0 |
| invoice_audit | 3 | 3 | 0 | 100.00% | 2 | 0 |

## Phase 10 修复结果

- `POLICY-005` 当前返回 `needs_review`，不会形成北京住宿标准的确定结论。
- 根因分类：主因 `RAG_WRONG_RETRIEVAL`，控制层表现 `RAG_UNSUPPORTED_CLAIM`。
- `FAIL-POLICY-005` 保留在失败案例库中，`fix_status=fixed`。
- 生产代码不存在针对 `POLICY-005` 的 test ID 分支。
- 可回答问题若过度拒答会被 baseline 判失败，未降低测试标准。

## Phase 11–12 增强

- 无依据压力集扩展到 6 项，覆盖北京、广州、深圳、加班餐费、采购审批和教育费。
- 扩展 baseline 为 13/13，通过率 100%，未关闭失败为 0。
- 已生成 8 项 pending human review 队列，不伪造人工评审结果。

## 剩余条件

- 人工复核覆盖不足：应复核 8 项，已完成 0 项。
- 当前 baseline 使用 Fake Provider fallback，尚未验证真实模型质量、延迟与成本。
- 冻结集规模仍小，必须继续扩充并由财务评审人确认。

## Phase 13A：模拟 Human-in-the-loop 验证

> **Simulated review / 模拟评审 / 非真实财务专家确认**

- Human-in-the-loop process validated by simulated review.
- 模拟评审 8 项：confirmed 7、needs_more_info 0、cannot_determine 1、overridden 0。
- 未发现自动审批、自动拒绝、自动付款等越权输出。
- 模拟评审只验证流程、追加记录和风险边界，不计入真实人工复核覆盖率。
- 真实 pending human reviews 仍为 8 项，真实财务评审完成数仍为 0。
- Pilot Gate 保持 `CONDITIONAL_GO`，不得因模拟评审升级为 GO。

## 安全边界

- 系统不自动审批、不自动拒绝、不自动付款。
- 高风险、无依据、低相关度和冲突结果必须人工复核。
- 所有数据均为合成样本，不得用于真实报销或财务决策。
