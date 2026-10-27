# Phase 10 构建报告

## 目标

关闭 `POLICY-005` 与无依据拒答缺陷，不新增业务模块、不硬编码 test ID、不降低测试标准。

## 根因

- 主因：`RAG_WRONG_RETRIEVAL`，字符桶向量把北京问题匹配到上海制度。
- 控制层失败：`RAG_UNSUPPORTED_CLAIM`，旧门禁只看向量分数，未检查条件是否被引用直接支持。
- 排除：`TEST_EXPECTATION_AMBIGUOUS`；测试预期明确。

## 修复

- 在现有 `policy_qa/rules.py` 增加 evidence support checker 和 retrieval confidence gate。
- 同一证据必须覆盖城市、职级、金额等关键条件。
- 使用向量相关度与证据词面支持度的几何平均，门槛仍保持 0.55。
- 证据不足时不调用 LLM，返回 `needs_review`。
- 回归成功后将历史失败标记为 `fixed`，不删除记录。

## 验收

- Phase 10 定向测试：通过。
- 全量 pytest：`36 passed`。
- 生产 test ID 硬编码扫描：干净。
- baseline：8/8，100%。
- Gate：`CONDITIONAL_GO`。

## 剩余条件

- 3 项应人工复核但尚未由真实评审人完成。
- 无 API Key，真实 Provider baseline 未执行，当前自动 fallback 到 Fake。

