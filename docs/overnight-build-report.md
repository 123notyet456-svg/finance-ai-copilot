# Finance AI Copilot v0.1 Overnight Build Report

构建日期：2026-06-29（Asia/Shanghai）

## 1. 完成的大步

1. 项目骨架与可运行空壳：完成。
2. 本地文件处理与 POC 测试记录框架：完成。
3. 轻量 Policy QA RAG 骨架：完成。

按照约束，第三大步验收通过后已停止功能开发，没有开始第四步或扩展新模块。

## 2. 分步验收结果

| 大步 | 结果 | 测试结果 | 修复轮次 | 关键证据 |
|---|---|---:|---:|---|
| 第一步 | 通过 | 4 passed | 1 | 项目可安装，公共 Schema、Fake Adapter、两个 Service、Streamlit 入口均可导入 |
| 第二步 | 通过 | 7 passed | 0 | TXT/Markdown 读取、SHA-256、评测 Schema、JSON/CSV/Markdown 导出与样本免责声明检查通过 |
| 第三步 | 通过 | 11 passed | 0 | 文档切分、Fake 检索、结构化来源、无依据回退和 Port 注入检查通过 |

第一步首轮验收发现两项基础问题：Fake LLM 文案未直接包含“人工”二字；普通 Python 进程在项目未安装时无法发现 `src` 包。第 1 轮修复后，补充明确人工复核文案，并以 editable 模式安装本地项目，复验通过。

用户将单个大步的自主修复上限从 2 轮调整为 5 轮；本次没有步骤触及该上限。

## 3. 执行的主要命令

```powershell
python --version
python -m pip install -e . --no-deps
python -m pytest -q
python -m compileall -q src app.py
rg -n -i 'import (openai|anthropic)|from (openai|anthropic)|qwen|deepseek|claude' src
rg -n 'Fake(Embedding|VectorStore|LLM)Adapter' src/finance_copilot/modules
python -m streamlit run app.py --server.headless=true --server.port=8765
```

此外执行了本地样本文档读取、SHA-256、端到端导入/检索，以及数据免责声明和 Docs 完整性扫描。

## 4. pytest 结果

最终结果：`11 passed in 0.79s`。

测试覆盖：

- 公共 AgentResponse Schema。
- Fake LLM、Embedding、OCR、Vector Store、Repository。
- Policy QA 与 Invoice Audit Service。
- TXT/Markdown 加载、文件校验、SHA-256、临时路径。
- TestRecord、HumanReviewRecord、FailureCaseRecord。
- JSON、CSV 与 Markdown 报告导出。
- 文档切分、轻量 RAG 检索、有来源回答与无来源回退。

## 5. 失败与原因

最终无未解决失败。第一步首次验收的两项失败均属于本地测试/安装问题，已在允许的第 1 轮自主修复中解决。

## 6. 自主修复记录

- 将 Fake LLM 输出改为明确要求“人工复核并最终确认”。
- 执行 `python -m pip install -e . --no-deps`，验证标准 Python 进程与 Streamlit 均可导入 `src` 包。

## 7. 已可运行功能

- 可安装并启动的 Python/Streamlit 项目。
- 两个 Agent 模块的 Service 骨架与公共 Pydantic 输出协议。
- 合成制度文档读取、校验、哈希和切分。
- 通过 Port/Adapter 完成轻量文档导入、向量检索、Fake 回答和来源回传。
- 无文档时返回稳定的人工复核 Fallback。
- 合成发票 Fake 审核结果。
- 测试记录、人工评审、失败案例模型，以及 JSON/CSV/Markdown 导出。
- Streamlit 首页可选择合成制度、输入问题并展示回答、sources 和人工复核标记。

最终启动探针访问 `http://127.0.0.1:8765` 返回 HTTP 200；探针结束后测试进程已关闭。

## 8. Fake 实现

- `FakeLLMAdapter`：返回确定性模拟说明。
- `FakeEmbeddingAdapter`：本地字符桶向量，不代表语义模型质量。
- `FakeVectorStoreAdapter`：进程内余弦排序，不是 Chroma。
- `FakeOCRAdapter`：只返回说明文本，不执行 OCR。
- `FakeRepository`：进程内字典存储，不是 SQLite。
- 发票审核仅为占位规则与结构化演示，不执行真实税务验真或复杂审核。

## 9. 后续可替换的真实能力

组合根 `src/finance_copilot/bootstrap/container.py` 可以在不修改业务工作流的情况下替换：

- `LLMPort` -> 经安全评审的真实 LLM Adapter。
- `EmbeddingPort` -> 真实 Embedding Adapter。
- `VectorStorePort` -> Chroma 或其他向量库 Adapter。
- `OCRPort` -> 经隐私评审的 OCR/Vision Adapter。
- `RepositoryPort` -> SQLite/SQLAlchemy Adapter。

本轮没有接入、安装或调用任何真实外部 Provider API。

## 10. 启动方式

```powershell
cd "D:\AI实战项目\Finance AI Copilot"
python -m pip install -e ".[dev]"
python -m pytest
streamlit run app.py
```

浏览器访问 Streamlit 输出的本地地址，通常为 `http://localhost:8501`。

## 11. 明天人工验收步骤

1. 运行 `python -m pytest`，确认 11 项测试通过。
2. 运行 `streamlit run app.py`，确认首页与风险边界声明显示正常。
3. 选择 `sample_policy_travel.md`，询问“上海普通员工住宿标准是多少？”。
4. 确认页面展示模拟回答、至少一条 source 和 `requires_human_review` 字段。
5. 检查无文档工作流测试是否稳定返回 needs_review Fallback。
6. 运行合成发票 Fake 审核，确认没有自动审批、拒绝或付款措辞。
7. 抽查 `data/poc_datasets`，确认所有样本均显著标注“合成样本 / 非真实数据 / 不可报销”。
8. 检查 `docs/DECISIONS.md` 与 `TODO.md`，确认边界、决策和未完成事项可追溯。

## 12. 下一步建议

下一轮先由财务评审人确认合成制度与测试问题的业务口径，再扩充冻结测试集和评测指标。真实 LLM、Embedding、OCR、Chroma、SQLite 或 FastAPI 应作为独立工作阶段，在隐私、安全、成本、重试和数据保留设计完成后接入；本轮不继续实施。

## Phase 4–6 续建记录（2026-06-29）

- Phase 4：真实 Provider Adapter + Fake fallback + SQLite 持久化 RAG；第 1 轮修复后 `17 passed`。
- Phase 5：SQLite POC Repository、三类记录与导出；第 1 轮清理警告后 `19 passed`。
- Phase 6：合成发票字段规范化与九类确定性规则；首轮 `25 passed`。
- 当前无 API Key，真实 Provider 未调用，Embedding/LLM 自动 fallback 到 Fake。
- 用户授权继续 Phase 7–9，每个 Phase 继续独立验收并更新本文档。

### Phase 7（构建中）

- 新增追加式人工评审 Service 和 Streamlit 测试/评审/失败历史视图。
- 原 Agent 输出保持不可变；覆盖评审保存为独立 HumanReviewRecord。
- 验收：首轮通过，`27 passed`，Streamlit 业务逻辑扫描通过。

### Phase 8（构建中）

- 新增冻结数据集 SHA-256 manifest、8 项合成 baseline 执行器和失败案例自动落库。
- baseline 结果支持 JSON、CSV、Markdown 导出。
- 验收：首轮通过，`29 passed`；冻结 manifest 共 6 个文件且哈希全部匹配。

### Phase 9（构建中）

- 新增模块指标、人工复核覆盖、Provider fallback 识别与 Pilot Gate 生成器。
- 当前预期结论为 `NO_GO`：Policy QA 4/5，通过率 80%，且有 1 个未关闭高严重度失败。
- 验收：首轮通过，`31 passed`；正式 Pilot Gate 结论为 `NO_GO`。
- Phase 7–9 已完成，详细结果见 `docs/overnight-build-report-phase-7-9.md`。

## 最终续建验收（Phase 4–9）

- 全量 pytest：`31 passed`。
- Streamlit：本地 HTTP 探针返回 200，结束后测试进程已关闭。
- 冻结 baseline：8 项中 7 项通过，总体 87.50%。
- 持久化：8 条测试记录、1 条失败案例、0 条人工评审。
- Provider：当前无 API Key，真实调用未发生，LLM/Embedding 自动 fallback 到 Fake。
- Pilot Gate：`NO_GO`；Policy QA 80% 低于 85% 门槛，且 `FAIL-POLICY-005` 尚未关闭。
- 项目仍不自动审批、不自动拒绝、不自动付款，所有数据均为合成样本。

## Phase 10（构建中）

- 根因：高分但错误的跨城市检索，分类为 `RAG_WRONG_RETRIEVAL` / `RAG_UNSUPPORTED_CLAIM`。
- 修复：新增通用 evidence support checker 与 retrieval confidence gate；证据不直接支持全部条件时不调用 LLM，返回 `needs_review`。
- 失败记录采用状态关闭，不删除历史案例。
- 验收：全量 `36 passed`，冻结 baseline 8/8；`FAIL-POLICY-005` 标记为 fixed。
- Pilot Gate 已从 `NO_GO` 更新为 `CONDITIONAL_GO`。

## Phase 11（构建中）

- 冻结制度问题从 5 项扩展到 10 项，其中 6 项为通用无依据压力样本。
- 新增城市错配、加班餐费、采购审批与教育费拒答回归，不新增业务模块。

## Phase 12（构建中）

- 新增 pending human review 查询与 JSON/CSV/Markdown 待办包。
- 系统不伪造人工评审；待办完成前 Gate 保持 Conditional GO。
- 验收：全量 `38 passed`，Streamlit HTTP 200。
- 扩展 baseline：13/13；待人工评审 8 项；未关闭失败 0。
- 详细交接见 `docs/overnight-build-report-phase-11-12.md`。

## Phase 13A：模拟人工验收

> **Simulated review / 模拟评审 / 非真实财务专家确认**

- Reviewer：Demo Finance Reviewer；类型 `simulated_non_expert`；范围 `process validation only`。
- 共模拟评审 8 项：confirmed 7、needs_more_info 0、cannot_determine 1、overridden 0。
- 未发现越权输出；异常发票因缺少原始来源证据标记 cannot_determine。
- 模拟评审以独立 HumanReviewRecord 追加，Agent 原始输出哈希前后一致。
- 模拟记录不清空真实 pending 队列、不计入真实评审覆盖率。
- Pilot Gate 保持 `CONDITIONAL_GO`。
- 详细报告：`docs/simulated-human-review-report.md`。
- 最终验收：`41 passed`；Streamlit HTTP 200；模拟记录 8；Agent 输出未改变；真实 pending 仍为 8。

## Phase 13B：作品集交付包

- 更新 GitHub/面试官导向 README。
- 新增 STAR 面试故事、面试版架构讲解、中英文简历、项目指标和 Phase 14–19 路线图。
- 完善 3–5 分钟演示脚本并重构 TODO 状态。
- pytest：41 passed。
- Pilot Gate：保持 `CONDITIONAL_GO`。
- 真实 pending review：保持 8 项。
- 历史失败：`FAIL-POLICY-005` 保留且为 fixed。
- simulated review：8 项，全部保持 simulated_non_expert 标记。
- Python 源码指纹前后一致，核心业务逻辑未修改。

## Phase 13C：普通用户体验改造

- 制度问答改为搜索式入口，自动检索当前全部合成制度。
- 有依据问题直接返回制度原句；“上海出差住宿标准是什么？”返回普通员工每晚 500 元、总监级员工每晚 800 元。
- 原始来源 JSON、相关度和 Provider 状态移入折叠技术详情；无依据场景仍进入人工复核。
- 发票审核结果由原始 JSON 改为用户可读建议，完整结构化记录仍可展开查看。
- 新增 Fake 回答抽取和 Markdown 标题展示测试；首轮全量回归发现旧 fallback 测试依赖“人工复核”措辞，第 1 轮兼容修复后通过。
- pytest：44 passed；Streamlit：HTTP 200，浏览器已验证正常回答与无依据拒答两条流程。
- Provider：未调用真实外部 API，Fake fallback 保留；Pilot Gate 保持 `CONDITIONAL_GO`。
