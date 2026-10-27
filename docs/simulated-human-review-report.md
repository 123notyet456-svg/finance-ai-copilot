# Simulated Human Review Report

> **Simulated review / 模拟评审 / 非真实财务专家确认**

本报告仅验证 Human-in-the-loop 流程，不代表真实财务专家意见或企业背书。

## Reviewer

- reviewer_name: Demo Finance Reviewer
- reviewer_role: Simulated reviewer for portfolio validation
- reviewer_type: simulated_non_expert
- review_scope: process validation only

## Summary

- reviewed: 8
- confirmed: 7
- needs_more_info: 0
- cannot_determine: 1
- overridden: 0
- original_agent_outputs_unchanged: true
- pilot_gate: CONDITIONAL_GO（模拟评审不计入真实人工复核覆盖率）

| source_test_id | module | Agent 建议 | 模拟决定 | 风险 |
|---|---|---|---|---|
| POLICY-010 | policy_qa | needs_review | confirmed | medium |
| POLICY-009 | policy_qa | needs_review | confirmed | medium |
| POLICY-008 | policy_qa | needs_review | confirmed | medium |
| POLICY-007 | policy_qa | needs_review | confirmed | medium |
| POLICY-006 | policy_qa | needs_review | confirmed | medium |
| INVOICE-EDGE-001 | invoice_audit | needs_review | confirmed | medium |
| INVOICE-ABNORMAL-001 | invoice_audit | reject | cannot_determine | high |
| POLICY-005 | policy_qa | needs_review | confirmed | medium |

## Boundary

- Simulated review / 模拟评审 / 非真实财务专家确认
- Human-in-the-loop process validated by simulated review.
- 真实财务评审仍然是进入 Pilot 的前置条件。
- 系统不自动审批、不自动拒绝、不自动付款。

## Final Validation

- pytest: 41 passed
- Streamlit HTTP status: 200
- simulated review records: 8
- original Agent outputs unchanged: true
- real pending reviews retained: 8
- Pilot Gate: CONDITIONAL_GO
- Simulated review / 模拟评审 / 非真实财务专家确认
