from finance_copilot.core.schemas.common import AgentRecommendation, AgentResponse


def test_common_schema_can_be_instantiated() -> None:
    response = AgentResponse(
        module="policy_qa",
        agent_recommendation=AgentRecommendation.NEEDS_REVIEW,
        summary="合成测试",
    )
    assert response.request_id
    assert response.requires_human_review is True
    assert response.estimated_cost == 0

