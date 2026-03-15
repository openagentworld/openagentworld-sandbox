"""
Smolagents integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.smolagents import CodeAgent
    from smolagents import HuggingFaceModel

    agent = CodeAgent(tools=[], model=HuggingFaceModel())
"""

from typing import Optional, Any, List
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile


try:
    from smolagents import Tool
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    class Tool:  # type: ignore
        pass


class CodeExecutorTool(Tool):
    """
    Smolagents tool for safe code execution.
    Wraps SafeExecutor for use in smolagents.

    Args:
        backend: "local", "docker", "e2b", or "firecracker"
        timeout: seconds before execution is killed
        security: Optional SecurityProfile instance
        language: "python", "javascript", "bash"
    """

    name: str = "code_executor"
    description: str = "Executes Python code safely in an isolated sandbox."
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "The Python code to execute"}
        },
        "required": ["code"]
    }

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        **kwargs
    ):
        if not SMOLAGENTS_AVAILABLE:
            raise ImportError(
                "Smolagents is not installed. "
                "Install with: pip install smolagents"
            )
        super().__init__(**kwargs)
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
