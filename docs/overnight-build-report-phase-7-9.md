# Phase 7–9 构建报告

> 全部数据均为合成样本 / 非真实数据 / 不可报销。

## Phase 7：Human-in-the-loop

- 结果：首轮通过，`27 passed`。
- 实现：追加式人工评审、确认/覆盖/无法判断、测试/评审/失败历史列表。
- 约束：不修改原 Agent 输出；Streamlit 只调用 Service。

## Phase 8：冻结 baseline 与失败闭环

- 结果：首轮通过，`29 passed`。
- 冻结集：2 份制度、5 个制度问题、3 个合成发票；6 个文件 SHA-256 全部匹配。
- baseline：7/8 通过，87.5%；`POLICY-005` 自动生成 `FAIL-POLICY-005`。
- 导出：JSON、CSV、Markdown 已生成到 `data/exports/baseline/`。

## Phase 9：POC 指标与 Pilot Gate

- 结果：首轮通过，`31 passed`。
- 结论：`NO_GO`。
- 阻断：Policy QA 80% 低于 85%；存在 1 个未关闭高严重度失败。
- 条件：3 项应人工复核但完成 0 项；真实 Provider 因缺 Key 未执行，自动 fallback 到 Fake。

## 下一轮建议

优先修复无依据拒答与低相关度校准，补齐人工复核，再扩充冻结集。真实 Provider 只能在受控合成数据、环境变量 Key 和 Fake fallback 保持有效的前提下运行。

## 最终整体验收

- pytest：`31 passed`。
- Streamlit：HTTP 启动探针返回 200。
- Provider 边界：modules 与 interfaces 无 Provider SDK 导入。
- Key 安全：未发现硬编码 Key；当前环境无 Key，fallback 正常。
- 冻结数据：6 个文件哈希全部匹配。
- 持久化结果：8 条测试、1 条失败、0 条人工评审。
- Pilot Gate：`NO_GO`，总体通过率 87.50%。
