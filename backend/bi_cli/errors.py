"""BI CLI 内部异常定义。"""

from dataclasses import dataclass

from .models import BiCliExitCode


@dataclass(frozen=True)
class BiCliFailure:
    """异常转换为 CLI 失败输出时使用的强类型详情。

    Attributes:
        exit_code: CLI 进程应该返回的退出码。
        error_code: 供 Agent 判断错误类别的稳定代码。
        message: 面向 Agent 或最终用户的中文错误说明。
        retryable: 使用相同参数是否允许再次尝试。
    """

    exit_code: BiCliExitCode
    error_code: str
    message: str
    retryable: bool = False


class BiCliError(RuntimeError):
    """携带稳定退出码和错误代码的 BI CLI 异常。"""

    def __init__(self, failure: BiCliFailure) -> None:
        """创建 BI CLI 异常。

        Args:
            failure: 需要向 Agent 返回的结构化失败详情。
        """
        super().__init__(failure.message)
        self.failure = failure
