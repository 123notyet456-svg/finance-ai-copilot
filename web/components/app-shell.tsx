"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BookOpen, FileCheck2, Home, Library, ShieldCheck } from "lucide-react";
import { useRole } from "./role-provider";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "工作台", icon: Home }, { href: "/policy", label: "制度问答", icon: BookOpen },
  { href: "/invoices", label: "发票审核", icon: FileCheck2 }, { href: "/reviews", label: "复核队列", icon: ShieldCheck },
  { href: "/knowledge", label: "制度库", icon: Library }, { href: "/metrics", label: "验证看板", icon: BarChart3 },
];
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname(); const { role, setRole } = useRole();
  return <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
    <aside className="border-r bg-[#111a2e] text-slate-200 lg:fixed lg:inset-y-0 lg:w-[240px]">
      <div className="flex h-16 items-center gap-3 border-b border-white/10 px-5"><div className="grid h-9 w-9 place-items-center rounded-lg bg-blue-500 font-bold text-white">F</div><div><p className="text-sm font-semibold text-white">Finance AI</p><p className="text-xs text-slate-400">Copilot · POC</p></div></div>
      <nav className="flex gap-1 overflow-x-auto p-3 lg:block lg:space-y-1">
        {nav.map((item) => { const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href); const Icon = item.icon; return <Link key={item.href} href={item.href} className={cn("flex shrink-0 items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition", active ? "bg-white/12 text-white" : "text-slate-400 hover:bg-white/7 hover:text-white")}><Icon className="h-4 w-4" />{item.label}</Link>; })}
      </nav>
      <div className="m-4 hidden rounded-lg border border-white/10 bg-white/5 p-3 text-xs leading-5 text-slate-400 lg:block">当前为合成数据环境。系统不自动审批、拒绝或付款。</div>
    </aside>
    <div className="lg:col-start-2">
      <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-white/90 px-5 backdrop-blur lg:px-8"><div><p className="text-sm font-medium">产品体验环境</p><p className="text-xs text-muted-foreground">CONDITIONAL_GO · 非生产系统</p></div><label className="flex items-center gap-2 text-xs text-muted-foreground"><span>演示角色</span><select aria-label="演示角色" className="rounded-lg border bg-white px-3 py-2 text-sm text-foreground" value={role} onChange={(e) => setRole(e.target.value as typeof role)}><option value="employee">员工</option><option value="finance_reviewer">财务复核人</option></select></label></header>
      <main className="mx-auto max-w-7xl p-5 lg:p-8">{children}</main>
    </div>
  </div>;
}
