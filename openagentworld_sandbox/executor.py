import abc
import uuid
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from .security.profiles import SecurityProfile
from .scanner import scan


@dataclass
class ExecutionResult:
    """Unified result returned by all backends."""
    output: str
    exit_code: int
    is_timeout: bool = False
    error: Optional[str] = None
    backend_used: str = "unknown"
    duration_ms: float = 0.0
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


@dataclass
class ResourceStats:
    """Resource usage statistics during execution."""
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    duration_ms: float = 0.0


@dataclass
class ExecutionRecord:
    """Record of a single execution."""
    id: str
    code: str
    result: ExecutionResult
    timestamp: float


@dataclass
class BatchResult:
    """Result of batch execution."""
    results: List[ExecutionResult]
    total_duration_ms: float
    success_count: int
    failure_count: int


class OutputFormatter:
    """Format execution results in different formats."""

    @staticmethod
    def to_json(result: ExecutionResult) -> str:
        """Format result as JSON."""
        return json.dumps({
            "output": result.output,
            "exit_code": result.exit_code,
            "is_timeout": result.is_timeout,
            "error": result.error,
            "backend": result.backend_used,
            "duration_ms": result.duration_ms,
        }, indent=2)

    @staticmethod
    def to_markdown(result: ExecutionResult) -> str:
        """Format result as markdown."""
        md = "```\n"
        if result.output:
            md += result.output
        md += "```\n"
        if result.error:
            md += f"**Error:** {result.error}\n"
        md += f"**Exit code:** {result.exit_code}\n"
        md += f"**Duration:** {result.duration_ms:.2f}ms\n"
        return md

    @staticmethod
    def to_text(result: ExecutionResult) -> str:
        """Format result as plain text."""
        if result.error:
            return f"[ERROR] {result.error}\n{result.output}"
        return result.output


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

    Session persistence:
        executor = SafeExecutor(backend="docker", session_id="my-session")
        executor.run("x = 1")
        executor.run("print(x)")  # prints 1
    """

    def __init__(
        self,
        backend: str = "local",
        timeout: int = 30,
        security: Optional[SecurityProfile] = None,
        language: str = "python",
        session_id: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        pip_packages: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        enable_history: bool = False,
        max_history: int = 100,
        on_success: Optional[Callable[[ExecutionResult], None]] = None,
        on_error: Optional[Callable[[ExecutionResult], None]] = None,
        output_format: str = "text",
        **kwargs: Any
    ):
        self.timeout = timeout
        self.security = security or SecurityProfile.DEFAULT
        self.language = language
        self.backend_name = backend
        self.session_id = session_id
        self.env = env or {}
        self.pip_packages = pip_packages or []
        self.working_dir = working_dir or "/tmp"
        self.enable_history = enable_history
        self.max_history = max_history
        self.on_success = on_success
        self.on_error = on_error
        self.output_format = output_format
        self._history: List[ExecutionRecord] = []
        self.backend = self._initialize_backend(backend, **kwargs)

    def _initialize_backend(self, backend: str, **kwargs: Any) -> SandboxBackend:
        kwargs.setdefault("language", self.language)
        kwargs.setdefault("env", self.env)
        kwargs.setdefault("pip_packages", self.pip_packages)
        kwargs.setdefault("working_dir", self.working_dir)
        if self.session_id:
            kwargs.setdefault("session_id", self.session_id)
        if backend == "local":
            from .backends.local import LocalBackend
            return LocalBackend(security=self.security, **kwargs)
        elif backend == "docker":
            from .backends.docker import DockerBackend
            return DockerBackend(security=self.security, **kwargs)
        elif backend == "e2b":
            from .backends.e2b import E2BBackend
            return E2BBackend(security=self.security, **kwargs)
        elif backend == "firecracker":
            from .backends.firecracker import FirecrackerBackend
            return FirecrackerBackend(security=self.security, **kwargs)
        else:
            raise ValueError(
                f"Backend '{backend}' is not supported. "
                f"Choose from: local, docker, e2b, firecracker"
            )

    def _inject_dependencies(self, code: str) -> str:
        """Inject pip package installation if needed."""
        if not self.pip_packages:
            return code

        install_code = "\n".join([
            (
                "import subprocess; subprocess.run("
                f"['pip', 'install', '-q', '{pkg}'], check=True)"
            )
            for pkg in self.pip_packages
        ])

        return f"{install_code}\n{code}"

    def _inject_env_vars(self, code: str) -> str:
        """Inject environment variables."""
        if not self.env:
            return code

        env_setup = "\n".join([
            f"__import__('os').environ['{key}'] = '{value}'"
            for key, value in self.env.items()
        ])

        return f"{env_setup}\n{code}"

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

    def _format_output(self, result: ExecutionResult) -> str:
        """Format output based on configured format."""
        if self.output_format == "json":
            return OutputFormatter.to_json(result)
        elif self.output_format == "markdown":
            return OutputFormatter.to_markdown(result)
        else:
            return OutputFormatter.to_text(result)

    def _record_execution(self, code: str, result: ExecutionResult) -> None:
        """Record execution in history."""
        if self.enable_history:
            record = ExecutionRecord(
                id=str(uuid.uuid4()),
                code=code,
                result=result,
                timestamp=time.time()
            )
            self._history.append(record)
            if len(self._history) > self.max_history:
                self._history.pop(0)

    def run(self, code: str) -> ExecutionResult:
        """
        Execute code and return a unified ExecutionResult.
        All sanitization and timeout logic lives here.

        Raises:
            ScanError: If dangerous code pattern detected
            PermissionError: If import blocked by security profile
        """
        start_time = time.time()

        # 1. Scan user code first (before injection)
        scan(code)

        # 2. Import block check
        code = self._sanitize(code)

        # 3. Inject dependencies and env vars AFTER scanning
        code = self._inject_dependencies(code)
        code = self._inject_env_vars(code)

        # 4. Execute
        result = self.backend.run(code, timeout=self.timeout)
        result.backend_used = self.backend_name
        result.duration_ms = (time.time() - start_time) * 1000

        # 5. Record execution
        self._record_execution(code, result)

        # 6. Callbacks
        if result.exit_code == 0 and self.on_success is not None:
            self.on_success(result)
        elif result.exit_code != 0 and self.on_error is not None:
            self.on_error(result)

        # 7. Format output
        formatted_output = self._format_output(result)
        result.output = formatted_output

        return result

    async def run_async(self, code: str) -> ExecutionResult:
        """Async execution - runs in thread pool to not block event loop."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.run, code)
        return result

    def run_batch(self, code_list: List[str]) -> BatchResult:
        """
        Execute multiple code snippets in sequence.

        Args:
            code_list: List of code strings to execute

        Returns:
            BatchResult with all execution results
        """
        results = []
        start_time = time.time()

        for code in code_list:
            result = self.run(code)
            results.append(result)

        total_duration = (time.time() - start_time) * 1000
        success = sum(1 for r in results if r.exit_code == 0)
        failure = len(results) - success

        return BatchResult(
            results=results,
            total_duration_ms=total_duration,
            success_count=success,
            failure_count=failure
        )

    async def run_streaming(
        self,
        code: str,
        callback: Callable[[str], None]
    ) -> ExecutionResult:
        """
        Execute code with streaming output support.

        Args:
            code: Code to execute
            callback: Function to call with each output chunk

        Returns:
            ExecutionResult
        """
        result = self.run(code)
        if result.output:
            for line in result.output.split('\n'):
                callback(line + '\n')
        return result
    def get_history(self) -> List[ExecutionRecord]:
        """Get execution history."""
        return self._history.copy()

    def clear_history(self) -> None:
        """Clear execution history."""
        self._history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self._history:
            return {"total_runs": 0}

        total = len(self._history)
        successes = sum(1 for r in self._history if r.result.exit_code == 0)
        failures = total - successes
        avg_duration = sum(r.result.duration_ms for r in self._history) / total

        return {
            "total_runs": total,
            "successes": successes,
            "failures": failures,
            "success_rate": successes / total if total > 0 else 0,
            "avg_duration_ms": avg_duration,
        }
