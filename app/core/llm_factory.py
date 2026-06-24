import os
from langchain_ollama import OllamaLLM


class NonStreamingOllamaLLM(OllamaLLM):
    """Subclass of OllamaLLM that disables streaming by default.

    Some parts of Argus request streaming tokens which can fail when the
    Ollama server disconnects (e.g., GPU mis-detection). This subclass forces
    non-streaming generation unless explicitly overridden by passing
    stream=True on a per-call basis.
    """

    def _generate_params(self, prompt: str, stop: list[str] | None = None, **kwargs):
        params = super()._generate_params(prompt, stop=stop, **kwargs)
        # Ensure stream defaults to False to avoid relying on streaming transport
        params["stream"] = kwargs.pop("stream", False)
        return params

    def _create_generate_stream(self, prompt: str, stop: list[str] | None = None, **kwargs):
        """Wrap parent generator and extract 'response' field properly.

        When stream=False, ollama.Client.generate() returns a single dict
        with all metadata (model, created_at, done, response, etc).
        We must extract only the 'response' field for each iteration so
        langchain_ollama's _stream_with_aggregation can process it correctly.
        """
        gen = super()._create_generate_stream(prompt, stop=stop, **kwargs)
        for part in gen:
            if isinstance(part, dict):
                # Extract response field if present; otherwise pass as-is
                if "response" in part:
                    yield {"response": part["response"], "done": part.get("done", False)}
                else:
                    # Pass through dicts that might be proper stream chunks
                    yield part
            elif isinstance(part, tuple):
                # Handle unexpected tuple format (legacy/version differences)
                try:
                    if len(part) == 2 and isinstance(part[0], str):
                        yield {"response": part[0], "done": part[1]}
                    else:
                        yield {"response": str(part)}
                except Exception:
                    yield {"response": str(part)}
            else:
                # Pass through strings or other types
                yield part


def build_llm(model_name: str) -> OllamaLLM:
    """
    Factory function for creating and configuring the Ollama LLM.
    Returns a NonStreamingOllamaLLM instance (streaming disabled by default).
    """
    return NonStreamingOllamaLLM(
        model=model_name,
        timeout=3600,           # Server timeout for inference (1 hour)
        temperature=0.2,        # Balanced for precision + slight creativity
        num_predict=4096,       # Max tokens (num_predict in Ollama)
        top_p=0.9,              # Logical filtering
        repeat_penalty=1.1,     # Frequency penalty equivalent
        presence_penalty=0.1,   # Presence penalty
        num_gpu=0,              # Force CPU usage (avoid GPU on hosts without GPU)
        # Increase httpx timeouts significantly to handle long CPU inference
        # Set to None for no timeout (allow unlimited time for inference)
        sync_client_kwargs={"timeout": None, "trust_env": False},
        async_client_kwargs={"timeout": None, "trust_env": False},
        # Also set client-level kwargs to avoid using environment proxies and to be explicit
        client_kwargs={"trust_env": False},
        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
