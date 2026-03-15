import docker
import tempfile
import os
import tarfile
import io
import uuid
from typing import Optional, Any
from ..executor import ExecutionResult, SandboxBackend
from ..security.profiles import SecurityProfile


class DockerBackend(SandboxBackend):
    """
    Executes code inside an isolated Docker container.
    - Respects SecurityProfile (network, memory, CPU)
    - Supports multiple languages: python, javascript, bash
    - Session persistence: reuse container across multiple .run() calls

    Requires: Docker Desktop running locally.
    """

    DEFAULT_IMAGE = "python:3.11-slim"
    LANGUAGE_IMAGES = {
        "python": "python:3.11-slim",
        "javascript": "node:20-slim",
        "bash": "bash:5.2",
    }
    LANGUAGE_EXTENSIONS = {
        "python": "py",
        "javascript": "js",
        "bash": "sh",
    }

    def __init__(
        self,
        image: Optional[str] = None,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        session_id: Optional[str] = None,
        **kwargs: Any
    ):
        self.language = language.lower()
        self.image = image or self.LANGUAGE_IMAGES.get(
            self.language, self.DEFAULT_IMAGE
        )
        self.security = security or SecurityProfile.DEFAULT
        self.session_id = session_id
        self._container: Any = None
        self._container_name = f"sandbox-{session_id or uuid.uuid4().hex[:8]}"

        try:
            self.client = docker.from_env()
        except Exception as e:
            raise RuntimeError(
                "Docker is not running or not installed. "
                "Start Docker Desktop and try again."
            ) from e

    def _get_execute_command(self) -> str:
        """Get the appropriate command to execute code based on language."""
        ext = self.LANGUAGE_EXTENSIONS.get(self.language, "py")
        if self.language == "javascript":
            return f"node /tmp/code.{ext}"
        elif self.language == "bash":
            return f"bash /tmp/code.{ext}"
        else:
            return f"python /tmp/code.{ext}"

    def _build_run_config(self) -> dict[str, Any]:
        """Translate SecurityProfile into Docker run kwargs."""
        config: dict[str, Any] = {
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
            config["cpu_period"] = 100000
            config["cpu_quota"] = int(
                self.security.max_cpu_percent * 1000
            )

        # Read-only filesystem
        if not self.security.allow_filesystem_write:
            config["read_only"] = True

        return config

    def _ensure_container(self) -> None:
        """Start container if not already running (for session persistence)."""
        if self._container is None:
            run_config = self._build_run_config()
            run_config["name"] = self._container_name
            run_config["detach"] = True

            self._container = self.client.containers.run(
                self.image,
                command="sleep infinity",
                **run_config
            )

    def run(self, code: str, timeout: int) -> ExecutionResult:
        """Execute code in container. Reuse container if session_id provided."""
        container = None
        try:
            # Use persistent container for session, or create new one
            if self.session_id:
                self._ensure_container()
                container = self._container
            else:
                run_config = self._build_run_config()
                container = self.client.containers.run(
                    self.image,
                    command="sleep 60",
                    **run_config
                )

            if container is None:
                raise RuntimeError("Failed to create or find Docker container")

            # Package code as a tar archive to copy into container
            code_bytes = code.encode("utf-8")
            ext = self.LANGUAGE_EXTENSIONS.get(self.language, "py")
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                info = tarfile.TarInfo(name=f"code.{ext}")
                info.size = len(code_bytes)
                tar.addfile(info, io.BytesIO(code_bytes))
            tar_buffer.seek(0)

            container.put_archive("/tmp", tar_buffer)

            # Execute the code
            exec_result = container.exec_run(
                self._get_execute_command(),
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
            # Only cleanup container if no session
            if not self.session_id and self._container is None:
                if container:
                    try:
                        container.stop(timeout=2)
                    except Exception:
                        pass

    def close(self):
        """Close the session - stop and remove container."""
        if self._container:
            try:
                self._container.stop(timeout=2)
                self._container.remove()
            except Exception:
                pass
            self._container = None
