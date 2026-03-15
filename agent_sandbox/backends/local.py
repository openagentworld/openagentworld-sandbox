import subprocess
import tempfile
import os
from ..executor import ExecutionResult, SandboxBackend
from ..security.profiles import SecurityProfile


class LocalBackend(SandboxBackend):
    """
    Executes code in a local subprocess using a temp file.
    NOT fully isolated — safe enough for dev/testing.
    For production isolation, use DockerBackend.
    """

    def __init__(self, security: SecurityProfile = None, **kwargs):
        self.security = security or SecurityProfile.DEFAULT

    def run(self, code: str, timeout: int) -> ExecutionResult:
        tmp_path = None
        try:
            # Write code to a temp file
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8"
            ) as f:
                f.write(code)
                tmp_path = f.name

            result = subprocess.run(
                ["python", tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return ExecutionResult(
                output=result.stdout,
                exit_code=result.returncode,
                error=result.stderr if result.stderr else None
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                output="",
                exit_code=1,
                is_timeout=True,
                error=f"Execution exceeded timeout of {timeout}s"
            )

        except Exception as e:
            return ExecutionResult(
                output="",
                exit_code=1,
                error=f"LocalBackend error: {str(e)}"
            )

        finally:
            # Always clean up temp file
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
