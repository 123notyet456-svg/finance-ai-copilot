import { mockDocuments, mockGate, mockMetrics, mockPolicyRequest, mockReviewDetail, mockReviews, sampleResult } from "./mock-data";
import type { AgentResult, Conversation, ConversationMessage, ConversationReply, MetricsSummary, PilotGate, PolicyDocument, PolicyRequest, ReviewDecision, ReviewDetail, ReviewSummary } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const API_MODE = process.env.NEXT_PUBLIC_API_MODE ?? "mock";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: isFormData ? init?.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.message ?? detail?.detail ?? `请求失败（${response.status}）`);
  }
  return response.json() as Promise<T>;
}

let mockConversation: Conversation | null = null;
const now = () => new Date().toISOString();
const mockMessage = (role: "user" | "assistant", content: string, result?: AgentResult): ConversationMessage => ({
  message_id: `MSG-${crypto.randomUUID()}`,
  conversation_id: mockConversation?.conversation_id ?? "CONV-DEMO",
  role,
  content,
  created_at: now(),
  result: result ?? null,
});

export const api = {
  async askPolicy(question: string): Promise<PolicyRequest> {
    if (API_MODE === "mock") {
      await new Promise((resolve) => setTimeout(resolve, 450));
      const needsReview = /加班|教育|忽略制度/.test(question);
      return needsReview ? { question, review_id: "POLICY-005", result: { ...sampleResult, request_id: "demo-review-001", recommendation: "needs_review", requires_human_review: true, summary: "当前制度中没有找到能够直接支持该问题的明确依据，已进入财务复核。", sources: [] } } : { ...mockPolicyRequest, question };
    }
    return request<PolicyRequest>("/api/v1/policy/questions", { method: "POST", body: JSON.stringify({ question, top_k: 5 }) });
  },
  getPolicyRequest: (id: string) => API_MODE === "mock" ? Promise.resolve({ ...mockPolicyRequest, result: { ...mockPolicyRequest.result, request_id: id } }) : request<PolicyRequest>(`/api/v1/policy/requests/${id}`),
  getDocuments: (): Promise<PolicyDocument[]> => API_MODE === "mock" ? Promise.resolve(mockDocuments) : request("/api/v1/policy/documents"),
  async uploadDocument(file: File, title: string, version: string): Promise<PolicyDocument> {
    if (API_MODE === "mock") {
      const document: PolicyDocument = { document_id: `DOC-${crypto.randomUUID()}`, title: title || file.name, version: version || "v1", processing_status: "ready", synthetic: false, source: "upload", file_name: file.name, file_type: file.name.split(".").pop() ?? null, content_hash: "mock-hash", chunk_count: 1, uploaded_at: now() };
      mockDocuments.push(document);
      return document;
    }
    const body = new FormData(); body.append("file", file); body.append("title", title); body.append("version", version);
    return request<PolicyDocument>("/api/v1/policy/documents/upload", { method: "POST", body });
  },
  async setDocumentStatus(id: string, processing_status: "ready" | "disabled"): Promise<PolicyDocument> {
    if (API_MODE === "mock") {
      const document = mockDocuments.find((item) => item.document_id === id); if (!document) throw new Error("文档不存在"); document.processing_status = processing_status; return document;
    }
    return request(`/api/v1/policy/documents/${id}`, { method: "PATCH", body: JSON.stringify({ processing_status }) });
  },
  async createConversation(): Promise<Conversation> {
    if (API_MODE === "mock") { mockConversation = { conversation_id: `CONV-${crypto.randomUUID()}`, title: "新的制度问答", created_at: now(), updated_at: now(), messages: [] }; return mockConversation; }
    return request("/api/v1/conversations", { method: "POST", body: JSON.stringify({}) });
  },
  async getConversation(id: string): Promise<Conversation> {
    if (API_MODE === "mock" && mockConversation?.conversation_id === id) return mockConversation;
    return request(`/api/v1/conversations/${id}`);
  },
  async sendConversationMessage(id: string, content: string): Promise<ConversationReply> {
    if (API_MODE === "mock") {
      if (!mockConversation) throw new Error("请先创建会话");
      const user = mockMessage("user", content); const needsReview = /加班|教育|忽略制度/.test(content);
      const result = { ...sampleResult, request_id: `REQ-${crypto.randomUUID()}`, recommendation: needsReview ? "needs_review" as const : "warning" as const, requires_human_review: needsReview, summary: needsReview ? "当前制度中没有找到能够直接支持该问题的明确依据。" : sampleResult.summary, sources: needsReview ? [] : sampleResult.sources };
      const assistant = mockMessage("assistant", result.summary, result); mockConversation.messages.push(user, assistant); mockConversation.updated_at = now();
      return { conversation_id: id, user_message: user, assistant_message: assistant };
    }
    return request(`/api/v1/conversations/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) });
  },
  auditInvoice: (payload: Record<string, string>): Promise<AgentResult> => API_MODE === "mock" ? Promise.resolve({ ...sampleResult, request_id: "demo-invoice-001", module: "invoice_audit", recommendation: Number(payload.total_amount) >= 10000 ? "needs_review" : "warning", requires_human_review: Number(payload.total_amount) >= 10000, summary: Number(payload.total_amount) >= 10000 ? "金额达到人工复核阈值，已进入财务复核。" : "字段结构完整；这是合成数据规则演示，不包含真实 OCR。", sources: [] }) : request("/api/v1/invoice-audits", { method: "POST", body: JSON.stringify(payload) }),
  getReviews: (): Promise<ReviewSummary[]> => API_MODE === "mock" ? Promise.resolve(mockReviews) : request("/api/v1/reviews?status=pending"),
  getReview: (id: string): Promise<ReviewDetail> => API_MODE === "mock" ? Promise.resolve({ ...mockReviewDetail, review_id: id, source_test_id: id }) : request(`/api/v1/reviews/${id}`),
  decideReview: (id: string, decision: ReviewDecision, notes: string, override?: string) => API_MODE === "mock" ? Promise.resolve({ review_id: id, review_decision: decision }) : request(`/api/v1/reviews/${id}/decisions`, { method: "POST", body: JSON.stringify({ reviewer: "Demo Finance Reviewer", decision, notes, overridden_recommendation: override || null }) }),
  getMetrics: (): Promise<MetricsSummary> => API_MODE === "mock" ? Promise.resolve(mockMetrics) : request("/api/v1/metrics/summary"),
  getGate: (): Promise<PilotGate> => API_MODE === "mock" ? Promise.resolve(mockGate) : request("/api/v1/pilot-gate"),
};
