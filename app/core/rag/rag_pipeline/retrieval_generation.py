# rag_pipeline/retrieval_generation.py

# 1. Replace Google libraries with local libraries compatible with Ollama
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

# Import the new variables, including the local server URL
from config import CHROMA_DB_DIR, EMBEDDING_MODEL, LLM_MODEL, OLLAMA_BASE_URL


def get_retriever():
    """
    Connect to ChromaDB and centrally configure the retriever settings
    using local embeddings.
    """

    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL
    )

    vector_db = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings
    )

    # --- The critical change is here ---
    # Changed the search_type to regular similarity search and removed the score_threshold
    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 3
        }
    )

    return retriever


def get_llm_chain():
    """
    Configure the local WhiteRabbitNeo LLM and the prompt template.
    """

    # 3. Call the local model, WhiteRabbitNeo, through OllamaLLM
    llm = OllamaLLM(
        model=LLM_MODEL,
        temperature=0.1,  # Very low temperature to ensure commitment to security data and reduce hallucination
        base_url=OLLAMA_BASE_URL
    )

    # Your security prompt and rules are excellent, so they will remain unchanged
    prompt_template = """You are an expert Cybersecurity Analyst.

Use only the following JSON context extracted from vulnerability reports to answer the user's question.

Rules:
- Do not invent information.
- If the answer is not in the context, say:
  "The information is not available in the provided reports."
- Write clearly and professionally.
- Mention the vulnerability name, severity, impact, and remediation if available.

Context:
{context}

Question:
{question}

Professional Answer:
"""

    prompt = PromptTemplate.from_template(prompt_template)

    # Combine the prompt and the LLM into one chain, creating the pipeline
    return prompt | llm