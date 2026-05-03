# AI Agent Python Libraries Guide

This document details the Python libraries used in the AI Multi-Agent system, their importance, and how to set up the environment.

---

## 1. Core Frameworks

### LangChain
- **Importance:** The primary orchestration framework. It allows connecting the LLM (Llama 3.2) with tools (Search, Vector DB) and manages the logic between different agents.
- **Installation:** `pip install langchain`

### Streamlit
- **Importance:** Used to build the "AI Multi-Agent Studio" GUI. it transforms Python scripts into interactive web apps for a better user experience.
- **Installation:** `pip install streamlit`

---

## 2. LLM & Embedding Integrations

### LangChain-Ollama
- **Importance:** The specific bridge between LangChain and Ollama. It allows the Python code to communicate with your locally running Llama models.
- **Installation:** `pip install langchain-ollama`

### LangChain-HuggingFace & Sentence-Transformers
- **Importance:** These provide the "Semantic Memory". They convert text into mathematical vectors (Embeddings) using the `all-MiniLM-L6-v2` model so the agent can understand the "meaning" of your files.
- **Installation:** `pip install langchain-huggingface sentence-transformers`

---

## 3. Tools & Data Storage

### LangChain-Community
- **Importance:** Contains a collection of third-party integrations, such as the DuckDuckGo search tool and the FAISS vector store.
- **Installation:** `pip install langchain-community`

### DuckDuckGo-Search
- **Importance:** The engine that allows the Researcher Agent to browse the live internet for news and real-time data.
- **Installation:** `pip install duckduckgo-search`

### FAISS-CPU
- **Importance:** A high-performance local vector database. It stores the "Embeddings" of your local documents for fast semantic search.
- **Installation:** `pip install faiss-cpu`

---

## 4. Document Processing

### PyPDF
- **Importance:** Necessary for the Local Knowledge Agent to read and analyze PDF files placed in the `knowledge_base` folder.
- **Installation:** `pip install pypdf`

---

## Quick Setup Instructions

To install all required libraries at once, you can use the `requirements.txt` file provided in this directory:

```bash
pip install -r requirements.txt
```

*Note: Ensure you have Python 3.12+ installed and Ollama running in the background before executing the agents.*
