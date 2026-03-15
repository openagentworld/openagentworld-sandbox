import docker
import tempfile
import os
import tarfile
import io
from ..executor import ExecutionResult, SandboxBackend
from ..security.profiles import SecurityProfile


class DockerBackend(SandboxBackend):
    """
    Executes code inside an isolated Docker container.
    - Each execution spins up a fresh container
    - Container is auto-removed after execution
    - Respects SecurityProfile (network, memory, CPU)

    Requires: Docker Desktop running locally.
    """

    DEFAULT_IMAGE = "python:3.11-slim"

    def __init__(
        self,
        image: str = DEFAULT_IMAGE,
        security: SecurityProfile = None,
        **kwargs
    ):
        self.image = image
        self.security = security or SecurityProfile.DEFAULT
        try:
            self.client = docker.from_env()
        except Exception as e:
            raise RuntimeError(
                "Docker is not running or not installed. "
                "Start Docker Desktop and try again."
            ) from e

    def _build_run_config(self) -> dict:
        """Translate SecurityProfile into Docker run kwargs."""
        config = {
            "detach": True,
            "remove": True,
        }

        # Network isolation
        if not self.security.network_access:
            config["network_disabled"] = True

        # Memory cap
        if self.security.max_memory_mb:
            config["mem_limit"] = f"{self.security.max_memory_mb}m"

        # CPU cap
        if self.security.max_cpu_percent:
            # Docker uses cpu_quota + cpu_period
            config["cpu_period"] = 100000
            config["cpu_quota"] = int(
                self.security.max_cpu_percent * 1000
            )

        # Read-only filesystem
        if not self.security.allow_filesystem_write:
            config["read_only"] = True

        return config

    def run(self, code: str, timeout: int) -> ExecutionResult:
        container = None
        try:
            run_config = self._build_run_config()

            # Start container with a sleep so we can copy code in
            container = self.client.containers.run(
                self.image,
                command="sleep 60",
                **run_config
            )

            # Package code as a tar archive to copy into container
            code_bytes = code.encode("utf-8")
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                info = tarfile.TarInfo(name="code.py")
                info.size = len(code_bytes)
                tar.addfile(info, io.BytesIO(code_bytes))
            tar_buffer.seek(0)

            container.put_archive("/tmp", tar_buffer)

            # Execute the code
            exec_result = container.exec_run(
                "python /tmp/code.py",
                demux=True
            )

            stdout = exec_result.output[0] or b""
            stderr = exec_result.output[1] or b""

            return ExecutionResult(
                output=stdout.decode("utf-8", errors="replace"),
                exit_code=exec_result.exit_code,
                error=stderr.decode("utf-8", errors="replace") or None
            )

        except Exception as e:
            err = str(e)
            is_timeout = "timeout" in err.lower()
            return ExecutionResult(
                output="",
                exit_code=1,
                is_timeout=is_timeout,
                error=f"DockerBackend error: {err}"
            )

        finally:
            if container:
                try:
                    container.stop(timeout=2)
                except Exception:
                    pass
