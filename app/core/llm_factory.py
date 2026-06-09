import os

from langchain_ollama import OllamaLLM


# Default Ollama server endpoint used when OLLAMA_HOST is not defined.
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"

# Default request timeout.
# Large local models may require more time to generate long security reports.
DEFAULT_TIMEOUT_SECONDS = 3600

# Low temperature keeps the model output more deterministic and consistent.
DEFAULT_TEMPERATURE = 0.1


def build_ollama_llm(
    model_name: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    temperature: float = DEFAULT_TEMPERATURE,
    base_url: str | None = None,
) -> OllamaLLM:
    """
    Create and configure a local Ollama language model.

    This factory function centralizes Ollama LLM creation so the rest of the
    application does not need to know the low-level configuration details.

    Configuration priority:
        1. Explicitly provided base_url argument.
        2. OLLAMA_HOST environment variable.
        3. DEFAULT_OLLAMA_BASE_URL fallback.

    Args:
        model_name:
            Name of the Ollama model to use, for example "llama3", "mistral",
            or any locally available Ollama model.

        timeout:
            Maximum time, in seconds, allowed for model response generation.

        temperature:
            Sampling temperature used by the model. Lower values produce more
            stable and deterministic responses.

        base_url:
            Optional Ollama server URL. If not provided, the function checks
            the OLLAMA_HOST environment variable, then falls back to the default
            local Ollama URL.

    Returns:
        OllamaLLM:
            Configured Ollama LLM instance ready for use by the agent.
    """

    # Resolve the Ollama server URL using explicit configuration first,
    # then environment configuration, then the local default.
    resolved_base_url = base_url or os.getenv(
        "OLLAMA_HOST",
        DEFAULT_OLLAMA_BASE_URL,
    )

    # Create the LangChain-compatible Ollama LLM instance.
    return OllamaLLM(
        model=model_name,
        timeout=timeout,
        temperature=temperature,
        base_url=resolved_base_url,
    )