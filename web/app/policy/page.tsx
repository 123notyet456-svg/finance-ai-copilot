"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, Loader2, MessageSquarePlus, Send, ShieldAlert, User } from "lucide-react";
import { api } from "@/lib/api-client";
import type { ConversationMessage } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const suggestions = ["上海出差住宿标准是什么？", "报销发票需要满足哪些要求？", "周末加班餐费一定可以报销吗？"];

export default function PolicyPage() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    const content = question.trim(); if (!content || loading) return;
    setLoading(true); setError(""); setQuestion("");
    try {
      let activeId = conversationId;
      if (!activeId) { const conversation = await api.createConversation(); activeId = conversation.conversation_id; setConversationId(activeId); }
      const reply = await api.sendConversationMessage(activeId, content);
      setMessages((current) => [...current, reply.user_message, reply.assistant_message]);
    } catch (reason) {
      setQuestion(content); setError(reason instanceof Error ? reason.message : "服务暂时不可用");
    } finally { setLoading(false); }
  }

  function newConversation() { setConversationId(null); setMessages([]); setQuestion(""); setError(""); }

  return <>
    <PageHeader eyebrow="员工任务" title="与制度助手对话" description="支持连续追问；每一轮都会补全问题并重新检索当前有效制度，而不是仅依赖聊天记忆。" action={<Button variant="outline" onClick={newConversation}><MessageSquarePlus className="h-4 w-4" />新建会话</Button>} />

    <div className="mb-4 flex items-center justify-between text-xs text-muted-foreground"><span>{conversationId ? `会话 ${conversationId}` : "尚未创建会话"}</span><span>外部制度请在“制度库”上传</span></div>

    <Card className="min-h-[420px]"><CardContent className="p-5">
      {messages.length === 0 ? <div className="grid min-h-[300px] place-items-center text-center"><div><div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-blue-50 text-primary"><BookOpen className="h-6 w-6" /></div><p className="mt-4 font-medium">从一个具体问题开始</p><p className="mt-1 text-sm text-muted-foreground">回答后可以继续问“那北京呢？”或“需要哪些材料？”</p><div className="mt-5 flex max-w-2xl flex-wrap justify-center gap-2">{suggestions.map((item) => <button key={item} onClick={() => setQuestion(item)} className="rounded-full bg-muted px-3 py-1.5 text-xs text-slate-600 hover:bg-blue-50 hover:text-primary">{item}</button>)}</div></div></div> :
        <div className="space-y-5">{messages.map((message) => message.role === "user" ? <div key={message.message_id} className="flex justify-end gap-3"><div className="max-w-2xl rounded-2xl rounded-tr-sm bg-primary px-4 py-3 text-sm leading-6 text-white">{message.content}</div><div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-200"><User className="h-4 w-4" /></div></div> : <div key={message.message_id} className="flex gap-3"><div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-blue-50 text-primary"><BookOpen className="h-4 w-4" /></div><div className="max-w-3xl flex-1 rounded-2xl rounded-tl-sm border bg-white p-4 shadow-sm">{message.result && <div className="mb-3 flex items-center justify-between"><StatusBadge value={message.result.recommendation} /><span className="font-mono text-[11px] text-muted-foreground">{message.result.latency_ms} ms</span></div>}<p className="text-sm leading-7">{message.content}</p>{message.result?.requires_human_review && <div className="mt-4 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900"><ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />不能形成确定性结论，已进入财务复核。</div>}{message.result && message.result.sources.length > 0 && <div className="mt-4 space-y-2">{message.result.sources.map((source) => <div key={`${message.message_id}-${source.document_id}`} className="rounded-lg bg-slate-50 p-3"><p className="text-xs font-medium">《{source.title}》</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{source.excerpt}</p></div>)}</div>}{message.result && <Link className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-primary" href={`/policy/requests/${message.result.request_id}`}>查看本轮完整记录 <ArrowRight className="h-3.5 w-3.5" /></Link>}{message.standalone_question && message.standalone_question !== messages.find((candidate) => candidate.message_id === message.message_id)?.content && <details className="mt-3 text-xs text-muted-foreground"><summary className="cursor-pointer">查看本轮检索问题</summary><p className="mt-2 rounded bg-muted p-2">{message.standalone_question}</p></details>}</div></div>)}</div>}
      {loading && <div className="mt-5 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin text-primary" />正在结合会话补全问题并重新检索制度…</div>}
      {error && <div className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
    </CardContent></Card>

    <div className="sticky bottom-4 mt-4 rounded-xl border bg-white p-3 shadow-lg"><div className="flex gap-3"><Input aria-label="制度问题" className="h-11" placeholder={messages.length ? "继续追问，例如：那北京呢？" : "输入制度问题"} value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => event.key === "Enter" && submit()} /><Button size="lg" onClick={submit} disabled={loading || !question.trim()}><Send className="h-4 w-4" />发送</Button></div><p className="mt-2 px-1 text-[11px] text-muted-foreground">系统只提供辅助答案；高风险、无依据和冲突结果必须人工复核。</p></div>
  </>;
}
