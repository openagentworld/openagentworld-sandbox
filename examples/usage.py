"""
agent-sandbox usage examples.
Run any section independently.
"""

from agent_sandbox import SafeExecutor, SecurityProfile


# ─────────────────────────────────────────
# 1. Basic local execution
# ─────────────────────────────────────────

ex = SafeExecutor(backend="local")

result = ex.run("print('hello from agent-sandbox')")
print(result.output)      # hello from agent-sandbox
print(result.exit_code)   # 0
print(result.error)       # None


# ─────────────────────────────────────────
# 2. Swap backend — zero code change
# ─────────────────────────────────────────

# Just change this one line:
# ex = SafeExecutor(backend="docker")
# ex = SafeExecutor(backend="e2b")
# Everything else stays identical.


# ─────────────────────────────────────────
# 3. Timeout handling
# ─────────────────────────────────────────

ex = SafeExecutor(backend="local", timeout=3)
result = ex.run("import time; time.sleep(100)")

if result.is_timeout:
    print("Execution was killed — took too long")


# ─────────────────────────────────────────
# 4. Error capture
# ─────────────────────────────────────────

result = ex.run("print(this_doesnt_exist)")
print(result.exit_code)  # non-zero
print(result.error)      # NameError: name 'this_doesnt_exist' is not defined


# ─────────────────────────────────────────
# 5. Security profiles
# ─────────────────────────────────────────

# STRICT — blocks dangerous imports
strict_ex = SafeExecutor(backend="local", security=SecurityProfile.STRICT)

try:
    strict_ex.run("import os; os.system('rm -rf /')")
except PermissionError as e:
    print(f"Blocked: {e}")  # Import 'os' is blocked by security profile


# ─────────────────────────────────────────
# 6. AutoGen drop-in (requires autogen installed)
# ─────────────────────────────────────────

# from agent_sandbox.integrations.autogen import AutoGenSandbox
# from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
#
# executor = AutoGenSandbox(backend="docker")
#
# assistant = AssistantAgent(name="assistant", code_executor=executor)
# user = UserProxyAgent(name="user", human_input_mode="NEVER")
#
# user.initiate_chat(assistant, message="Write and run a fibonacci sequence")


# ─────────────────────────────────────────
# 7. LangChain drop-in (requires langchain installed)
# ─────────────────────────────────────────

# from agent_sandbox.integrations.langchain import LangChainSandbox
# from langchain.agents import initialize_agent
# from langchain_openai import ChatOpenAI
#
# tool = LangChainSandbox(backend="docker", security=SecurityProfile.STRICT)
# llm = ChatOpenAI(model="gpt-4")
#
# agent = initialize_agent(
#     tools=[tool],
#     llm=llm,
#     agent="zero-shot-react-description",
#     verbose=True
# )
# agent.run("Calculate the first 10 prime numbers")
