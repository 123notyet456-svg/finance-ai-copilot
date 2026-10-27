# TODO / Delivery Status

## 已完成

- [x] 外部制度上传：PDF / DOCX / Markdown / TXT 解析、哈希、版本、启停与语料索引替换。
- [x] 多轮制度问答：会话/消息持久化、追问补全、每轮重新检索与复核分流。
- [x] 前端先行蓝图：Next.js 产品 Web、八个页面、演示角色切换与全状态 Mock。
- [x] FastAPI v1 契约：制度问答、发票规则、复核、指标、Pilot Gate 和统一错误。
- [x] OpenAPI 生成 TypeScript 类型，Mock 与 HTTP Client 共用契约。
- [x] Playwright 真实 HTTP 纵向切片：制度拒答 -> 创建复核 -> 财务队列。
- [x] 项目骨架、公共 Pydantic Schema、Port/Adapter 分层与 Streamlit 入口。
- [x] 本地文件校验、SHA-256、Markdown/TXT 读取和 PDF 文本接口占位。
- [x] SQLite 持久化向量库与 POC Repository。
- [x] Policy QA 文档 ingest、切分、检索、引用、无依据 fallback。
- [x] Evidence support checker 与 retrieval confidence gate。
- [x] `POLICY-005` 修复；失败历史保留并标记 fixed。
- [x] 合成发票字段规范化与九类确定性规则。
- [x] TestRecord、FailureCaseRecord、HumanReviewRecord 与导出。
- [x] 冻结 baseline：10 个制度问题 + 3 个合成发票，13/13。
- [x] pytest：44 passed；Streamlit HTTP 200。
- [x] 模拟 Human-in-the-loop 流程：8 项。
- [x] 作品集 README、STAR 故事、面试架构、演示稿、双语简历、指标与路线文档。
- [x] Phase 13C 普通用户体验：搜索式制度问答、简洁答案、折叠依据和用户可读发票建议。

> **Simulated review / 模拟评审 / 非真实财务专家确认。** 模拟评审不计入真实财务评审覆盖率。

## 当前 Gate

- Pilot Gate：`CONDITIONAL_GO`，不得改写为 GO。
- 未关闭高严重度失败：0。
- 真实 pending review：8 项，必须保留。
- 历史失败：`FAIL-POLICY-005` 保留，状态 fixed。
- 当前无受控真实 Provider baseline，默认使用 Fake fallback。

## Phase 14：真实财务专家评审

- [ ] 由授权财务人员独立处理 8 项 pending review。
- [ ] 核对制度引用、发票规则命中和建议状态。
- [ ] 为异常发票补充可核验的原始合成凭证。
- [ ] 使用真实 HumanReviewRecord 记录决定，不复用 simulated 结果。

## Phase 15：受控真实 Provider 验证

- [ ] 使用环境变量提供 API Key，不写入代码或仓库。
- [ ] 在非敏感合成数据上运行真实 LLM/Embedding baseline。
- [ ] 记录质量、延迟、Token、成本、超时和 fallback。
- [ ] 保持无 Key 或 Provider 失败时 pytest 可通过。

## Phase 16：扩展冻结测试集

- [ ] 将制度问题扩展到 20–50 题。
- [ ] 增加版本冲突、跨条款、对抗和引用直接支持性样本。
- [ ] 由财务专家确认标准答案与拒答边界。
- [ ] 为 baseline 增加独立 run_id，保留多轮历史。

## Phase 17：OCR / Vision

- [ ] 通过 OCRPort 接入受控 Vision Adapter。
- [ ] 只使用合成或脱敏票据。
- [ ] 保存字段证据与置信度；低置信必须进入人工复核。
- [ ] 覆盖旋转、模糊、裁切、多票同图和 Provider 超时。

## Phase 18：FastAPI Pilot 服务化

- [ ] 复用现有 Service，不把业务逻辑搬进 API 层。
- [ ] 增加鉴权、审计、数据保留、监控、限流和超时策略。
- [ ] 设计数据库 migration、备份和并发写入方案。

## Phase 19：小范围 Pilot

- [ ] 明确 Pilot 用户、数据范围和人工责任人。
- [ ] 比较人工耗时、修改成本、准确率、延迟与费用。
- [ ] 所有高风险动作保持人工确认。
- [ ] Gate 条件全部满足后再讨论扩大范围。

## POC 技术债

- [ ] 扫描 PDF 和图片制度尚未接入 OCR；当前只处理文本型 PDF。
- [ ] 多轮问题补全为可解释的确定性规则；复杂指代仍需扩展冻结测试集。
- [ ] 演示角色切换尚不是真实鉴权/RBAC，不可进入真实 Pilot。
- [ ] 尚未完成 3 名员工视角与 2 名财务视角用户的可用性试用。
- [ ] 扫描 PDF OCR 尚未实现。
- [ ] 发票类型、币种、红票、多税率和复杂重复指纹尚未覆盖。
- [ ] SQLite 文档版本清理和 embedding 模型迁移策略待设计。
- [ ] 待评审队列的分页、并发覆盖冲突、身份可信度和 SLA 待完善。
