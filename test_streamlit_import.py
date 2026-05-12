import streamlit as st
import paramiko
import sys
import os

st.write("Python Executable:", sys.executable)
st.write("Python Path:", sys.path)
st.write("Paramiko Version:", paramiko.__version__)
st.write("Paramiko File:", paramiko.__file__)
st.write("Current Directory:", os.getcwd())
