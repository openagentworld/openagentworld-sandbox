"""
LangChain integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.langchain import LangChainSandbox
    from langchain.agents import initialize_agent

    sandbox_tool = LangChainSandbox(backend="docker")
    agent = initialize_agent(tools=[sandbox_tool], ...)
"""

from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile

try:
    from langchain_core.tools import BaseTool
    from langchain_core.callbacks import CallbackManagerForToolRun
    from typing import Optional
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseTool = object  # fallback


class LangChainSandbox(BaseTool):
    """
    Drop-in LangChain tool for safe code execution.
    Wraps SafeExecutor — swap backends without changing agent logic.

    Args:
        backend: "local", "docker", or "e2b"
        timeout: seconds before execution is killed
        security: SecurityProfile instance (default: SecurityProfile.DEFAULT)

    Example:
        tool = LangChainSandbox(backend="docker", security=SecurityProfile.STRICT)
        agent = initialize_agent(tools=[tool], llm=llm, ...)
    """

    name: str = "code_executor"
    description: str = (
        "Executes Python code safely in an isolated sandbox. "
        "Input should be valid Python code as a string. "
        "Returns stdout output or error messages."
    )

    # Pydantic requires class-level declaration for BaseTool subclasses
    _executor: SafeExecutor = None

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: SecurityProfile = None,
        **kwargs
    ):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. "
                "Install with: pip install langchain-core"
            )
        super().__init__(**kwargs)
        object.__setattr__(
            self, "_executor",
            SafeExecutor(backend=backend, timeout=timeout, security=security)
        )

    def _run(
        self,
        code: str,
        run_manager: Optional["CallbackManagerForToolRun"] = None
    ) -> str:
        """Synchronous execution — called by LangChain agent."""
        result = self._executor.run(code)

        if result.is_timeout:
            return "[Timeout] Execution exceeded time limit."
        if result.error and result.exit_code != 0:
            return f"[Error]\n{result.error}"
        return result.output or "[No output]"

    async def _arun(
        self,
        code: str,
        run_manager=None
    ) -> str:
        """Async execution — same logic, async-compatible."""
        return self._run(code)
