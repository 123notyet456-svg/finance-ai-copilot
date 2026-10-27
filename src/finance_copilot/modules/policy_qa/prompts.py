def build_answer_prompt(question: str, contexts: list[str]) -> str:
    joined = "\n\n".join(contexts)
    return f"只能根据以下合成制度上下文回答。\n上下文：\n{joined}\n\n问题：{question}"

