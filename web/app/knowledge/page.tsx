"use client";

import { useEffect, useRef, useState } from "react";
import { FileText, Loader2, Power, PowerOff, Upload } from "lucide-react";
import { api } from "@/lib/api-client";
import type { PolicyDocument } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<PolicyDocument[] | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [version, setVersion] = useState("v1");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  const refresh = () => api.getDocuments().then(setDocuments);
  useEffect(() => { refresh(); }, []);

  async function uploadDocument() {
    if (!file) return;
    setUploading(true); setError(""); setMessage("");
    try {
      const uploaded = await api.uploadDocument(file, title.trim() || file.name.replace(/\.[^.]+$/, ""), version.trim() || "v1");
      setMessage(`《${uploaded.title}》已解析并发布到知识库。`);
      setFile(null); setTitle(""); setVersion("v1");
      if (fileInput.current) fileInput.current.value = "";
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "上传失败");
    } finally { setUploading(false); }
  }

  async function toggleDocument(document: PolicyDocument) {
    const next = document.processing_status === "ready" ? "disabled" : "ready";
    await api.setDocumentStatus(document.document_id, next);
    await refresh();
  }

  return <>
    <PageHeader eyebrow="财务配置" title="制度库" description="上传 PDF、DOCX、Markdown 或 TXT；系统解析文本、计算哈希、切分索引，并按版本控制是否参与问答。" />

    <Card className="mb-6 border-blue-100">
      <CardHeader><CardTitle>上传外部制度</CardTitle><CardDescription>单个文件不超过 10 MB。扫描 PDF 暂不支持 OCR；请勿上传未经授权的敏感资料。</CardDescription></CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_160px_auto] lg:items-end">
          <label><span className="mb-1.5 block text-xs font-medium">制度文件</span><Input ref={fileInput} type="file" accept=".pdf,.docx,.md,.markdown,.txt" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
          <label><span className="mb-1.5 block text-xs font-medium">显示名称</span><Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder={file?.name.replace(/\.[^.]+$/, "") || "例如：2026 差旅费制度"} /></label>
          <label><span className="mb-1.5 block text-xs font-medium">版本</span><Input value={version} onChange={(event) => setVersion(event.target.value)} /></label>
          <Button onClick={uploadDocument} disabled={!file || uploading}>{uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}{uploading ? "解析中" : "上传并发布"}</Button>
        </div>
        {file && <p className="mt-3 text-xs text-muted-foreground">已选择：{file.name} · {(file.size / 1024).toFixed(1)} KB</p>}
        {message && <p className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}
        {error && <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      </CardContent>
    </Card>

    <Card><CardContent className="p-0">
      {!documents ? <div className="flex items-center gap-2 p-8 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />加载制度…</div> :
        <div className="divide-y">{documents.map((doc) => <div key={doc.document_id} data-document-title={doc.title} className="flex flex-col justify-between gap-4 p-5 md:flex-row md:items-center">
          <div className="flex items-center gap-4"><div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-50 text-primary"><FileText className="h-5 w-5" /></div><div><p className="font-medium">{doc.title}</p><p className="mt-1 font-mono text-xs text-muted-foreground">{doc.file_name || doc.document_id} · {doc.version}{doc.chunk_count ? ` · ${doc.chunk_count} 个片段` : ""}</p></div></div>
          <div className="flex items-center gap-2"><Badge tone={doc.synthetic ? "neutral" : "primary"}>{doc.synthetic ? "内置合成制度" : "外部上传"}</Badge><Badge tone={doc.processing_status === "ready" ? "success" : "danger"}>{doc.processing_status === "ready" ? "参与检索" : doc.processing_status === "disabled" ? "已停用" : "处理失败"}</Badge>{doc.source !== "builtin" && <Button variant="outline" size="sm" onClick={() => toggleDocument(doc)}>{doc.processing_status === "ready" ? <PowerOff className="h-3.5 w-3.5" /> : <Power className="h-3.5 w-3.5" />}{doc.processing_status === "ready" ? "停用" : "启用"}</Button>}</div>
        </div>)}</div>}
    </CardContent></Card>
    <div className="mt-5 rounded-xl border bg-white p-5"><h2 className="font-medium">索引行为</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">上传后立即发布；下一次提问会用所有“参与检索”的制度重新构建当前语料索引。停用文档后，旧向量会被清除，不再参与回答。</p></div>
  </>;
}
