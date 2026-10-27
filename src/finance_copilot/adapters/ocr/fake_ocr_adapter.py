from pathlib import Path


class FakeOCRAdapter:
    def extract_text(self, path: Path) -> str:
        return f"合成 OCR 结果：{path.name}（非真实识别结果）"

