"""
CrewAI integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.crewai import CodeExecutorTool
    from crewai import Agent, Task, Crew

    tool = CodeExecutorTool(backend="docker", security=SecurityProfile.STRICT)
    coder = Agent(role="Coder", tools=[tool])
"""

from typing import Optional
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile


try:
    from crewai.tools import BaseTool as CrewBaseTool
    from pydantic import BaseModel, Field
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    CrewBaseTool = object
    BaseModel = object
    Field = lambda **kw: None


class CodeExecutorTool:
    """
    CrewAI tool for safe code execution.
    Wraps SafeExecutor for use in CrewAI agents.

    Args:
        backend: "local", "docker", "e2b", or "firecracker"
        timeout: seconds before execution is killed
        security: SecurityProfile instance
        language: "python", "javascript", "bash"

    Example:
        tool = CodeExecutorTool(backend="docker")
        agent = Agent(role="Coder", tools=[tool])
    """

    name: str = "code_executor"
    description: str = "Executes Python code safely in an isolated sandbox. Input should be valid Python code."

    class ToolArgs:
        code: str = Field(description="The Python code to execute")

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        **kwargs
    ):
        if not CREWAI_AVAILABLE:
            raise ImportError(
                "CrewAI is not installed. "
                "Install with: pip install crewai"
            )
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            language=language
        )

    def _run(self, code: str) -> str:
        """Execute code and return output."""
        result = self._executor.run(code)
        
        if result.is_timeout:
            return f"[Timeout] Execution exceeded {self._executor.timeout}s limit."
        if result.error:
            return f"[Error]\n{result.error}"
        return result.output or "[No output]"
