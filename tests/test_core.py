"""
Full test suite for agent-sandbox.
Run with: pytest tests/ -v
"""

import pytest
from agent_sandbox import SafeExecutor, SecurityProfile


# ─────────────────────────────────────────
# LOCAL BACKEND TESTS
# ─────────────────────────────────────────

class TestLocalBackend:

    def setup_method(self):
        self.ex = SafeExecutor(backend="local", timeout=5)

    def test_basic_print(self):
        result = self.ex.run("print('hello world')")
        assert result.output.strip() == "hello world"
        assert result.exit_code == 0
        assert result.error is None

    def test_math_output(self):
        result = self.ex.run("print(2 + 2)")
        assert result.output.strip() == "4"

    def test_multiline_code(self):
        code = """
x = 10
y = 20
print(x + y)
"""
        result = self.ex.run(code)
        assert result.output.strip() == "30"

    def test_syntax_error_captured(self):
        result = self.ex.run("print(undefined_variable)")
        assert result.exit_code != 0
        assert result.error is not None

    def test_timeout(self):
        ex = SafeExecutor(backend="local", timeout=2)
        result = ex.run("import time; time.sleep(10)")
        assert result.is_timeout is True
        assert result.exit_code == 1

    def test_backend_used_label(self):
        result = self.ex.run("print('ok')")
        assert result.backend_used == "local"

    def test_empty_output(self):
        result = self.ex.run("x = 1 + 1")
        assert result.output == ""
        assert result.exit_code == 0


# ─────────────────────────────────────────
# SECURITY PROFILE TESTS
# ─────────────────────────────────────────

class TestSecurityProfiles:

    def test_strict_blocks_os_import(self):
        ex = SafeExecutor(backend="local", security=SecurityProfile.STRICT)
        with pytest.raises(PermissionError):
            ex.run("import os; print(os.getcwd())")

    def test_strict_blocks_subprocess(self):
        ex = SafeExecutor(backend="local", security=SecurityProfile.STRICT)
        with pytest.raises(PermissionError):
            ex.run("import subprocess; subprocess.run(['ls'])")

    def test_default_allows_os(self):
        ex = SafeExecutor(backend="local", security=SecurityProfile.DEFAULT)
        result = ex.run("import os; print('ok')")
        assert result.output.strip() == "ok"

    def test_permissive_allows_all(self):
        ex = SafeExecutor(backend="local", security=SecurityProfile.PERMISSIVE)
        result = ex.run("import os; print('ok')")
        assert result.output.strip() == "ok"


# ─────────────────────────────────────────
# SAFE EXECUTOR DIRECT API TESTS
# ─────────────────────────────────────────

class TestSafeExecutorAPI:

    def test_invalid_backend_raises(self):
        with pytest.raises(ValueError):
            SafeExecutor(backend="firecracker_not_real")

    def test_result_dataclass_fields(self):
        ex = SafeExecutor(backend="local")
        result = ex.run("print('test')")
        assert hasattr(result, "output")
        assert hasattr(result, "exit_code")
        assert hasattr(result, "is_timeout")
        assert hasattr(result, "error")
        assert hasattr(result, "backend_used")

    def test_stderr_captured(self):
        ex = SafeExecutor(backend="local")
        result = ex.run("import sys; sys.stderr.write('err msg')")
        assert result.error is not None
        assert "err msg" in result.error
