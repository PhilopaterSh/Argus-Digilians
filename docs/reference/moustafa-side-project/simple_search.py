import sys
import json
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_ollama import ChatOllama

def simple_search_agent(question):
    print(f"\n[1/2] ╪¼╪º╪▒┘è ╪º┘ä╪¿╪¡╪½ ┘ü┘è ╪º┘ä╪Ñ┘å╪¬╪▒┘å╪¬ ╪╣┘å: {question}...")
    
    # 1. ╪Ñ╪╣╪»╪º╪» ┘à╪¡╪▒┘â ╪º┘ä╪¿╪¡╪½ ┘ä╪¼┘ä╪¿ 10 ┘å╪¬╪º╪ª╪¼ ┘ä╪╢┘à╪º┘å ╪º┘ä╪¡╪╡┘ê┘ä ╪╣┘ä┘ë ╪º┘ä╪│╪╣╪▒
    wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)
    
    try:
        search_results = search.run(question)
        if not search_results:
            print("┘ä┘à ┘è╪¬┘à ╪º┘ä╪╣╪½┘ê╪▒ ╪╣┘ä┘ë ┘å╪¬╪º╪ª╪¼ ┘ü┘è ╪º┘ä╪¿╪¡╪½.")
            return
    except Exception as e:
        print(f"┘ü╪┤┘ä ╪º┘ä╪¿╪¡╪½: {e}")
        return

    print(f"[2/2] ╪¼╪º╪▒┘è ╪¬╪¡┘ä┘è┘ä ╪º┘ä┘å╪¬╪º╪ª╪¼ ┘ê╪¬┘ä╪«┘è╪╡┘ç╪º ╪¿╪º╪│╪¬╪«╪»╪º┘à ╪º┘ä┘à┘ê╪»┘è┘ä ╪º┘ä┘à╪¡┘ä┘è (Llama 3.2 3B)...")

    # 2. ╪Ñ╪╣╪»╪º╪» ╪º┘ä┘à┘ê╪»┘è┘ä ╪º┘ä┘à╪¡┘ä┘è
    llm = ChatOllama(
        model="llama3.2:3b",
        temperature=0.1, # ╪¡╪▒╪º╪▒╪⌐ ┘à┘å╪«┘ü╪╢╪⌐ ┘ä╪╢┘à╪º┘å ╪º┘ä╪»┘é╪⌐ ┘ü┘è ╪º┘ä╪ú╪▒┘é╪º┘à
        timeout=600
    )

    # 3. ╪¿┘å╪º╪í ╪º┘ä┘Ç Prompt ╪¿╪┤┘â┘ä ╪º╪¡╪¬╪▒╪º┘ü┘è
    prompt = f"""
    Below are the search results for the query: "{question}"
    
    SEARCH RESULTS:
    {search_results}
    
    INSTRUCTION:
    1. Carefully read the search results.
    2. Extract the specific information requested (like prices, dates, etc.).
    3. Summarize the answer in clear Arabic.
    4. Mention the date if found in the results.
    
    Final Answer in Arabic:
    """

    try:
        response = llm.invoke(prompt)
        print("\n" + "="*50)
        print("╪º┘ä┘å╪¬┘è╪¼╪⌐ ╪º┘ä┘å┘ç╪º╪ª┘è╪⌐:")
        print(response.content)
        print("="*50)
    except Exception as e:
        print(f"┘ü╪┤┘ä ╪º┘ä┘à┘ê╪»┘è┘ä ┘ü┘è ╪º┘ä╪▒╪»: {e}")

if __name__ == "__main__":
    # ╪º╪│╪¬╪«╪»╪º┘à ╪│╪ñ╪º┘ä ╪º┘ü╪¬╪▒╪º╪╢┘è ╪Ñ╪░╪º ┘ä┘à ┘è╪¬┘à ╪¬┘ê┘ü┘è╪▒ ┘ê╪º╪¡╪»
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "╪│╪╣╪▒ ╪º┘ä╪░┘ç╪¿ ╪º┘ä┘è┘ê┘à ┘ü┘è ┘à╪╡╪▒ ╪╣┘è╪º╪▒ 21"
    simple_search_agent(query)
