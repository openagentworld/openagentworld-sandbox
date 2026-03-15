import abc
from dataclasses import dataclass, field
from typing import Optional
from .security.profiles import SecurityProfile


@dataclass
class ExecutionResult:
    """Unified result returned by all backends."""
    output: str
    exit_code: int
    is_timeout: bool = False
    error: Optional[str] = None
    backend_used: str = "unknown"


class SandboxBackend(abc.ABC):
    """Abstract base — every backend (local, docker, e2b) implements this."""

    @abc.abstractmethod
    def run(self, code: str, timeout: int) -> ExecutionResult:
        pass


class SafeExecutor:
    """
    Universal controller.
    Framework-agnostic — called by AutoGen/LangChain integration layers
    or directly by the developer.

    Usage:
        executor = SafeExecutor(backend="local")
        result = executor.run("print('hello')")
    """

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: Optional[SecurityProfile] = None,
        **kwargs
    ):
        self.timeout = timeout
        self.security = security or SecurityProfile.DEFAULT
        self.backend_name = backend
        self.backend = self._initialize_backend(backend, **kwargs)

    def _initialize_backend(self, backend: str, **kwargs) -> SandboxBackend:
        if backend == "local":
            from .backends.local import LocalBackend
            return LocalBackend(security=self.security, **kwargs)
        elif backend == "docker":
            from .backends.docker import DockerBackend
            return DockerBackend(security=self.security, **kwargs)
        elif backend == "e2b":
            from .backends.e2b import E2BBackend
            return E2BBackend(security=self.security, **kwargs)
        else:
            raise ValueError(
                f"Backend '{backend}' is not supported. "
                f"Choose from: local, docker, e2b"
            )

    def _sanitize(self, code: str) -> str:
        """Block forbidden imports based on security profile."""
        if not self.security.blocked_imports:
            return code
        for forbidden in self.security.blocked_imports:
            if f"import {forbidden}" in code or f"from {forbidden}" in code:
                raise PermissionError(
                    f"Import '{forbidden}' is blocked by security profile."
                )
        return code

    def run(self, code: str) -> ExecutionResult:
        """
        Execute code and return a unified ExecutionResult.
        All sanitization and timeout logic lives here.
        """
        code = self._sanitize(code)
        result = self.backend.run(code, timeout=self.timeout)
        result.backend_used = self.backend_name
        return result
