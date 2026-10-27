import { Badge } from "./ui/badge";
import type { Recommendation } from "@/lib/types";
const labels: Record<Recommendation, string> = { pass: "依据充分", warning: "存在提示项", needs_review: "需要人工复核", reject: "建议退回人工核查" };
export function StatusBadge({ value }: { value: Recommendation }) { const tone = value === "pass" ? "success" : value === "warning" ? "warning" : "danger"; return <Badge tone={tone}>{labels[value]}</Badge>; }
