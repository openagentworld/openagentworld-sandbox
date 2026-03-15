from typing import Optional, Any
from ..executor import ExecutionResult, SandboxBackend
from ..security.profiles import SecurityProfile


class E2BBackend(SandboxBackend):
    """
    Executes code in E2B cloud sandboxes.
    Requires: `pip install e2b-code-interpreter` and E2B_API_KEY env var.

    Usage:
        import os
        os.environ["E2B_API_KEY"] = "your_key"
        executor = SafeExecutor(backend="e2b")
    """

    def __init__(
        self,
        security: Optional[SecurityProfile] = None,
        **kwargs: Any
    ):
        self.security = security or SecurityProfile.DEFAULT
        try:
            from e2b_code_interpreter import Sandbox
            self._Sandbox = Sandbox
        except ImportError:
            raise ImportError(
                "E2B backend requires e2b-code-interpreter. "
                "Install with: pip install e2b-code-interpreter"
            )

    def run(self, code: str, timeout: int) -> ExecutionResult:
        try:
            with self._Sandbox() as sandbox:
                execution = sandbox.run_code(code, timeout=timeout)

                output = "\n".join(
                    str(r) for r in execution.results
                ) if execution.results else ""

                error = execution.error.traceback if execution.error else None

                return ExecutionResult(
                    output=output,
                    exit_code=1 if execution.error else 0,
                    error=error
                )

        except Exception as e:
            err = str(e)
            return ExecutionResult(
                output="",
                exit_code=1,
                is_timeout="timeout" in err.lower(),
                error=f"E2BBackend error: {err}"
            )
