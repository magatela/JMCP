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
            "4. If an API operation fails, report the error code and error message back to the user.\n"
            "5. To prevent token window overflow (context bloating) when handling large amounts of data:\n"
            "   - Use JQL queries or lists which are returned in a condensed format by default.\n"
            "   - If you need to count, analyze, or process a large set of issues, divide the work into batches (e.g. processing 10-20 items at a time).\n"
            "   - Use the provisional memory tools (write_to_scratchpad, read_from_scratchpad, list_scratchpad_keys) to store partial calculations, counts, notes, or lists.\n"
            "   - Read from the scratchpad to consolidate your findings and deliver the final answer, then clear the scratchpad if no longer needed.\n"
            "6. When the user asks for charts, statistics, graphs, or visual metrics based on Jira data:\n"
            "   Calculate the statistics first, and then include a special `<chart>` XML block in your final text response. Do not add any text inside the block other than the raw JSON. The syntax is:\n"
            "   <chart type=\"bar|line|area|pie|metric\" title=\"Chart Title\">\n"
            "   {\n"
            "     \"labels\": [\"label1\", \"label2\", ...],\n"
            "     \"values\": [value1, value2, ...]\n"
            "   }\n"
            "   </chart>\n"
            "   For type=\"metric\", values can be numbers or strings, and labels represent each metric name."
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
