# 前端先行产品蓝图

## 生命周期

`Vision -> PRD -> UX/UI -> Experience Contract -> Architecture -> Implementation -> Validation -> Iteration`

每一层都必须通过 Gate 才进入下一层；体验契约同时约束前端 Mock 和 FastAPI。

## 角色与任务

- 员工：查到有直接引用的制度答案，并能识别无依据结果。
- 财务复核人：集中处理低置信、冲突和高风险结果，追加可审计决定。

## 当前范围

- 制度问答、引用、拒答、查询详情和复核闭环。
- 发票字段预览与确定性规则；OCR/Vision 明确为 Mock。
- 制度库、验证指标和 Pilot Gate 只读视图。

不包含：真实鉴权、多租户、ERP 写入、税务验真、自动审批/拒绝/付款。

## Gate 状态

- Gate 0–4：已用页面、状态矩阵、OpenAPI 和分层架构落地。
- Gate 5：制度问答与追加式复核已有端到端链路。
- Gate 6：工程自动验证已覆盖；3 名员工视角与 2 名财务视角的真实可用性试用仍待执行。
