# openagentworld-sandbox

> A lightweight, framework-agnostic safe code execution library for AI agents.

No lock-in. Swap backends in one line. Works with AutoGen, LangChain, or standalone.

---

## The Problem

Every AI agent framework needs to execute code. But:

- AutoGen's executor only works with AutoGen
- LangChain has no safe execution built in
- E2B is cloud-only and paid
- `exec()` is dangerous with no isolation

**openagentworld-sandbox is the missing abstraction layer.**

---

## Install

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

## Quick Start

```python
from openagentworld_sandbox import SafeExecutor

# Local subprocess (dev/testing)
executor = SafeExecutor(backend="local")
result = executor.run("print('hello from sandbox')")
print(result.output)   # hello from sandbox
print(result.exit_code)  # 0

# Docker (isolated, production-safe)
executor = SafeExecutor(backend="docker")
result = executor.run("print(2 ** 32)")
print(result.output)   # 4294967296

# E2B cloud
executor = SafeExecutor(backend="e2b")
result = executor.run("print('running in cloud')")
```

---

## Security Profiles

```python
from openagentworld_sandbox import SafeExecutor, SecurityProfile

# STRICT: blocks dangerous imports, no network, 128MB RAM cap, wipes on exit
executor = SafeExecutor(backend="docker", security=SecurityProfile.STRICT)

# DEFAULT: sane defaults, nothing blocked
executor = SafeExecutor(backend="local", security=SecurityProfile.DEFAULT)

# PERMISSIVE: minimal restrictions for trusted code
executor = SafeExecutor(backend="local", security=SecurityProfile.PERMISSIVE)
```

---

## AutoGen Integration

```python
from openagentworld_sandbox.integrations.autogen import AutoGenSandbox
from autogen_agentchat.agents import AssistantAgent

executor = AutoGenSandbox(backend="docker", security=SecurityProfile.STRICT)

agent = AssistantAgent(
    name="coder",
    code_executor=executor
)
```

---

## LangChain Integration

```python
from openagentworld_sandbox.integrations.langchain import LangChainSandbox
from langchain.agents import initialize_agent

tool = LangChainSandbox(backend="docker")

agent = initialize_agent(
    tools=[tool],
    llm=llm,
    agent="zero-shot-react-description"
)
```

---

## ExecutionResult

Every `.run()` call returns:

```python
@dataclass
class ExecutionResult:
    output: str         # stdout
    exit_code: int      # 0 = success
    is_timeout: bool    # True if killed by timeout
    error: str | None   # stderr if any
    backend_used: str   # "local" | "docker" | "e2b"
```

---

## Backends

| Backend | Isolation | Cost | Requires |
|---|---|---|---|
| `local` | Low (subprocess) | Free | Nothing |
| `docker` | High (container) | Free | Docker Desktop |
| `e2b` | High (cloud VM) | Paid tiers | E2B API key |

---

## Roadmap

- [ ] Firecracker backend
- [ ] Multi-language support (JS, bash)
- [ ] Session persistence across `.run()` calls
- [ ] CrewAI integration
- [ ] OpenManus integration

---

## Contributing

Issues and PRs welcome at [openagentworld/openagentworld-sandbox](https://github.com/openagentworld/openagentworld-sandbox)

---

## License

MIT
