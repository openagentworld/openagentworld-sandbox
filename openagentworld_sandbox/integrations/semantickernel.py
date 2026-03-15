"""
Semantic Kernel integration for openagentworld-sandbox.

Usage:
    from openagentworld_sandbox.integrations.semantickernel import CodeExecutionPlugin
    from semantic_kernel import Kernel

    kernel = Kernel()
    kernel.add_plugin(CodeExecutionPlugin(backend="docker"), "code")
"""

from typing import Optional
from ..executor import SafeExecutor
from ..security.profiles import SecurityProfile


try:
    from semantic_kernel.functions import kernel_function
    SEMANTIC_KERNEL_AVAILABLE = True
except ImportError:
    SEMANTIC_KERNEL_AVAILABLE = False
    def kernel_function(**kwargs):
        def decorator(func):
            return func
        return decorator


class CodeExecutionPlugin:
    """
    Semantic Kernel plugin for safe code execution.

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
        if not SEMANTIC_KERNEL_AVAILABLE:
            raise ImportError(
                "Semantic Kernel is not installed. "
                "Install with: pip install semantic-kernel"
            )
        self._executor = SafeExecutor(
            backend=backend,
            timeout=timeout,
            security=security,
            language=language
        )

    @kernel_function(description="Executes Python code safely in an isolated sandbox")
    def execute(self, code: str) -> str:
        """Execute code and return output."""
        result = self._executor.run(code)
        
        if result.is_timeout:
            return f"[Timeout] Execution exceeded {self._executor.timeout}s limit."
        if result.error:
            return f"[Error]\n{result.error}"
        return result.output or "[No output]"
