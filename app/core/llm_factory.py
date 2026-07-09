import os
from langchain_ollama import ChatOllama, OllamaLLM

def build_llm(model_name: str) -> OllamaLLM:
    """
    Factory function for creating and configuring the Ollama LLM.

    Returns the plain completion-style `OllamaLLM` - `.invoke()` returns a
    bare string. Existing callers (`app/core/agent/nodes/reflective.py`,
    `app/core/rag/rag_engine.py`) depend on that string return directly
    (e.g. `response.strip()`); do not repoint this at `ChatOllama` without
    checking every caller first (see `build_chat_llm()` for why).
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


def build_chat_llm(model_name: str) -> ChatOllama:
    """
    Factory function for a chat-style Ollama LLM with real structured-output support.

    specs/018-structured-agent-reliability found, via direct live testing,
    that `OllamaLLM.with_structured_output(...)` raises `NotImplementedError`
    - LangChain's structured-output/schema-constrained decoding only works
    through Ollama's chat completions API (`ChatOllama`), not its plain
    completions API (`OllamaLLM`). This made every
    `react_workflow.py::_try_structured_action`/`_try_structured_final_answer`
    call silently fail and fall back to free-text parsing every single time,
    even after `018`'s fix - `ArgusBrain` was still built with `build_llm()`.
    Verified directly: `ChatOllama(...).with_structured_output(_ArgusAction)`
    returns a real, valid instance against the live model; `OllamaLLM`'s
    equivalent call raises immediately.

    Also sets `num_ctx` explicitly. Live testing (specs/018) hit
    `exceed_context_size_error` at Ollama's unset default (4096 tokens) -
    `ArgusBrain`'s RAG+Blackboard context fusion alone routinely runs
    ~6000+ tokens, well past that. `ollama show` confirms this model
    (qwen2 architecture, F16) supports up to 32768. `ARGUS_LLM_NUM_CTX`
    lets an operator tune this against their actual VRAM - this GPU is
    already near its limit (7.6B params at F16 = ~14GB of a 16GB card), so
    a large increase can force partial CPU offload (slow) or fail outright
    rather than silently degrading; 8192 is a conservative default chosen
    to leave headroom on a 16GB card, not the model's real ceiling.

    Returns:
        ChatOllama: `.invoke()` returns an `AIMessage` (not a bare string) -
        callers must use `.content`, not string methods directly on the
        result. Use `build_llm()` instead if a bare-string-returning LLM is
        needed.
    """
    return ChatOllama(
        model=model_name,
        client_kwargs={"timeout": 3600},
        temperature=0.1,
        num_ctx=int(os.getenv("ARGUS_LLM_NUM_CTX", "8192")),
        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    )
