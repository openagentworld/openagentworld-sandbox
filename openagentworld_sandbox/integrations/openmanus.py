"""
OpenManus integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.openmanus import OpenManusExecutor
"""

from typing import Optional
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile


class OpenManusExecutor:
    """
    OpenManus executor for safe code execution.
    Drop-in replacement for OpenManus code execution.

    Args:
        backend: "local", "docker", "e2b", or "firecracker"
        timeout: seconds before execution is killed
        security: SecurityProfile instance
        language: "python", "javascript", "bash"
    """

    def __init__(
        self,
        backend: str = "docker",
        timeout: int = 30,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        **kwargs
    ):
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            language=language
        )

    def execute(self, code: str) -> dict:
        """Execute code and return result dict."""
        result = self._executor.run(code)
        
        return {
            "success": result.exit_code == 0,
            "output": result.output,
            "error": result.error,
            "is_timeout": result.is_timeout,
            "exit_code": result.exit_code
        }

    async def execute_async(self, code: str) -> dict:
        """Async execute code."""
        result = await self._executor.run_async(code)
        
        return {
            "success": result.exit_code == 0,
            "output": result.output,
            "error": result.error,
            "is_timeout": result.is_timeout,
            "exit_code": result.exit_code
        }
