"""
Agno integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.agno import CodeExecutor
    from agno import Agent

    executor = CodeExecutor(backend="docker")
    agent = Agent(executors=[executor])
"""

from typing import Optional
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile


try:
    from agno.tools import Tool
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Tool = object


class CodeExecutor(Tool if AGNO_AVAILABLE else object):
    """
    Agno tool for safe code execution.

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
        **kwargs
    ):
        if not AGNO_AVAILABLE:
            raise ImportError(
                "Agno is not installed. "
                "Install with: pip install agno"
            )
        super().__init__(**kwargs)
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            language=language
        )

    def execute(self, code: str) -> str:
        """Execute code and return output."""
        result = self._executor.run(code)
        
        if result.is_timeout:
            return f"[Timeout] Execution exceeded {self._executor.timeout}s limit."
        if result.error:
            return f"[Error]\n{result.error}"
        return result.output or "[No output]"
