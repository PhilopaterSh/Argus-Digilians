import streamlit as st
import sys
import os

# إضافة المسار الرئيسي لكي يتمكن البرنامج من قراءة مجلد core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tools import WSLTools
from core.agent import ArgusBrain
from langchain_core.tools import Tool

# --- UI Setup ---
st.set_page_config(page_title="Argus AI Studio", layout="wide")

# تصميم بسيط واحترافي
st.markdown("""
    <style>
    .report-card {
        background-color: #111;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00ff41;
        font-family: monospace;
        color: #00ff41;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Argus AI Professional Studio")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    model = st.selectbox("Intelligence Model", ["WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest", "llama3.2:3b"])
    distro = st.text_input("WSL Distro", "kali-linux")

# Logic Initialization
wsl = WSLTools(distro=distro)

@st.cache_resource
def load_brain(model_name):
    # تعريف الأدوات للذكاء الاصطناعي
    tools = [
        Tool(name="Check_Reachability", func=wsl.check_reachability, description="Verify if a domain is alive via ping or HTTP. MUST be used first."),
        Tool(name="Recon_Suite", func=wsl.recon_suite, description="Run WhatWeb, Curl, and Wget analysis.")
    ]
    return ArgusBrain(model_name, tools)

# Main Interface
target = st.text_input("🎯 Target URL", "https://")

if st.button("RUN ANALYSIS"):
    if target:
        brain = load_brain(model)
        
        with st.status("🕵️ Working...", expanded=True) as status:
            st.write("Initializing reconnaissance suite...")
            report = wsl.recon_suite(target)
            
            st.markdown("### 📋 Reconnaissance Evidence")
            st.markdown(f"<div class='report-card'>{report.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
            
            st.write("AI is analyzing evidence...")
            analysis = brain.ask(f"Analyze this reconnaissance report for {target}. Report: {report}")
            
            st.markdown("### 🧠 AI Intelligence Report")
            st.info(analysis["output"])
            
            status.update(label="Analysis Finished!", state="complete")
