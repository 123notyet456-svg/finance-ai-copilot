# 架构与实现决策

## 2026-06-29

- 在当前空工作区根目录直接建立项目，避免无必要的重复嵌套目录。
- 使用 Python 3.11+、Pydantic v2、pytest 和 Streamlit；不引入真实 Provider SDK。
- Port 使用 `typing.Protocol`，使业务模块可以通过构造器注入任意实现。
- Fake Embedding 使用确定性字符桶向量，Fake Vector Store 使用进程内余弦排序，保证测试稳定且不泄露数据。
- 所有样本使用显著的“合成样本 / 非真实数据 / 不可报销”标记。
- PDF 仅实现轻量文本提取占位，扫描件与 OCR 留待后续安全评审。
- Streamlit 保持为薄展示层，不承载业务规则。
- 用户将每一大步的自主修复上限由 2 轮调整为 5 轮；达到 5 轮仍失败才停止。
- 第三步新增独立组合根 `bootstrap/container.py`，由它选择 Fake Adapter；业务工作流只接受 Port 注入，避免把 Fake 实现写死。

## Phase 4：真实 Policy QA RAG

- 采用 SQLite 本地持久化向量库，而不是强制依赖 Chroma；向量和元数据以 JSON 存储，查询时本地计算余弦相似度。
- 真实 Provider 选择 OpenAI Adapter，LLM 使用 Responses API，Embedding 使用 Embeddings API；Provider SDK 只存在于 `adapters/provider`。
- 默认 `FINANCE_COPILOT_PROVIDER=fake`。只有显式选择 `openai` 且 `OPENAI_API_KEY` 存在时才尝试真实 Provider。
- Embedding 与 LLM 均由 fallback adapter 包装；缺 Key、缺 SDK、构造失败或调用异常均自动切换 Fake，测试不依赖网络。
- 检索相关度阈值默认 0.55，低于阈值或没有来源时输出 `needs_review`。

## Phase 5：SQLite Repository 与 POC 记录持久化

- 使用一个通用 `poc_records` 表，以 `collection + record_id` 为主键保存 Test、Human Review 和 Failure Case 的 JSON payload；这样保持 RepositoryPort 简单并支持后续迁移。
- 所有连接都在操作结束时显式关闭，避免 Windows 文件句柄残留。
- `POCRecordService` 负责 Pydantic 类型转换和导出；Streamlit 只调用 Service 展示测试记录列表。
- JSON/CSV 导出覆盖三类记录，Markdown 汇总测试记录；SQLite 不承载审批动作。

## Phase 6：发票审核 v0.1 规则引擎

- 仅处理带强免责声明的合成 JSON，不接 OCR、税务验真或真实发票。
- 字段规范化和九类基础规则均为确定性 Python 逻辑，不使用 LLM；`today` 可注入以保证测试可重复。
- 状态优先级：字段缺失/格式错误 -> `needs_review`；明确超期、未来日期、抬头错误、非正金额或计算错误 -> `reject` 建议；重复或人工阈值 -> `needs_review`；警告阈值 -> `warning`；否则 `pass`。
- `reject` 只表示 Agent 建议退回并待人工确认；UI 显著声明不自动审批、不自动拒绝、不自动付款。
- 疑似重复以历史发票号码为 POC 判据，通过 RepositoryPort 查询并保存；Pilot 前需升级为更稳健的指纹策略。

## Phase 7：Human-in-the-loop

- 人工评审采用追加记录，不修改原 TestRecord 或 Agent 输出，以保证审计可追溯。
- 评审结论限定为确认、覆盖、无法判断；覆盖时必须填写覆盖后的建议。
- Streamlit 只收集评审输入并调用 `POCRecordService.submit_review()`，验证与持久化逻辑均位于 Service/Repository。

## Phase 8：冻结 baseline 与失败闭环

- 当前冻结集为 2 份制度、5 个制度问题和 3 个合成发票 JSON；manifest 使用相对路径与 SHA-256，便于复现实验。
- baseline 先验证检索来源与拒答门槛，再验证发票状态；答案关键词质量仍需人工评审，不伪造高质量指标。
- 所有未达预期结果自动写入 FailureCaseRecord，并关联同 ID 回归测试；测试与失败记录可重复 upsert。

## Phase 9：POC 指标与 Pilot Gate

- Policy QA 自动门槛为 85%，Invoice Audit 为 90%；高严重度未关闭失败是硬阻断。
- 人工复核未覆盖和 Fake Provider baseline 属于条件项；有硬阻断则 `NO_GO`，无阻断但有条件项则 `CONDITIONAL_GO`。
- Pilot Gate 仅基于冻结合成样本，不对真实业务外推；报告必须显式列出阻断原因和未验证项。

## Phase 10：无依据拒答机制增强

- `POLICY-005` 主因分类为 `RAG_WRONG_RETRIEVAL`，控制层表现为 `RAG_UNSUPPORTED_CLAIM`；不是测试预期歧义。
- 证据门禁同时要求向量分数达标、词面支持充分、问题中的城市/职级/金额条件被同一引用片段直接覆盖。
- 任一门槛失败时不调用 LLM，统一返回 `needs_review` 和固定无依据说明；不按 test_id 或样本文本写分支。
- 回归通过后保留 FailureCase 历史但将 `fix_status` 更新为 `fixed`，不删除失败记录。

## Phase 11：无依据拒答压力验证

- 在同一冻结问题集中增加跨城市、加班餐费、采购审批和教育费等无依据问题，不新增业务模块。
- 所有新增负例使用同一证据门禁，不增加按问题文本或 test ID 的特例。
- baseline 的可回答问题必须返回非人工复核结果；无依据问题必须返回 `needs_review`，防止过度拒答或漏拒答被记为通过。

## Phase 12：人工评审待办包

- 系统只生成 pending 队列，不自行创建或确认人工评审，避免伪造 Human-in-the-loop 覆盖率。
- 已有独立评审记录的测试从 pending 队列移除；原测试和 Agent 输出仍保持不变。
- 待办包导出 JSON、CSV、Markdown，供真实财务评审人后续处理。

## Phase 13A：模拟人工验收

> **Simulated review / 模拟评审 / 非真实财务专家确认**

- simulated_non_expert 记录与真实人工评审严格区分，Pilot Gate 和 pending 队列忽略模拟记录的完成状态。
- 模拟评审只验证追加记录、覆盖字段、证据不足分流和边界措辞，不代表财务专业判断。
- Agent 原始输出在评审前后以稳定哈希核对，不允许覆盖。

## Phase 13B：作品集交付包

- 本阶段只编辑 README、TODO 和 `docs/`，不修改 `src/**/*.py`；Python 源码指纹前后一致。
- 展示材料统一使用 `CONDITIONAL_GO`，不把模拟评审包装为真实专家背书。
- GitHub README 以业务问题、架构取舍、量化结果、失败边界和下一阶段 Gate 为主线，不宣称生产就绪。
- 面试材料同时提供 STAR、架构讲解、演示脚本、中英文简历、指标表和 Phase 14–19 路线图。

## Phase 13C：普通用户搜索式体验

- 制度问答默认检索全部合成制度，不再要求普通用户选择底层文档。
- Fake LLM Adapter 在证据门禁通过后进行确定性原句抽取，输出简洁答案；不联网、不绕过 evidence gate，也不按测试 ID 硬编码。
- Streamlit 默认只展示答案与一条直接来源；候选片段、相关度、Provider 状态和结构化记录放入折叠详情。
- 无依据问题继续返回 `needs_review`，候选文档明确标记为“不足以支持确定结论”，避免把错误检索包装成引用。
- 发票审核默认展示用户可读建议，完整 AgentResponse 保留在折叠审核记录中。
- Pilot Gate 继续保持 `CONDITIONAL_GO`；真实财务评审、真实 pending review 和模拟评审标记均未改变。
