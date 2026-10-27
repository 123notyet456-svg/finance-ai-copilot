# Finance AI Copilot：3–5 分钟演示脚本

## 0:00–0:30｜开场：项目定位

“这是一个财务 AI 的 POC 价值验证项目，不是自动审批系统。它解决两个高频场景：财务制度重复咨询和合成发票基础审核。我的重点不是展示一次成功回答，而是展示 AI 如何被测试、拒答、人工复核，并最终形成 Pilot Gate。”

强调安全边界：仅使用合成数据；不自动审批、不自动拒绝、不自动付款。

## 0:30–1:00｜Dashboard 与架构

启动：

```powershell
streamlit run app.py
```

快速展示四个页面：制度问答、发票审核、测试历史、POC 指标。说明 Streamlit 是薄界面，业务逻辑在 Service/Workflow，Provider SDK 只在 Adapter。

## 1:00–1:40｜Policy QA 正常问题

选择 `sample_policy_travel.md`，输入：

> 普通员工去上海出差的住宿标准是多少？

展示回答、引用片段、相关度和 `requires_human_review=false`。说明检索结果不仅看向量分数，还会检查城市、职级、金额等条件是否被证据直接支持。

## 1:40–2:15｜无依据问题

输入：

> 北京地区普通员工住宿标准是多少？

展示 `needs_review`，指出当前制度只有上海标准。解释历史缺陷 `FAIL-POLICY-005`：错误检索曾把北京问题匹配到上海制度；修复后失败历史没有删除，而是标记 fixed 并保留为回归测试。

## 2:15–2:50｜合成发票审核

展示正常或边界合成发票 JSON。说明日期、抬头、金额、价税、阈值、必填和重复检查由确定性规则完成。

强调：界面中的 `reject` 是“建议退回、待人工确认”，不是系统已经拒绝。

## 2:50–3:25｜Human-in-the-loop

打开测试历史和待人工评审队列。展示模拟评审报告：

> **Simulated review / 模拟评审 / 非真实财务专家确认**

说明 8 项流程演练中 confirmed 7、cannot_determine 1；模拟记录没有覆盖 Agent 输出，也没有清空真实 pending 队列。异常发票因没有原始凭证被保守标记为 cannot_determine。

## 3:25–4:05｜Pilot Gate 与测试结果

展示：

- pytest：44 passed
- baseline：13/13
- 未关闭高严重度失败：0
- Pilot Gate：`CONDITIONAL_GO`

解释为什么不是 GO：真实财务评审尚未完成，真实 Provider 的质量、延迟和成本尚未受控验证，冻结集规模仍有限。

## 4:05–4:30｜结尾：下一阶段

“下一步不是盲目加功能，而是按 Gate 缺口推进：真实财务专家评审、受控 Provider baseline、扩展冻结测试集，再考虑 OCR/Vision、FastAPI 和小范围 Pilot。这体现了我如何把 AI 原型变成可验证、可追溯、可治理的业务 POC。”

## 演示前检查

```powershell
python -m pytest
python scripts/run_poc_baseline.py
streamlit run app.py
```

- 确认使用合成数据。
- 确认 Gate 为 `CONDITIONAL_GO`，不要口述为 GO。
- 确认模拟评审声明清晰可见。
- 不展示任何 API Key 或本地敏感配置。
