# 架构说明

## 用途

记录 Finance AI Copilot v0.1 POC 的模块边界和依赖方向。

```text
Next.js Web -> Typed API Client -> FastAPI v1 -> Service/Workflow -> Core Ports <- Adapters
                                      |               |
                               OpenAPI Schema      Evaluation

Streamlit --------------------------> Service/Workflow
```

- `core`：跨模块 Schema、Port、配置、异常和文件处理。
- `adapters`：Fake LLM、Embedding、OCR、Vector Store、Repository。
- `modules`：Policy QA 与 Invoice Audit 业务编排。
- `evaluation`：测试、人工评审、失败案例和报告。
- `interfaces`：只负责输入输出展示。

`interfaces/api` 是产品契约层，负责 HTTP DTO、请求 ID、错误协议和业务 Schema 映射；它不承载检索、发票规则或 Pilot Gate 判定逻辑。`web/` 中的 Mock 与 HTTP Client 共用 OpenAPI 生成类型，可通过 `NEXT_PUBLIC_API_MODE` 切换。

具体 Fake Adapter 只在 `bootstrap/container.py` 组合根中选择；`PolicyQAWorkflow` 通过 `EmbeddingPort`、`VectorStorePort` 和 `LLMPort` 接收依赖，因此可独立替换真实实现。
