# Web 与 API 验证报告

## 自动验收

- FastAPI 契约：3 项新测试通过，覆盖制度问答、请求持久化、发票审核、统一错误和 OpenAPI。
- Web：TypeScript、ESLint、Vitest 和 Next.js 16.2.9 production build 通过。
- E2E：Playwright 同时启动 FastAPI 与 Next.js，通过真实 HTTP 完成无依据提问、角色切换和复核队列检查；无页面异常。
- Python：`47 passed`，原有 pytest 全量回归通过。

> 环境提示：FastAPI TestClient 报告 Starlette 对 `httpx` 的弃用预警，不影响当前测试结果，待上游迁移到 `httpx2` 后跟进。

## 人工验收待办

- 3 名员工视角用户：完成有依据与无依据各一次查询。
- 2 名财务视角用户：分别完成确认与覆盖复核。
- 记录任务完成率、完成时间、风险提示理解率与复核追溯性。

未完成上述人工试用前，Gate 6 不得标记为完全通过。
