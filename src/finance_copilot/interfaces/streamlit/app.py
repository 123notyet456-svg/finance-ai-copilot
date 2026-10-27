"""薄 UI：只收集输入、调用 Service、展示结构化结果。"""

from pathlib import Path

import streamlit as st

from finance_copilot.bootstrap.container import (
    build_evaluation_service,
    build_invoice_audit_service,
    build_pilot_gate_service,
    build_policy_qa_service,
)
from finance_copilot.core.document_processing import load_markdown
from finance_copilot.modules.policy_qa.schemas import PolicyDocument


def _show_response(response: object) -> None:
    labels = {
        "pass": "未发现明显异常",
        "warning": "存在提示项",
        "reject": "建议退回人工核查",
        "needs_review": "需要人工复核",
    }
    recommendation = response.agent_recommendation.value
    st.subheader(labels.get(recommendation, "审核建议"))
    st.write(response.summary)
    if response.findings:
        st.markdown("\n".join(f"- {finding}" for finding in response.findings))
    st.caption("以上是 Agent 辅助建议，不是最终审批、拒绝或付款动作。")
    with st.expander("查看完整审核记录"):
        st.json(response.model_dump(mode="json"), expanded=False)


def _markdown_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return fallback


def main() -> None:
    st.set_page_config(page_title="Finance AI Copilot v0.1 POC", layout="wide")
    st.title("Finance AI Copilot")
    st.caption("查询财务制度，获取有来源、可追溯的辅助答案。当前使用合成制度演示。")

    policy_tab, invoice_tab, history_tab, metrics_tab = st.tabs(
        ["制度问答", "发票审核", "测试历史", "POC 指标"]
    )
    with policy_tab:
        sample_dir = Path("data/poc_datasets/policy_qa")
        sample_paths = sorted(sample_dir.glob("sample_policy_*.md"))
        with st.form("policy_search"):
            question = st.text_input(
                "查询财务制度",
                "上海出差住宿标准是什么？",
                placeholder="例如：上海出差住宿标准是什么？",
            )
            submitted = st.form_submit_button("搜索", type="primary")

        if submitted:
            service = build_policy_qa_service()
            documents = []
            for path in sample_paths:
                content = load_markdown(path)
                documents.append(
                    PolicyDocument(
                        document_id=path.stem,
                        title=_markdown_title(content, path.stem),
                        content=content,
                    )
                )
            service.ingest_documents(documents)

            try:
                response = service.answer_question(question)
            except ValueError:
                st.warning("请输入需要查询的制度问题。")
            else:
                st.subheader("答案")
                if response.requires_human_review:
                    st.warning(response.summary)
                    st.caption("现有制度依据不足，本结果需要人工确认。")
                else:
                    st.write(response.summary)

                if response.sources:
                    cited_titles = [response.sources[0].title]
                    source_prefix = (
                        "候选来源（不足以支持确定结论）："
                        if response.requires_human_review
                        else "来源："
                    )
                    st.caption(source_prefix + "；".join(f"《{title}》" for title in cited_titles))

                with st.expander("查看依据与技术详情"):
                    for index, source in enumerate(response.sources, start=1):
                        score = f" · 相关度 {source.score:.0%}" if source.score is not None else ""
                        st.markdown(f"**{index}. 《{source.title}》{score}**")
                        st.write(source.excerpt)
                    st.divider()
                    st.caption(f"Agent 建议：{response.agent_recommendation.value}")
                    st.caption(f"需要人工复核：{'是' if response.requires_human_review else '否'}")
                    st.json(service.runtime_status(), expanded=False)

        with st.expander("当前演示数据范围"):
            st.write("、".join(_markdown_title(load_markdown(path), path.stem) for path in sample_paths))
            st.caption("全部为合成样本 / 非真实数据 / 不可用于报销或真实业务决策。")

    with invoice_tab:
        st.info("以下结果仅为 Agent 建议，不是最终审批、拒绝或付款动作。")
        invoice_number = st.text_input("合成发票号码", "SYNTHETIC-UI-001")
        invoice_date = st.date_input("合成开票日期")
        buyer_name = st.text_input("合成购买方", "虚构科技有限公司")
        seller_name = st.text_input("合成销售方", "合成服务有限公司")
        amount = st.number_input("合成金额", min_value=0.0, value=100.00)
        tax = st.number_input("合成税额", min_value=0.0, value=6.00)
        total = st.number_input("合成价税合计", min_value=0.0, value=106.00)
        if st.button("运行发票规则审核"):
            _show_response(
                build_invoice_audit_service().audit_invoice(
                    {
                        "invoice_number": invoice_number,
                        "invoice_date": invoice_date.isoformat(),
                        "buyer_name": buyer_name,
                        "seller_name": seller_name,
                        "amount": str(amount),
                        "tax": str(tax),
                        "total_amount": str(total),
                    }
                )
            )

    with history_tab:
        st.caption("历史记录只用于 POC 测试追溯，不代表审批结果。")
        evaluation_service = build_evaluation_service()
        records = evaluation_service.list_tests()
        reviews = evaluation_service.list_reviews()
        failures = evaluation_service.list_failures()
        pending_reviews = evaluation_service.list_pending_human_reviews()
        tests_view, reviews_view, failures_view = st.tabs(["测试记录", "人工评审", "失败案例"])
        with tests_view:
            st.metric("待人工评审", len(pending_reviews))
            if pending_reviews:
                st.dataframe([record.model_dump(mode="json") for record in pending_reviews])
            if records:
                st.dataframe([record.model_dump(mode="json") for record in records])
                test_id = st.selectbox("待评审测试", [record.test_id for record in records])
                reviewer = st.text_input("评审人", "POC Reviewer")
                decision = st.selectbox(
                    "评审结论", ["confirmed", "overridden", "unable_to_determine"]
                )
                overridden = st.text_input("覆盖后的建议（仅 overridden 必填）")
                notes = st.text_area("人工备注")
                if st.button("追加人工评审记录"):
                    evaluation_service.submit_review(
                        test_id=test_id,
                        reviewer=reviewer,
                        review_decision=decision,
                        notes=notes,
                        overridden_recommendation=overridden or None,
                    )
                    st.success("人工评审已追加，原 Agent 输出未修改。")
            else:
                st.info("暂无持久化测试记录。")
        with reviews_view:
            st.dataframe([record.model_dump(mode="json") for record in reviews])
        with failures_view:
            st.dataframe([record.model_dump(mode="json") for record in failures])

    with metrics_tab:
        evaluation_service = build_evaluation_service()
        gate = build_pilot_gate_service().evaluate(
            evaluation_service.list_tests(),
            evaluation_service.list_failures(),
            evaluation_service.list_reviews(),
        )
        st.metric("Pilot Gate", gate.recommendation)
        st.metric("总体通过率", f"{gate.overall_pass_rate:.2%}")
        st.dataframe([metric.model_dump(mode="json") for metric in gate.modules])
        st.write("阻断原因", gate.blocking_reasons)
        st.write("条件与未验证项", gate.conditions)

    st.caption(
        "风险边界：系统仅提供辅助分析和审核建议；不自动审批、不自动拒绝、不自动付款；"
        "高风险结果必须人工复核。"
    )


if __name__ == "__main__":
    main()
