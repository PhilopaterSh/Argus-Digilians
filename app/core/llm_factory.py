import os
from langchain_ollama import OllamaLLM

def build_llm(model_name: str) -> OllamaLLM:
    """
    Factory function for creating and configuring the Ollama LLM.
    Optimized for Security Operations: Low temperature for precision,
    penalties to avoid loops, and top_p for logical filtering.
    """
    return OllamaLLM(
        model=model_name,
        timeout=3600,
        temperature=0.2,       # Balanced for precision + slight creativity
        num_predict=4096,      # Max tokens (num_predict in Ollama)
        top_p=0.9,             # Logical filtering
        repeat_penalty=1.1,    # Frequency penalty equivalent
        presence_penalty=0.1,  # Presence penalty
        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
