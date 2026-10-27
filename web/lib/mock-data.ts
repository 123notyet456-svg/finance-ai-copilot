import type { AgentResult, MetricsSummary, PilotGate, PolicyDocument, PolicyRequest, ReviewDetail, ReviewSummary } from "./types";

export const sampleResult: AgentResult = {
  request_id: "demo-policy-001", module: "policy_qa", execution_status: "completed",
  recommendation: "pass", review_status: "pending",
  summary: "上海出差住宿标准为每晚不超过 600 元；超过标准的部分需要补充说明并进入人工复核。",
  findings: ["适用地点：上海", "标准上限：600 元/晚"],
  recommendations: ["报销时保留住宿发票和出差审批记录"],
  sources: [{ document_id: "sample_policy_travel", title: "合成差旅费管理制度", excerpt: "员工赴上海出差，住宿费标准为每人每天不超过 600 元。", page: 2, score: 0.92 }],
  next_actions: ["查看制度原文"], requires_human_review: false, model_version: "fake-llm-v1",
  prompt_version: "v0.1", rules_version: "v0.1", schema_version: "v0.1", latency_ms: 380,
  estimated_cost: 0, created_at: "2026-06-30T04:00:00Z",
};
export const mockPolicyRequest: PolicyRequest = { question: "上海出差住宿标准是什么？", result: sampleResult };
export const mockDocuments: PolicyDocument[] = [
  { document_id: "sample_policy_travel", title: "合成差旅费管理制度", version: "v1", processing_status: "ready", synthetic: true, source: "builtin", chunk_count: 0 },
  { document_id: "sample_policy_invoice", title: "合成发票及报销凭证制度", version: "v1", processing_status: "ready", synthetic: true, source: "builtin", chunk_count: 0 },
];
export const mockReviews: ReviewSummary[] = [
  { review_id: "POLICY-005", source_test_id: "POLICY-005", module: "policy_qa", recommendation: "needs_review", summary: "当前制度没有找到周末加班餐费的明确依据。", risk_level: "medium", status: "pending", created_at: "2026-06-30T03:10:00Z" },
  { review_id: "INVOICE-002", source_test_id: "INVOICE-002", module: "invoice_audit", recommendation: "reject", summary: "购买方抬头与演示公司名称不一致。", risk_level: "high", status: "pending", created_at: "2026-06-30T02:30:00Z" },
];
export const mockReviewDetail: ReviewDetail = {
  ...mockReviews[0], input_sample: { question: "周末加班餐费一定可以报销吗？" },
  findings: ["检索片段未直接覆盖周末加班餐费", "不能形成确定性结论"], sources: [],
  agent_output: { ...sampleResult, recommendation: "needs_review", requires_human_review: true, summary: mockReviews[0].summary }, decisions: [],
};
export const mockMetrics: MetricsSummary = { total_tests: 13, passed_tests: 13, overall_pass_rate: 1, pending_reviews: 8, completed_reviews: 0, open_failures: 0, modules: [
  { module: "policy_qa", total: 10, passed: 10, pass_rate: 1 }, { module: "invoice_audit", total: 3, passed: 3, pass_rate: 1 },
] };
export const mockGate: PilotGate = { recommendation: "CONDITIONAL_GO", overall_pass_rate: 1, blocking_reasons: [], conditions: ["仍有 8 项待授权财务人员复核", "真实 Provider 质量、延迟与成本尚未形成完整基线"], provider_fallback_observed: true };
