import streamlit as st
import subprocess
import os
import sys
import time
from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

# --- Page Configuration ---
st.set_page_config(
    page_title="Argus AI - Security Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced Custom CSS & HTML ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'JetBrains+Mono', monospace;
    }

    .main {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: #00ff41;
    }
    
    .stApp {
        background-color: transparent;
    }

    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: rgba(0, 0, 0, 0.6);
        border-radius: 15px;
        border: 1px solid #00ff41;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.2);
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #00ff41;
        text-transform: uppercase;
        letter-spacing: 5px;
        margin: 0;
    }

    /* Terminal Style Recon Box */
    .terminal-box {
        background-color: #000000;
        color: #00ff41;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #333;
        font-family: 'JetBrains+Mono', monospace;
        margin-top: 10px;
        white-space: pre-wrap;
    }

    /* Button Styling */
    .stButton>button {
        background-color: #00ff41 !important;
        color: black !important;
        font-weight: bold !important;
        border-radius: 5px !important;
        border: none !important;
        transition: 0.3s !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        background-color: #008f11 !important;
        box-shadow: 0 0 15px #00ff41 !important;
    }

    /* Sidebar Styling */
    .css-1d391kg {
        background-color: #0a0a0a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Custom Header ---
st.markdown("""
    <div class="main-header">
        <h1>Argus AI Security Studio</h1>
        <p style="color: #888;">Autonomous Intelligence & Reconnaissance Framework v1.0</p>
    </div>
    """, unsafe_allow_html=True)

# --- Logic Layer ---

DISTRO_NAME = "kali-linux"
MODEL_NAME = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"

def run_wsl_command(command: str) -> str:
    try:
        full_command = f"wsl -d {DISTRO_NAME} bash -c \"{command}\""
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True)
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Exception: {str(e)}"

def recon_workflow(url: str) -> str:
    placeholder = st.empty()
    with placeholder.container():
        st.write("📡 **Initializing Recon Subsystem...**")
        
        with st.status("Scanning Target...", expanded=True) as status:
            st.write("Executing WhatWeb Fingerprinting...")
            ww = run_wsl_command(f"whatweb {url}")
            
            st.write("Analyzing Headers (Curl)...")
            cl = run_wsl_command(f"curl -skI -A 'Mozilla/5.0' {url}")
            
            st.write("Fetching Content Structure (Wget)...")
            wg = run_wsl_command(f"wget -q -O - --no-check-certificate --user-agent='Mozilla/5.0' {url} | head -n 30")
            
            status.update(label="Scan Complete!", state="complete", expanded=False)
    
    return f"WHATWEB:\n{ww}\n\nCURL:\n{cl}\n\nWGET SNIPPET:\n{wg}"

@st.cache_resource
def get_agent():
    status_placeholder = st.empty()
    try:
        status_placeholder.warning("🧠 Waking up the AI Intelligence Core (this may take 1-2 minutes)...")
        llm = OllamaLLM(model=MODEL_NAME, timeout=120)
        
        # We'll skip the heavy 'Hi' invoke here to avoid blocking too long, 
        # or do a very short one.
        
        tools = [
            Tool(name="Recon_Workflow", func=recon_workflow, description="Combined recon tool."),
            Tool(name="WhatWeb", func=lambda u: run_wsl_command(f"whatweb {u}"), description="Fingerprinting."),
            Tool(name="Curl", func=lambda u: run_wsl_command(f"curl -skI {u}"), description="Headers."),
        ]
        template = """You are Argus AI, a senior security researcher.
Analyze the provided target carefully using your tools.
Format your final answer in a clear, structured way with emojis for readability.

Tools available:
{tools}

Use the following format:
Question: {input}
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
        
        status_placeholder.empty()
        return executor
    except Exception as e:
        status_placeholder.error(f"SYSTEM OVERLOAD: {str(e)}")
        return None

# --- UI Layout ---

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("System Status")
    st.success(f"Kali WSL: ONLINE")
    st.success(f"LLM: {MODEL_NAME}")
    
    st.markdown("---")
    url_input = st.text_input("Target URL", "https://example.com")
    run_btn = st.button("EXECUTE ANALYSIS")

with col2:
    st.subheader("Intelligence Output")
    if run_btn:
        if url_input:
            agent = get_agent()
            if agent:
                with st.spinner("Argus AI is processing..."):
                    # For demo purposes, we will call the recon workflow directly to show results clearly
                    # In a full app, the agent decides when to call it.
                    report = recon_workflow(url_input)
                    st.markdown("#### Found Data:")
                    st.markdown(f'<div class="terminal-box">{report}</div>', unsafe_allow_html=True)
                    
                    st.info("AI Analysis:")
                    # Simplified agent call for instant feedback
                    res = agent.invoke({"input": f"Based on this report for {url_input}, give me a security summary."})
                    st.write(res["output"])
            else:
                st.error("Ollama Engine Error. Check Connection.")
        else:
            st.warning("Input target URL.")

st.markdown("""
    <div style="position: fixed; bottom: 10px; right: 10px; color: #555; font-size: 0.8rem;">
        Argus Framework v1.0 | Security Intelligence Division
    </div>
    """, unsafe_allow_html=True)
