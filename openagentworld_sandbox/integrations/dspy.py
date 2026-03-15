"""
DSPy integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.dspy import CodeExecutorModule
    import dspy

    executor = CodeExecutorModule(backend="docker")
    code = dspy.Predict(executor)
"""

from typing import Optional, Any
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile


try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False


class CodeExecutorModule:
    """
    DSPy module for safe code execution.

    Args:
        backend: "local", "docker", "e2b", or "firecracker"
        timeout: seconds before execution is killed
        security: SecurityProfile instance
        language: "python", "javascript", "bash"
    """

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        **kwargs: Any
    ):
        if not DSPY_AVAILABLE:
            raise ImportError(
                "DSPy is not installed. "
                "Install with: pip install dspy"
            )
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            language=language
        )

    def forward(self, code: str) -> str:
        """Execute code and return output."""
        result = self._executor.run(code)

        if result.is_timeout:
            return f"[Timeout] Execution exceeded {self._executor.timeout}s limit."
        if result.error:
            return f"[Error]\n{result.error}"
        return result.output or "[No output]"
