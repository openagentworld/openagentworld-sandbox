"""
AutoGen integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.autogen import AutoGenSandbox
    from autogen_agentchat.agents import AssistantAgent

    executor = AutoGenSandbox(backend="docker")
    agent = AssistantAgent(name="coder", code_executor=executor)
"""

from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile

try:
    from autogen_core.code_executor import (
        CodeExecutor,
        CodeBlock,
        CodeResult,
    )
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    CodeExecutor = object  # fallback base


class AutoGenSandbox(CodeExecutor):
    """
    Drop-in replacement for AutoGen's built-in code executors.
    Wraps SafeExecutor so you can swap backends without touching agent logic.

    Args:
        backend: "local", "docker", or "e2b"
        timeout: seconds before execution is killed
        security: SecurityProfile instance (default: SecurityProfile.DEFAULT)

    Example:
        executor = AutoGenSandbox(backend="docker", security=SecurityProfile.STRICT)
    """

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: SecurityProfile = None,
        **kwargs
    ):
        if not AUTOGEN_AVAILABLE:
            raise ImportError(
                "AutoGen is not installed. "
                "Install with: pip install autogen-agentchat"
            )
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            **kwargs
        )

    async def execute_code_blocks(
        self,
        code_blocks: list,
        cancellation_token=None
    ) -> "CodeResult":
        """
        AutoGen calls this with a list of CodeBlock objects.
        We execute each block and return a combined CodeResult.
        """
        outputs = []
        exit_code = 0

        for block in code_blocks:
            # Only execute Python blocks for now
            if block.language.lower() not in ("python", "py", ""):
                outputs.append(f"# Skipped non-python block: {block.language}")
                continue

            result = self._executor.run(block.code)

            if result.output:
                outputs.append(result.output)
            if result.error:
                outputs.append(f"[stderr]: {result.error}")
            if result.is_timeout:
                outputs.append("[agent-sandbox]: Execution timed out.")
                exit_code = 1
            if result.exit_code != 0:
                exit_code = result.exit_code

        return CodeResult(
            exit_code=exit_code,
            output="\n".join(outputs)
        )

    async def restart(self) -> None:
        """AutoGen calls this to reset the executor state."""
        pass
