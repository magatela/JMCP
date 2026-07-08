# Jira & Xray LangGraph Agent (JMCP)

This project provides a robust integration of Jira Core and Xray Test Management REST APIs with an agentic AI built using **LangGraph** and **LangChain**. It enables users to interact with Jira and Xray naturally through conversational prompts—allowing queries, issue creation, status transitions, test step management, and more.

---

## Features

- **Jira Core Client (`JiraAPI`)**: Direct HTTP client to query, create, update, delete, search (via JQL), and transition Jira issues.
- **Xray Test Management Client (`XrayAPI`)**: Client wrapper for test case operations, test steps, test runs/executions, and test results importing.
- **LangGraph Agent (`src/agent/`)**: ReAct agent using LangGraph to bind the APIs as standard LangChain tools, utilizing conversational memory to persist thread states.
- **Interactive CLI Runner (`src/run_agent.py`)**: Command line chatbot to execute the agent.

---

## Repository Structure

```
JMCP/
├── .env.example            # Template for required environment variables
├── requirements.txt        # Python dependency list
├── README.md               # Project documentation (this file)
└── src/
    ├── run_agent.py        # Interactive CLI runner for the agent
    ├── api/                # Low-level REST API clients
    │   ├── base_api.py     # Base RestAPIClient class
    │   ├── jira_api.py     # Client for Jira Core endpoints
    │   └── xray_api.py     # Client for Xray Test Management endpoints
    └── agent/              # LangGraph Agent logic
        ├── tools.py        # LangChain tools wrapping Jira/Xray functions
        └── graph.py        # LangGraph ReAct compiled graph logic
```

---

## Installation & Setup

1. **Clone or locate the workspace directory**:
   Ensure you are in the workspace folder:
   ```bash
   cd JMCP
   ```

2. **Set up a virtual environment (optional but recommended)**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   Install the required libraries listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory by copying the template:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and fill in your details:
   - **`JIRA_BASE_URL`**: Base URL of your Jira instance (e.g., `https://your-domain.atlassian.net/`).
   - **`JIRA_USER`**: Your Jira username or email address.
   - **`JIRA_PASSWORD`**: Your Jira API Token or password.
   - **`JIRA_PREFIX`**: The project prefix code (e.g. `PROJ`).
   - **`OPENAI_API_KEY`**: Your OpenAI API Key (necessary to run the LangGraph model).
   - **`ENABLE_XRAY`**: Set to `true` (default) to include Xray Test Management tools, or `false` to disable them.

---

## Usage

### 1. Conversational Agent (CLI Chat)
You can run the interactive agent via command line:
```bash
python src/run_agent.py
```
This loads your credentials, binds all Jira and Xray APIs as tool nodes, compiles the LangGraph agent, and launches a chat session.

**Example queries you can try:**
- *"Get details of the issue PROJ-101."*
- *"Find all open bugs in the project using JQL."*
- *"Create a new Test issue with summary 'Verify checkout process' and description 'Test description details'."*
- *"Transition issue PROJ-105. Check its available transitions first."*
- *[Xray]* *"List the test steps of the test case PROJ-200."*
- *[Xray]* *"Update the test run status of test run 1234 to PASS."*

### 2. Streamlit Web Interface (GUI)
You can run the web-based graphical user interface:
```bash
streamlit run src/app.py
```
This launches a browser-based application with:
*   An interactive sidebar to view/configure connection parameters and list active agent tools.
*   A clean, modern dark-themed chat layout to communicate with the agent.
*   Real-time status updates and errors logging.

### 3. Direct API Clients usage
If you want to use the API clients programmatically without the LLM agent:
```python
from api.jira_api import JiraAPI

jira = JiraAPI(
    base_url="https://your-domain.atlassian.net/",
    prefix="PROJ",
    user="your-user@email.com",
    password="your-api-token"
)

# Fetch project info
response = jira.get_project_info()
if response.ok:
    print(response.json())
```
