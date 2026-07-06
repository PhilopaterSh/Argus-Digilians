import os
from langchain_ollama import OllamaLLM

def build_llm(model_name: str) -> OllamaLLM:
    """
    Factory function for creating and configuring the Ollama LLM.
    """
    return OllamaLLM(
        model=model_name,
        # `timeout` is not a field of OllamaLLM itself - it must go through
        # client_kwargs, which is forwarded to the underlying ollama.Client.
        # A bare `timeout=` kwarg here is silently dropped and has no effect.
        client_kwargs={"timeout": 3600},  # 1 hour, for large models
        temperature=0.1,
        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
