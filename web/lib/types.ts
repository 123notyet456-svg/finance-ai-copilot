import type { components } from "./api-schema";

export type Recommendation = components["schemas"]["AgentResultDTO"]["recommendation"];
export type ExecutionStatus = components["schemas"]["AgentResultDTO"]["execution_status"];
export type ReviewDecision = components["schemas"]["ReviewDecisionRequest"]["decision"];
export type SourceReference = components["schemas"]["SourceDTO"];
type GeneratedAgentResult = components["schemas"]["AgentResultDTO"];
export type AgentResult = Omit<GeneratedAgentResult, "findings" | "recommendations" | "sources" | "next_actions"> & {
  findings: string[];
  recommendations: string[];
  sources: SourceReference[];
  next_actions: string[];
};
export type PolicyRequest = Omit<components["schemas"]["PolicyRequestDTO"], "result"> & { result: AgentResult };
export type PolicyDocument = components["schemas"]["PolicyDocumentDTO"];
type GeneratedConversationMessage = components["schemas"]["ConversationMessageDTO"];
export type ConversationMessage = Omit<GeneratedConversationMessage, "result"> & {
  result?: AgentResult | null;
};
export type Conversation = Omit<components["schemas"]["ConversationDTO"], "messages"> & {
  messages: ConversationMessage[];
};
export type ConversationReply = Omit<
  components["schemas"]["ConversationReplyDTO"],
  "user_message" | "assistant_message"
> & {
  user_message: ConversationMessage;
  assistant_message: ConversationMessage;
};
export type ReviewSummary = components["schemas"]["ReviewSummaryDTO"];
export type ReviewDetail = Omit<components["schemas"]["ReviewDetailDTO"], "findings" | "sources" | "agent_output" | "decisions"> & {
  findings: string[];
  sources: SourceReference[];
  agent_output: Record<string, unknown>;
  decisions: Record<string, unknown>[];
};
export type MetricsSummary = components["schemas"]["MetricsSummaryDTO"];

// The Pilot Gate endpoint intentionally exposes the existing domain model directly.
export interface PilotGate {
  recommendation: string;
  overall_pass_rate: number;
  blocking_reasons: string[];
  conditions: string[];
  provider_fallback_observed: boolean;
}
