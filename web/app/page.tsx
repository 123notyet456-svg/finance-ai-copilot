import Link from "next/link";
import { ArrowRight, BookOpen, Clock3, FileCheck2, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const modules = [
  { href: "/policy", icon: BookOpen, title: "制度问答", desc: "从合成财务制度中查找有引用、可核验的答案。", status: "真实链路" },
  { href: "/invoices", icon: FileCheck2, title: "发票审核", desc: "预览字段、规则命中和人工复核分流。", status: "规则已接通 / OCR Mock" },
  { href: "/reviews", icon: ShieldCheck, title: "人工复核", desc: "核对证据，追加确认、覆盖或无法判断记录。", status: "追加式审计" },
];
export default function Home() {
  return <>
    <PageHeader eyebrow="Finance AI Copilot" title="有依据、可复核的财务工作台" description="先把员工与财务人员的完整任务做通，再让后端围绕稳定契约逐条接真。当前仅使用合成数据。" action={<Badge tone="warning">Pilot Gate · CONDITIONAL_GO</Badge>} />
    <section className="grid gap-4 md:grid-cols-3">
      <Card><CardHeader><CardDescription>待人工复核</CardDescription><CardTitle className="text-3xl">8</CardTitle></CardHeader><CardContent className="text-xs text-muted-foreground">真实评审尚未完成</CardContent></Card>
      <Card><CardHeader><CardDescription>冻结测试通过率</CardDescription><CardTitle className="text-3xl">100%</CardTitle></CardHeader><CardContent className="text-xs text-muted-foreground">13 / 13 · 合成样本</CardContent></Card>
      <Card><CardHeader><CardDescription>未关闭高严重度失败</CardDescription><CardTitle className="text-3xl">0</CardTitle></CardHeader><CardContent className="text-xs text-muted-foreground">历史失败仍完整保留</CardContent></Card>
    </section>
    <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">开始一项工作</h2><span className="flex items-center gap-1 text-xs text-muted-foreground"><Clock3 className="h-3.5 w-3.5" />体验环境</span></div><div className="grid gap-4 lg:grid-cols-3">{modules.map(({ href, icon: Icon, title, desc, status }) => <Link key={href} href={href}><Card className="h-full transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md"><CardHeader><div className="mb-4 flex items-center justify-between"><div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-50 text-primary"><Icon className="h-5 w-5" /></div><ArrowRight className="h-4 w-4 text-slate-400" /></div><CardTitle>{title}</CardTitle><CardDescription>{desc}</CardDescription></CardHeader><CardContent><Badge tone="neutral">{status}</Badge></CardContent></Card></Link>)}</div></section>
    <section className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-5"><h2 className="font-medium text-amber-950">风险边界</h2><p className="mt-1 text-sm leading-6 text-amber-800">所有结果均为辅助建议，不构成审批、拒绝或付款决定。低置信、无依据和高风险结果必须由授权财务人员复核。</p></section>
  </>;
}
