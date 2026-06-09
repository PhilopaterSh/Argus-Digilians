# rag_gui.py

import streamlit as st
from dotenv import load_dotenv

from rag_pipeline.retrieval_generation import get_retriever, get_llm_chain

load_dotenv()

st.set_page_config(
    page_title="RAG Tester",
    page_icon="🎯",
    layout="centered"
)

st.title("🎯 RAG Testing Dashboard")
st.markdown("A smart interface for searching vulnerability reports and generating analytical answers.")
st.divider()


@st.cache_resource
def load_backend():
    return get_retriever(), get_llm_chain()


retriever, chain = load_backend()

query = st.text_input(
    "🔍 Type your question here. Example: What vulnerabilities were found and how can they be fixed?"
)

if st.button("Search & Analyze 🚀"):
    if not query:
        st.error("Please write a question first!")
    else:
        with st.spinner("Searching and analyzing the data..."):

            results = retriever.invoke(query)

            if not results:
                st.warning("No matching information was found in the database.")
            else:
                st.success(f"Found {len(results)} relevant chunks! Generating analysis...")

                context_text = "\n\n".join(
                    document.page_content for document in results
                )

                final_response = chain.invoke({
                    "context": context_text,
                    "question": query
                })

                st.markdown("### 🤖 Analyst Report")

                if hasattr(final_response, "content"):
                    st.info(final_response.content)
                elif isinstance(final_response, dict):
                    st.info(
                        final_response.get("text")
                        or final_response.get("output")
                        or final_response.get("answer")
                        or str(final_response)
                    )
                else:
                    st.info(str(final_response))

                st.divider()
                st.markdown("#### 📄 Raw Data Sources for Validation")

                for index, document in enumerate(results, 1):
                    source = document.metadata.get("source", "Unknown")

                    with st.expander(
                        f"📌 Raw JSON {index} | Source: {source}",
                        expanded=False
                    ):
                        st.code(document.page_content, language="json")