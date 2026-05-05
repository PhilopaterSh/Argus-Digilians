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
        Tool(name="Recon_Suite", func=wsl.recon_suite, description="Run WhatWeb, Curl, and Wget.")
    ]
    return ArgusBrain(model_name, tools)

# Main Interface
target = st.text_input("🎯 Target URL", "https://")

if st.button("RUN ANALYSIS"):
    if target:
        brain = load_brain(model)
        
        with st.status("🕵️ Working...", expanded=True) as status:
            st.write("Extracting technology fingerprint...")
            data = wsl.recon_suite(target)
            
            st.markdown("### 📋 Raw Evidence")
            st.markdown(f"<div class='report-card'><b>WHATWEB:</b><br>{data['whatweb']}</div>", unsafe_allow_html=True)
            
            st.write("AI is analyzing findings...")
            analysis = brain.ask(f"Analyze this site: {target}. Findings: {data}")
            
            st.markdown("### 🧠 AI Intelligence Report")
            st.info(analysis["output"])
            
            status.update(label="Analysis Finished!", state="complete")
