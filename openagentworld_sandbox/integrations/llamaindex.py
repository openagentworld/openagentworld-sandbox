"""
LlamaIndex integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.llamaindex import CodeExecutionTool
    from llama_index.agents import AgentRunner

    tool = CodeExecutionTool(backend="docker")
    agent = AgentRunner(tools=[tool])
"""

from typing import Optional
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile


try:
    from llama_index.tools import BaseTool as LlamaBaseTool
    from llama_index.types import ToolMetadata
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    LlamaBaseTool = object
    ToolMetadata = object


class CodeExecutionTool:
    """
    LlamaIndex tool for safe code execution.
    Wraps SafeExecutor for use in LlamaIndex agents.

    Args:
        backend: "local", "docker", "e2b", or "firecracker"
        timeout: seconds before execution is killed
        security: SecurityProfile instance
        language: "python", "javascript", "bash"
    """

    name: str = "code_executor"
    description: str = "Executes Python code safely in an isolated sandbox."

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        **kwargs
    ):
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex is not installed. "
                "Install with: pip install llama-index"
            )
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            language=language
        )

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description=self.description
        )

    def _call(self, input: str) -> str:
        """Execute code and return output."""
        result = self._executor.run(input)
        
        if result.is_timeout:
            return f"[Timeout] Execution exceeded {self._executor.timeout}s limit."
        if result.error:
            return f"[Error]\n{result.error}"
        return result.output or "[No output]"
