# Contributing

Welcome! This project aims to be the universal abstraction layer for safe code execution in AI agents.

## Adding a New Backend

Adding a new backend is straightforward:

1. **Create the backend file** in `openagentworld_sandbox/backends/`:
   ```python
   # openagentworld_sandbox/backends/firecracker.py
   from ..executor import SandboxBackend, ExecutionResult
   
   class FirecrackerBackend(SandboxBackend):
       def run(self, code: str, timeout: int) -> ExecutionResult:
           # Implement your backend here
           ...
   ```

2. **Register it in** `openagentworld_sandbox/backends/__init__.py`:
   ```python
   from .firecracker import FirecrackerBackend
   ```

3. **Update the executor** in `openagentworld_sandbox/executor.py`:
   ```python
   elif backend == "firecracker":
       from .backends.firecracker import FirecrackerBackend
       backend_instance = FirecrackerBackend(...)
   ```

4. **Add tests** in `tests/test_core.py`

5. **Update README.md** with the new backend in the comparison table

## Backend Requirements

Every backend must implement:
- `run(code: str, timeout: int) -> ExecutionResult`
- Return `ExecutionResult` with: `output`, `exit_code`, `is_timeout`, `error`, `backend_used`

## Security

All backends should consider:
- Resource limits (memory, CPU)
- Network isolation
- Filesystem access
- Cleanup on exit

## Development Setup

```bash
git clone https://github.com/openagentworld/openagentworld-sandbox
cd openagentworld-sandbox
pip install -e ".[dev]"
pytest tests/ -v
```

## Questions?

Open an issue at https://github.com/openagentworld/openagentworld-sandbox/issues
