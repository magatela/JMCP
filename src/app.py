# app.py
"""
Streamlit Web Interface for the Jira & Xray LangGraph Agent.
Provides a premium dark-themed UI for natural language interaction,
supporting network proxy configurations and local models (e.g., Gemma).
"""

import os
import sys
import uuid
import streamlit as st
from dotenv import load_dotenv

# Ensure local directories are in path
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

# ---------------------------------------------------------
# Page Configurations & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Jira & Xray AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium high-contrast light theme and layout custom styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Global Font Override and Base Light Styling */
html, body, [class*="css"], .stApp {
    font-family: 'Outfit', sans-serif;
    background-color: #f8fafc !important; /* Slate 50 background */
    color: #0f172a !important; /* Slate 900 high contrast dark text */
}

/* Premium Light Header Banner */
.header-container {
    background: linear-gradient(135deg, #e0e7ff 0%, #f5f3ff 50%, #fae8ff 100%);
    padding: 2.5rem;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    margin-bottom: 2rem;
    border: 1px solid #e2e8f0;
    text-align: center;
}

.header-title {
    font-size: 2.6rem;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(90deg, #4f46e5, #7c3aed, #2563eb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header-subtitle {
    font-size: 1.1rem;
    font-weight: 400;
    margin-top: 0.75rem;
    color: #1e1b4b; /* Deep indigo for high contrast */
}

/* Sidebar Styling - Light Slate */
section[data-testid="stSidebar"] {
    background-color: #f1f5f9 !important; /* Slate 100 */
    border-right: 1px solid #cbd5e1 !important;
}

.sidebar-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #0f172a !important;
    margin-bottom: 1.5rem;
}

/* Modern Card Layouts for Sidebar */
.sidebar-section-card {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
}

.sidebar-section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 0.5rem;
}

/* Tool Badges in Sidebar */
.tool-badge {
    display: inline-block;
    background-color: rgba(79, 70, 229, 0.08); /* Indigo tint */
    color: #4338ca; /* Indigo 700 - high contrast */
    border: 1px solid rgba(79, 70, 229, 0.15);
    border-radius: 6px;
    padding: 0.2rem 0.5rem;
    font-size: 0.8rem;
    margin: 0.2rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.tool-badge:hover {
    background-color: rgba(79, 70, 229, 0.15);
    border-color: #4338ca;
    transform: translateY(-1px);
}

/* Style overrides for inputs, buttons, and status labels to enforce contrast */
.stMarkdown p, label, .stMarkdown span {
    color: #0f172a !important;
    font-weight: 500;
}

/* Force dark text color on stForm, stExpander, and markdown outputs for legibility */
.stExpander, div[data-testid="stForm"] {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 10px !important;
}

/* Chat bubble overrides for high contrast light mode */
div[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

/* Keep user text dark slate */
div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] li, div[data-testid="stChatMessage"] span {
    color: #0f172a !important; 
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
# Load environment variables on startup
load_dotenv()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "jira_client" not in st.session_state:
    st.session_state.jira_client = None

if "xray_client" not in st.session_state:
    st.session_state.xray_client = None

if "agent" not in st.session_state:
    st.session_state.agent = None

if "connected" not in st.session_state:
    st.session_state.connected = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "config" not in st.session_state:
    st.session_state.config = {"configurable": {"thread_id": st.session_state.thread_id}}

# ---------------------------------------------------------
# Header Section
# ---------------------------------------------------------
st.markdown("""
<div class="header-container">
    <div class="header-title">🤖 Jira & Xray LangGraph Agent</div>
    <div class="header-subtitle">Interact with your Jira projects and Xray Test Suites using natural language</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Configuration Form
# ---------------------------------------------------------
st.sidebar.markdown('<div class="sidebar-title">⚙️ Configuration</div>', unsafe_allow_html=True)

# Auto-fill defaults from .env if available
default_url = os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net/")
default_user = os.getenv("JIRA_USER", "")
default_pass = os.getenv("JIRA_PASSWORD", "")
default_prefix = os.getenv("JIRA_PREFIX", "PROJ")
default_proxy = os.getenv("JIRA_PROXY", "")
default_openai_key = os.getenv("OPENAI_API_KEY", "")
default_model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
default_base_url = os.getenv("LLM_BASE_URL", "")
default_xray = os.getenv("ENABLE_XRAY", "true").lower() == "true"

with st.sidebar.form("credentials_form"):
    st.markdown('<div class="sidebar-section-title">🔌 Connection Details</div>', unsafe_allow_html=True)
    jira_url = st.text_input("Jira Base URL", value=default_url)
    jira_user = st.text_input("Jira Username / Email", value=default_user)
    jira_password = st.text_input("Jira Password / API Token", type="password", value=default_pass)
    jira_prefix = st.text_input("Jira Project Prefix", value=default_prefix)
    jira_proxy = st.text_input("Proxy URL (optional)", value=default_proxy, help="e.g., http://proxy.example.com:8080")

    st.markdown('<div class="sidebar-section-title">🧠 LLM Parameters</div>', unsafe_allow_html=True)
    openai_key = st.text_input("OpenAI API Key (optional for local LLM)", type="password", value=default_openai_key)
    openai_model = st.text_input("Model Name (e.g. gemma2, gpt-4o-mini)", value=default_model)
    llm_base_url = st.text_input("LLM Base URL (optional for local LLM)", value=default_base_url, help="e.g., http://localhost:11434/v1 for Ollama")
    
    st.markdown('<div class="sidebar-section-title">🧬 Features</div>', unsafe_allow_html=True)
    enable_xray = st.checkbox("Enable Xray Test Management Integration", value=default_xray)

    submit_button = st.form_submit_button("Save & Connect")

# ---------------------------------------------------------
# Connection Logic
# ---------------------------------------------------------
def connect_agent():
    if not jira_url or not jira_user or not jira_password or not jira_prefix:
        st.sidebar.error("Jira URL, Username, Password, and Prefix are required.")
        st.session_state.connected = False
        return

    # OpenAI-compatible local APIs (Ollama, LM Studio) might not need a real key.
    # However, ChatOpenAI requires api_key parameter to be set, otherwise it checks env vars.
    # We pass a dummy key if it's empty to allow local LLM execution.
    api_key_to_use = openai_key if openai_key else ("dummy-key" if llm_base_url else "")
    if not api_key_to_use:
        st.sidebar.error("OpenAI API Key is required when not using a local LLM Base URL.")
        st.session_state.connected = False
        return

    with st.sidebar.status("Connecting and compiling agent...", expanded=True) as status:
        try:
            # Configure HTTP/HTTPS proxy in system environment for LLM requests
            if jira_proxy:
                st.write(f"Setting system proxy environment variables to: {jira_proxy}")
                os.environ["HTTP_PROXY"] = jira_proxy
                os.environ["HTTPS_PROXY"] = jira_proxy
                os.environ["http_proxy"] = jira_proxy
                os.environ["https_proxy"] = jira_proxy
            else:
                # Remove proxy variables if empty, so local connections (like localhost) don't get routed incorrectly
                for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
                    if key in os.environ:
                        del os.environ[key]

            # Build proxies argument for Jira REST Client
            proxies_dict = None
            if jira_proxy:
                proxies_dict = {
                    "http": jira_proxy,
                    "https": jira_proxy
                }

            # 1. Instantiate the API client
            st.write("Initializing Jira Core client...")
            jira_client = JiraAPI(
                base_url=jira_url,
                prefix=jira_prefix,
                user=jira_user,
                password=jira_password,
                proxies=proxies_dict
            )

            # Test connection
            response = jira_client.check_user_credentials()
            if not response.ok:
                st.sidebar.error(f"Jira Connection failed: Status code {response.status_code}")
                st.session_state.connected = False
                return

            st.session_state.jira_client = jira_client

            # 2. Xray Integration
            xray_client = None
            if enable_xray:
                st.write("Initializing Xray Test Management client...")
                xray_client = XrayAPI(
                    base_url=jira_url,
                    prefix=jira_prefix,
                    user=jira_user,
                    password=jira_password,
                    proxies=proxies_dict
                )
                st.session_state.xray_client = xray_client
            else:
                st.session_state.xray_client = None

            # 3. Create Tools List
            st.write("Registering Jira/Xray tools...")
            tools = get_jira_tools(jira=jira_client, xray=xray_client)

            # 4. Compile the LangGraph Agent
            st.write("Compiling LangGraph agent...")
            from langchain_openai import ChatOpenAI
            
            llm_params = {
                "model": openai_model,
                "temperature": 0,
                "api_key": api_key_to_use
            }
            if llm_base_url:
                st.write(f"Routing LLM requests to local endpoint: {llm_base_url}")
                llm_params["base_url"] = llm_base_url

            llm = ChatOpenAI(**llm_params)
            agent = compile_agent(model=llm, tools=tools)

            st.session_state.agent = agent
            st.session_state.connected = True
            status.update(label="Successfully Connected!", state="complete", expanded=False)

        except Exception as e:
            st.session_state.connected = False
            status.update(label=f"Connection Error: {e}", state="error", expanded=True)

# Auto-connect on startup if credentials exist
if not st.session_state.connected and default_url and default_user and default_pass and default_prefix:
    if openai_key or default_base_url:
        connect_agent()

# If form is submitted, reconnect
if submit_button:
    connect_agent()

# ---------------------------------------------------------
# Sidebar Connection Status & Info Cards
# ---------------------------------------------------------
if st.session_state.connected:
    st.sidebar.success("🟢 Connected to Jira & Xray")
    
    # Active config info
    st.sidebar.markdown(f"""
    <div class="sidebar-section-card">
        <div class="sidebar-section-title">Active Environment</div>
        <p style="margin:0;font-size:0.9rem;color:#94a3b8;">
            <b>Project:</b> {jira_prefix}<br>
            <b>URL:</b> {jira_url}<br>
            <b>Model:</b> {openai_model}<br>
            <b>Proxy:</b> {"Yes" if jira_proxy else "No"}<br>
            <b>Local Endpoint:</b> {"Yes" if llm_base_url else "No"}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Display Enabled Tools
    st.sidebar.markdown('<div class="sidebar-section-title">Enabled Agent Tools</div>', unsafe_allow_html=True)
    
    jira_tools = [
        "get_project_info", "get_issue_info", "get_issue_changelogs", 
        "check_issue_editable_fields", "get_all_fields", "jql_search", 
        "get_bugs_linked_to_test", "get_test_cases_in_project", 
        "get_issue_transitions", "create_jira_issue", 
        "transition_jira_issue", "link_jira_issues", "update_jira_issue", "delete_jira_issue"
    ]
    xray_tools = [
        "xray_get_test_steps", "xray_add_test_step", "xray_delete_test_step", 
        "xray_get_all_test_executions", "xray_get_test_run_results", 
        "xray_add_test_to_execution", "xray_update_testrun_status", 
        "xray_get_testrun_data", "xray_get_testrun_data_by_id", "xray_upload_results"
    ]

    with st.sidebar.expander("Jira Core Tools", expanded=True):
        for tool in jira_tools:
            st.markdown(f'<span class="tool-badge">{tool}</span>', unsafe_allow_html=True)

    if enable_xray:
        with st.sidebar.expander("Xray Tools", expanded=True):
            for tool in xray_tools:
                st.markdown(f'<span class="tool-badge">{tool}</span>', unsafe_allow_html=True)

else:
    st.sidebar.warning("🔴 Disconnected. Please configure details above.")

# ---------------------------------------------------------
# Chat Interface
# ---------------------------------------------------------
# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Chat Input
if st.session_state.connected:
    user_input = st.chat_input("Ask about Jira tasks, transitions, JQL, or test runs...")
    
    if user_input:
        # 1. Render User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # 2. Get Agent Response
        with st.chat_message("assistant"):
            with st.spinner("Agent is running..."):
                try:
                    response = st.session_state.agent.invoke(
                        {"messages": [("user", user_input)]},
                        config=st.session_state.config
                    )
                    # Extract the last message content
                    agent_response = response["messages"][-1].content
                    
                    st.write(agent_response)
                    st.session_state.messages.append({"role": "assistant", "content": agent_response})
                    
                except Exception as e:
                    error_msg = f"An error occurred while executing request: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
else:
    st.info("💡 Please fill in your connection credentials and click **Save & Connect** in the sidebar to start talking with the agent.")
