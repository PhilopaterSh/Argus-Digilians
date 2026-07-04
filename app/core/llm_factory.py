import os
from langchain_ollama import OllamaLLM

def build_llm(model_name: str) -> OllamaLLM:
    """
    Factory function for creating and configuring the Ollama LLM.
    """
    return OllamaLLM(
        model=model_name,
        timeout=3600,  # Increased to 1 hour for large models
        temperature=0.1,
        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
