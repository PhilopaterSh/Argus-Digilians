# Minimal placeholder for Argus GUI Studio
# This provides a simple Streamlit-compatible entrypoint so LAUNCH_STUDIO
# can import and run the application during development/testing.

import sys

def main():
    try:
        import streamlit as st
    except Exception:
        print("Streamlit is not installed in this Python environment.")
        print("To run the GUI, install requirements: python -m pip install streamlit")
        # Keep process alive briefly so the launcher output is visible
        return

    st.title("Argus Security Studio (Placeholder)")
    st.write("This is a minimal placeholder GUI. Replace app/GUI/studio.py with the real UI.")

if __name__ == '__main__':
    main()
