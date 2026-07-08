# graph.py
"""
Defines the structure of the LangGraph agent.
Compiles the execution graph with tools and persistent memory.
"""

from typing import List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


def compile_agent(
    model: BaseChatModel,
    tools: List[BaseTool],
    system_prompt: Optional[str] = None
):
    """
    Compiles the ReAct agent using the prebuilt create_react_agent function from LangGraph.
    
    Parameters:
    - model: The LangChain chat model (e.g. ChatOpenAI, ChatAnthropic, etc.).
    - tools: List of LangChain tools accessible to the agent.
    - system_prompt: System instructions to guide the agent.
    
    Returns:
    - A compiled graph ready for invocation.
    """
    if system_prompt is None:
        system_prompt = (
            "You are an expert AI assistant for Jira and Xray.\n"
            "You help users manage issues, view details, run JQL queries, and perform transitions.\n"
            "Important Rules:\n"
            "1. Use the tools at your disposal to query accurate information before responding.\n"
            "2. Be precise and polite.\n"
            "3. When performing issue status transitions, make sure to query available transitions first using get_issue_transitions.\n"
            "4. If an API operation fails, report the error code and error message back to the user."
        )

    # In-memory checkpointer to keep conversation history (context) via thread_id
    memory = MemorySaver()

    # Compile the ReAct agent with tools and memory
    compiled_agent = create_react_agent(
        model=model,
        tools=tools,
        checkpointer=memory
    )
    
    return compiled_agent
