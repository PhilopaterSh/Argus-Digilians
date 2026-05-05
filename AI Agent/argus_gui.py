import streamlit as st
import subprocess
import os
import sys
import time
from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

# --- Configuration & Setup ---
DISTRO_NAME = "kali-linux"
MODEL_NAME = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B" # Or "dolphin-llama3"

st.set_page_config(page_title="Argus AI - Security Studio", page_icon="🛡️", layout="wide")

# Custom CSS for a dark, professional look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stTextInput > div > div > input {
        background-color: #262730;
        color: white;
    }
    .recon-box {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #4CAF50;
        margin-bottom: 20px;
    }
    .stHeader {
        color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Tool Definitions ---

def run_wsl_command(command: str) -> str:
    try:
        full_command = f"wsl -d {DISTRO_NAME} bash -c \"{command}\""
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Exception: {str(e)}"

def whatweb_tool(url: str) -> str:
    return run_wsl_command(f"whatweb {url}")

def curl_tool(url: str) -> str:
    return run_wsl_command(f"curl -skI -A 'Mozilla/5.0' {url}")

def wget_tool(url: str) -> str:
    # Use -q to keep it quiet, and head to get a snippet
    return run_wsl_command(f"wget -q -O - --no-check-certificate --user-agent='Mozilla/5.0' {url} | head -n 30")

def recon_workflow(url: str) -> str:
    st.info(f"🔍 Launching Recon Workflow for {url}...")
    
    with st.status("Gathering Intelligence...", expanded=True) as status:
        st.write("Running WhatWeb Fingerprinting...")
        whatweb_res = whatweb_tool(url)
        
        st.write("Analyzing HTTP Headers with Curl...")
        curl_res = curl_tool(url)
        
        st.write("Fetching Content Snippet with Wget...")
        wget_res = wget_tool(url)
        
        status.update(label="Intelligence Gathered!", state="complete", expanded=False)

    report = f"""
### --- Recon Report for {url} ---
**WhatWeb:**
{whatweb_res}

**Headers:**
{curl_res}

**Snippet:**
{wget_res}
"""
    return report

# --- LangChain Agent Setup ---

@st.cache_resource
def init_agent():
    try:
        llm = OllamaLLM(model=MODEL_NAME)
        
        tools = [
            Tool(
                name="Recon_Workflow",
                func=recon_workflow,
                description="Use this for initial website analysis. It runs WhatWeb, Curl, and Wget."
            ),
            Tool(name="WhatWeb", func=whatweb_tool, description="Identify web technologies."),
            Tool(name="Curl", func=curl_tool, description="Analyze HTTP headers."),
            Tool(name="Wget", func=wget_tool, description="Fetch page content.")
        ]

        template = """You are Argus AI, a senior security researcher.
Analyze the provided target carefully using your tools.
Format your final answer in a clear, structured way with emojis for readability.

Tools available: {tools}

Use this format:
Question: {input}
Thought: {agent_scratchpad}
Action: [{tool_names}] (pick one)
Action Input: the input
Observation: result...
... (repeat)
Final Answer: your summary

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    except Exception as e:
        st.error(f"Failed to initialize Agent: {e}")
        return None

# --- Streamlit UI ---

st.title("🛡️ Argus AI Security Studio")
st.markdown("---")

agent_executor = init_agent()

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.write(f"**Target Distro:** {DISTRO_NAME}")
    st.write(f"**AI Model:** {MODEL_NAME}")
    st.markdown("---")
    st.info("Argus is connected to Kali Linux WSL and ready for reconnaissance.")

# Main Input
target_url = st.text_input("Enter Target URL (e.g., https://example.com)", placeholder="https://...")

if st.button("Start Analysis"):
    if target_url:
        if not target_url.startswith("http"):
            st.error("Please enter a valid URL starting with http:// or https://")
        elif agent_executor:
            with st.spinner("Argus AI is thinking..."):
                try:
                    # To show the 'Thinking' process in UI, we can use a callback or just capture output
                    # For simplicity, we'll run the agent and show the result
                    response = agent_executor.invoke({"input": f"Perform a full recon on {target_url} and summarize the findings."})
                    
                    st.success("Analysis Complete!")
                    st.markdown("### 🤖 Argus Final Summary")
                    st.markdown(response["output"])
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Agent not initialized. Ensure Ollama is running.")
    else:
        st.warning("Please enter a URL first.")

st.markdown("---")
st.caption("Argus Security Framework - May 2026")
