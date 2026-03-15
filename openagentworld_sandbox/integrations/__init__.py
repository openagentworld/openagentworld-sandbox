# Framework integrations
# Each integration provides a safe code execution tool for the respective framework

from .autogen import AutoGenSandbox
from .langchain import LangChainSandbox
from .crewai import CodeExecutorTool as CrewAITool
from .llamaindex import CodeExecutionTool as LlamaIndexTool
from .smolagents import CodeExecutorTool as SmolagentsTool
from .openmanus import OpenManusExecutor
from .agno import CodeExecutor as AgnoTool
from .semantickernel import CodeExecutionPlugin as SemanticKernelPlugin
from .dspy import CodeExecutorModule as DSPyModule
from .camel import CodeExecutionTool as CamelTool
from .haystack import CodeExecutorTool as HaystackTool

__all__ = [
    "AutoGenSandbox",
    "LangChainSandbox",
    "CrewAITool",
    "LlamaIndexTool",
    "SmolagentsTool",
    "OpenManusExecutor",
    "AgnoTool",
    "SemanticKernelPlugin",
    "DSPyModule",
    "CamelTool",
    "HaystackTool",
]
