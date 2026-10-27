"""应用级异常。"""


class FinanceCopilotError(Exception):
    """所有可预期业务异常的基类。"""


class FileValidationError(FinanceCopilotError):
    """文件类型或大小不符合约束。"""


class DocumentProcessingError(FinanceCopilotError):
    """文档无法被安全解析。"""

