from finance_copilot.interfaces.streamlit.app import _markdown_title


def test_markdown_title_uses_first_level_one_heading() -> None:
    content = "# 合成差旅费管理制度\n\n> 合成样本 / 非真实数据"

    assert _markdown_title(content, "fallback") == "合成差旅费管理制度"


def test_markdown_title_falls_back_when_heading_is_missing() -> None:
    assert _markdown_title("普通正文", "sample_policy") == "sample_policy"
