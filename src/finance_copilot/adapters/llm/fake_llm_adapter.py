"""确定性的本地回答器；不会进行网络调用。"""

import re


class FakeLLMAdapter:
    provider_name = "fake"

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            return "未提供可用于回答的上下文，建议人工复核。"

        context, marker, question = prompt.partition("\n\n问题：")
        if not marker:
            return "当前为本地模拟回答，请结合制度来源并进行人工复核确认。"

        context = context.removeprefix("只能根据以下合成制度上下文回答。\n上下文：\n")
        answer = self._best_supported_sentence(context, question)
        if answer:
            return answer
        return "当前证据未形成可直接回答的内容，建议查看制度来源并由人工确认。"

    @staticmethod
    def _best_supported_sentence(context: str, question: str) -> str | None:
        """从已通过证据门禁的上下文中提取最相关原句，供离线演示使用。"""
        question_terms = _bigrams(_normalize(question))
        asks_for_value = any(term in question for term in ("多少", "标准", "上限", "金额"))
        candidates = re.split(r"[。！？\n]+", context)
        scored: list[tuple[float, str]] = []
        for raw_sentence in candidates:
            sentence = re.sub(r"^[#>\-*\s]+", "", raw_sentence).strip()
            if not sentence or "非真实数据" in sentence or sentence.startswith("版本："):
                continue
            sentence_terms = _bigrams(_normalize(sentence))
            overlap = len(question_terms & sentence_terms)
            if overlap == 0:
                continue
            value_bonus = 2 if asks_for_value and re.search(r"\d", sentence) else 0
            scored.append((overlap + value_bonus, sentence))

        if not scored:
            return None
        best = max(scored, key=lambda item: item[0])[1]
        return f"{best}。"


def _normalize(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9.]", "", text).casefold()


def _bigrams(text: str) -> set[str]:
    return {text[index : index + 2] for index in range(max(0, len(text) - 1))}
