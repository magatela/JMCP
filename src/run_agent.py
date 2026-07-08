# run_agent.py
"""
Runnable script to execute the LangGraph agent interactively.
Loads credentials from a .env file and sets up the chat loop,
supporting proxy configurations and custom local LLM base URLs (e.g. for Gemma).
"""

import os
import sys
from dotenv import load_dotenv

# Ensure that the src and src/api directories are in the path for clean imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
api_dir = os.path.join(current_dir, "api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from api.jira_api import JiraAPI
from api.xray_api import XrayAPI
from agent.tools import get_jira_tools
from agent.graph import compile_agent


def main():
    # Load environment variables from the .env file
    load_dotenv()

    # Retrieve Jira credentials
    base_url = os.getenv("JIRA_BASE_URL")
    user = os.getenv("JIRA_USER")
    password = os.getenv("JIRA_PASSWORD")
    prefix = os.getenv("JIRA_PREFIX")
    jira_proxy = os.getenv("JIRA_PROXY", "")

    # Retrieve OpenAI / LLM credentials
    openai_api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    llm_base_url = os.getenv("LLM_BASE_URL", "")

    print("=" * 60)
    print("           JIRA & XRAY LANGGRAPH AGENT RUNNER")
    print("=" * 60)

    # Validate critical variables
    missing_vars = []
    if not base_url: missing_vars.append("JIRA_BASE_URL")
    if not user: missing_vars.append("JIRA_USER")
    if not password: missing_vars.append("JIRA_PASSWORD")
    if not prefix: missing_vars.append("JIRA_PREFIX")
    
    api_key_to_use = openai_api_key
    if not llm_base_url and not openai_api_key:
        missing_vars.append("OPENAI_API_KEY")
    elif llm_base_url and not openai_api_key:
        api_key_to_use = "dummy-key"

    if missing_vars:
        print(f"\n[ERROR] Missing the following environment variables in your .env file:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease create a '.env' file in the project root based on '.env.example'")
        sys.exit(1)

    # Configure HTTP/HTTPS proxy in system environment for LLM requests
    if jira_proxy:
        print(f"[*] Setting system proxy to: {jira_proxy}")
        os.environ["HTTP_PROXY"] = jira_proxy
        os.environ["HTTPS_PROXY"] = jira_proxy
        os.environ["http_proxy"] = jira_proxy
        os.environ["https_proxy"] = jira_proxy

    print(f"[*] Connecting to Jira: {base_url} (Project prefix: {prefix})")
    if jira_proxy:
        print(f"[*] Using connection proxy: {jira_proxy}")
    print(f"[*] Initializing LLM: {model_name}")
    if llm_base_url:
        print(f"[*] Routing LLM requests to local base URL: {llm_base_url}")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("[ERROR] Could not import langchain_openai. Ensure you have installed the requirements correctly.")
        sys.exit(1)

    # Build proxies argument for Jira/Xray clients
    proxies_dict = None
    if jira_proxy:
        proxies_dict = {
            "http": jira_proxy,
            "https": jira_proxy
        }

    # 1. Instantiate Jira and Xray API clients
    jira_client = JiraAPI(
        base_url=base_url,
        prefix=prefix,
        user=user,
        password=password,
        proxies=proxies_dict
    )

    # Xray is optional; check if user wants to enable it
    xray_enabled = os.getenv("ENABLE_XRAY", "true").lower() == "true"
    xray_client = None
    if xray_enabled:
        print("[*] Xray integration enabled.")
        xray_client = XrayAPI(
            base_url=base_url,
            prefix=prefix,
            user=user,
            password=password,
            proxies=proxies_dict
        )

    # 2. Get bound tools
    tools = get_jira_tools(jira=jira_client, xray=xray_client)
    print(f"[*] Registered {len(tools)} Jira/Xray tools.")

    # 3. Instantiate LLM
    llm_params = {
        "model": model_name,
        "temperature": 0,
        "api_key": api_key_to_use
    }
    if llm_base_url:
        llm_params["base_url"] = llm_base_url

    llm = ChatOpenAI(**llm_params)

    # 4. Compile LangGraph agent
    print("[*] Compiling the LangGraph agent...")
    agent = compile_agent(model=llm, tools=tools)
    print("[+] Agent ready and compiled successfully.")
    print("=" * 60)
    print("Enter your queries about Jira/Xray. Type 'exit' or 'salir' to quit.")
    print("=" * 60)

    # Thread configuration for chat memory session
    config = {"configurable": {"thread_id": "interactive-session-1"}}

    while True:
        try:
            query = input("\nYou: ").strip()
            if not query:
                continue
            if query.lower() in ["salir", "exit", "quit"]:
                print("Goodbye!")
                break

            print("\n[*] Processing request...")
            
            # Invoke the LangGraph agent passing the user query
            response = agent.invoke(
                {"messages": [("user", query)]},
                config=config
            )
            
            # Print the final agent response
            # In LangGraph ReAct agent, the last message contains the assistant's response
            last_message = response["messages"][-1]
            print(f"\nAgent: {last_message.content}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n[ERROR] An error occurred while executing the agent: {e}")


if __name__ == "__main__":
    main()
