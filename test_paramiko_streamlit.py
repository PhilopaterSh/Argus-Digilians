import streamlit as st
import sys
import os

st.write(f"Python Executable: {sys.executable}")
st.write(f"Python Version: {sys.version}")
st.write(f"CWD: {os.getcwd()}")
st.write(f"sys.path: {sys.path}")

try:
    import paramiko
    st.success("Successfully imported paramiko")
    st.write(f"Paramiko version: {paramiko.__version__}")
    st.write(f"Paramiko path: {paramiko.__file__}")
except ImportError as e:
    st.error(f"Failed to import paramiko: {e}")
