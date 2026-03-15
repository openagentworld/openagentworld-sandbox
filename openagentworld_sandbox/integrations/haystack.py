"""
Haystack integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.haystack import CodeExecutorTool
    from haystack.agents import Agent

    tool = CodeExecutorTool(backend="docker")
    agent = Agent(tools=[tool])
"""

from typing import Optional, Any
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile



try:
    from haystack.tools import Tool
    HAYSTACK_AVAILABLE = True
except ImportError:
    HAYSTACK_AVAILABLE = False
    class Tool:  # type: ignore
        pass


class CodeExecutorTool(Tool):
    """
    Haystack tool for safe code execution.

    Args:
        backend: "local", "docker", "e2b", or "firecracker"
        timeout: seconds before execution is killed
        security: Optional SecurityProfile instance
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

        if not HAYSTACK_AVAILABLE:
            raise ImportError(
                "Haystack is not installed. "
                "Install with: pip install haystack-ai"
            )
        super().__init__(**kwargs)
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            language=language
        )

    def run(self, code: str) -> str:
        """Execute code and return output."""
        result = self._executor.run(code)

        if result.is_timeout:
            return f"[Timeout] Execution exceeded {self._executor.timeout}s limit."
        if result.error:
            return f"[Error]\n{result.error}"
        return result.output or "[No output]"
