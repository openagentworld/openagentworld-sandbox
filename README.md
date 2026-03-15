# openagentworld-sandbox

<p align="center">
  <a href="https://pypi.org/project/openagentworld-sandbox/">
    <img src="https://img.shields.io/pypi/v/openagentworld-sandbox?color=%2334D058&label=PyPI" alt="PyPI version">
  </a>
  <a href="https://pypi.org/project/openagentworld-sandbox/">
    <img src="https://img.shields.io/pypi/pyversions/openagentworld-sandbox" alt="Python versions">
  </a>
  <a href="https://github.com/openagentworld/openagentworld-sandbox/actions">
    <img src="https://github.com/openagentworld/openagentworld-sandbox/workflows/CI/CD/badge.svg" alt="CI status">
  </a>
  <a href="https://github.com/openagentworld/openagentworld-sandbox/blob/main/LICENSE">
    <img src="https://img.shields.io/pypi/l/openagentworld-sandbox" alt="License">
  </a>
</p>

> **Run AI agent code safely — without the lock-in.**

One line to swap backends. Works with AutoGen, LangChain, or standalone.

---

## Installation

```bash
pip install openagentworld-sandbox
```

With Docker support:
```bash
pip install openagentworld-sandbox[docker]
```

With all backends:
```bash
pip install openagentworld-sandbox[all]
```

---

## Why openagentworld-sandbox?

| Problem | Solution |
|---------|----------|
| AutoGen executor only works with AutoGen | Framework-agnostic |
| `exec()` is dangerous with no isolation | Sandboxed execution |
| E2B is cloud-only and costs money | Local Docker backend |
| Malicious code can destroy your servers | Pre-execution scanner blocks 50+ dangerous patterns |

---

## Quick Start

```python
from openagentworld_sandbox import SafeExecutor, ScanError

# Create sandbox — runs anywhere
executor = SafeExecutor(backend="docker")

# Safe execution
result = executor.run("print(2 ** 32)")
print(result.output)  # 4294967296

# Dangerous code is blocked BEFORE it runs
try:
    executor.run("import os; os.system('rm -rf /')")
except ScanError as e:
    print(f"Blocked: {e}")

# Multi-language: JavaScript, Bash, Python
js = SafeExecutor(backend="docker", language="javascript")
js.run("console.log('hello')")

bash = SafeExecutor(backend="docker", language="bash")
bash.run("echo 'hello'")

# Session persistence — stateful across runs
executor = SafeExecutor(backend="docker", session_id="my-session")
executor.run("x = 42")      # set variable
executor.run("print(x)")    # prints 42 — state preserved!
```

---

## Features

### 🛡️ Pre-execution Scanner
Blocks 50+ dangerous patterns automatically before code runs:

- **Code execution**: `eval()`, `exec()`, `compile()`, `__import__()`
- **Process execution**: `os.system()`, `subprocess.*()`, `fork()`, `spawn()`
- **File operations**: write, delete, rename, chmod, shutil.*
- **Network**: sockets, HTTP requests, urllib, requests, telnetlib, ftplib
- **Threading**: threading, multiprocessing, asyncio imports
- **Serialization**: pickle, yaml.unsafe_load, marshal, shelve

### 🔒 Security Profiles

```python
SafeExecutor(backend="docker", security=SecurityProfile.STRICT)   
# 128MB RAM, no network, no filesystem write, blocked imports

SafeExecutor(backend="docker", security=SecurityProfile.DEFAULT) 
# Balanced - nothing blocked by default

SafeExecutor(backend="local", security=SecurityProfile.PERMISSIVE)  
# Minimal restrictions - for trusted code
```

### 🐳 Docker Backend
- CPU/memory caps via SecurityProfile
- Network isolation with `network_disabled`
- Automatic container cleanup
- Multi-language: Python, JavaScript, Bash

### 🔥 Firecracker Backend
- MicroVM isolation (like AWS Lambda/Fargate)
- Stronger than containers — VM-level security
- Configurable memory (default 256MB)
- Requires: [firecracker binary](https://github.com/firecracker-microvm/firecracker)

### 💾 Session Persistence
Maintain state across multiple `.run()` calls:

```python
executor = SafeExecutor(backend="docker", session_id="my-app")

executor.run("import numpy as np")  # import persists
executor.run("arr = np.array([1,2,3])")  # variable persists
executor.run("print(arr.mean())")  # 2.0 — all state preserved!
```

---

## Framework Integrations

### AutoGen
```python
from openagentworld_sandbox.integrations.autogen import AutoGenSandbox
from openagentworld_sandbox import SecurityProfile

executor = AutoGenSandbox(
    backend="docker", 
    security=SecurityProfile.STRICT
)
agent = AssistantAgent(name="coder", code_executor=executor)
```

### LangChain
```python
from openagentworld_sandbox.integrations.langchain import LangChainSandbox
from langchain.agents import initialize_agent

tool = LangChainSandbox(backend="docker")
agent = initialize_agent(tools=[tool], llm=llm, agent="...")
```

---

## Backends

| Backend | Isolation | Cost | When to Use |
|---------|-----------|------|-------------|
| `local` | Subprocess | Free | Development, testing |
| `docker` | Container | Free | Production (self-hosted) |
| `firecracker` | MicroVM | Free | Highest security needs |
| `e2b` | Cloud VM | Paid | When you need cloud |

---

## API Reference

```python
from openagentworld_sandbox import SafeExecutor, ExecutionResult, SecurityProfile, ScanError

# Create executor
executor = SafeExecutor(
    backend="docker",      # "local", "docker", "e2b"
    timeout=30,           # seconds before timeout
    security=SecurityProfile.STRICT,
    language="python"      # "python", "javascript", "bash"
)

# Execute code
result = executor.run("print('hello')")

# Result fields
result.output       # stdout string
result.exit_code    # 0 = success
result.is_timeout  # True if timed out
result.error       # stderr if any
result.backend_used # "local", "docker", "e2b"
```

---

## Why Not...?

### E2B
- Cloud-only → costs money, data leaves your infrastructure
- openagentworld-sandbox runs locally with Docker — **free**

### Custom Docker scripts
- You'd build the scanner from scratch
- No unified API across backends
- No framework integrations

### Pyodide (browser)
- Python only, limited packages
- No true server-side execution

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  ⭐ Star us if this solves your problem
</p>
