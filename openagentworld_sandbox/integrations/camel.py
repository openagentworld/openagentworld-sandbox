"""
Camel (ChatGeML) integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.camel import CodeExecutionTool
    from camel.agents import RolePlayingAgent

    tool = CodeExecutionTool(backend="docker")
    agent = RolePlayingAgent(...)
"""

from typing import Optional, Any
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile



try:
    from camel.tools import BaseTool as CamelBaseTool
    CAMEL_AVAILABLE = True
except ImportError:
    CAMEL_AVAILABLE = False
    class CamelBaseTool:  # type: ignore
        pass


class CodeExecutionTool(CamelBaseTool):
    """
    Camel tool for safe code execution.

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

        if not CAMEL_AVAILABLE:
            raise ImportError(
                "Camel is not installed. "
                "Install with: pip install camel-ai"
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
