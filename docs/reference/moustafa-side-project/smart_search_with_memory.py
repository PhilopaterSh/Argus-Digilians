import sys
import json
import os
from datetime import datetime
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_ollama import ChatOllama

MEMORY_FILE = "ai_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_to_memory(question, answer):
    memory = load_memory()
    memory.append({
        "question": question,
        "answer": answer,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=4)

def search_memory(question):
    memory = load_memory()
    # ╪¿╪¡╪½ ╪¿╪│┘è╪╖ ╪╣┘å ╪º┘ä┘â┘ä┘à╪º╪¬ ╪º┘ä┘à┘ü╪¬╪º╪¡┘è╪⌐ ┘ü┘è ╪º┘ä╪ú╪│╪ª┘ä╪⌐ ╪º┘ä╪│╪º╪¿┘é╪⌐
    for entry in memory:
        if question.lower() in entry["question"].lower():
            return entry
    return None

def smart_ai_agent(question):
    print(f"\n[?] ╪º┘ä╪│╪ñ╪º┘ä: {question}")
    
    # 1. ╪º┘ä╪¿╪¡╪½ ┘ü┘è ╪º┘ä╪░╪º┘â╪▒╪⌐ ╪ú┘ê┘ä╪º┘ï
    past_info = search_memory(question)
    if past_info:
        print(f"[!] ┘ê╪¼╪»╪¬ ┘à╪╣┘ä┘ê┘à╪⌐ ┘à╪┤╪º╪¿┘ç╪⌐ ┘ü┘è ╪░╪º┘â╪▒╪¬┘è (╪¿╪¬╪º╪▒┘è╪« {past_info['date']})...")
        print(f"\n[╪º┘ä╪░╪º┘â╪▒╪⌐]: {past_info['answer']}")
        print("\n┘ç┘ä ╪¬╪▒┘è╪» ╪¬╪¡╪»┘è╪½ ┘ç╪░┘ç ╪º┘ä┘à╪╣┘ä┘ê┘à╪⌐ ╪¿╪¿╪¡╪½ ╪¼╪»┘è╪»╪ƒ (┘å╪╣┘à/┘ä╪º)")
        # ┘ü┘è ┘ê╪╢╪╣ ╪º┘ä╪│┘â╪▒┘è╪¿╪¬ ╪│┘å┘ü╪¬╪▒╪╢ ┘ä╪º ╪Ñ┘ä╪º ┘ä┘ê ╪º┘ä┘à╪│╪¬╪«╪»┘à ╪╖┘ä╪¿ ╪¬╪¡╪»┘è╪½╪î ┘ä┘â┘å ┘ä┘ä╪¬╪¿╪│┘è╪╖ ╪│┘å╪╣╪▒╪╢┘ç╪º ┘ü┘é╪╖
        return

    # 2. ╪Ñ╪░╪º ┘ä┘à ╪¬┘ê╪¼╪»╪î ╪º╪¿╪¡╪½ ┘ü┘è ╪º┘ä╪Ñ┘å╪¬╪▒┘å╪¬
    print(f"[1/2] ┘ä┘à ╪ú╪¼╪» ╪º┘ä┘à╪╣┘ä┘ê┘à╪⌐ ┘ü┘è ╪░╪º┘â╪▒╪¬┘è. ╪¼╪º╪▒┘è ╪º┘ä╪¿╪¡╪½ ┘ü┘è ╪º┘ä┘ê┘è╪¿...")
    wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)
    
    try:
        search_results = search.run(question)
        if not search_results:
            print("┘ä┘à ┘è╪¬┘à ╪º┘ä╪╣╪½┘ê╪▒ ╪╣┘ä┘ë ┘å╪¬╪º╪ª╪¼.")
            return
    except Exception as e:
        print(f"┘ü╪┤┘ä ╪º┘ä╪¿╪¡╪½: {e}")
        return

    print(f"[2/2] ╪¼╪º╪▒┘è ╪¬╪¡┘ä┘è┘ä ╪º┘ä┘å╪¬╪º╪ª╪¼ ┘ê╪¬┘ä╪«┘è╪╡┘ç╪º...")

    llm = ChatOllama(model="llama3.2:3b", temperature=0.1, timeout=600)

    prompt = f"""
    Below are the search results for: "{question}"
    RESULTS: {search_results}
    Instruction: Provide a detailed answer in Arabic.
    """

    try:
        response = llm.invoke(prompt)
        final_answer = response.content
        
        print("\n" + "="*50)
        print("╪º┘ä┘å╪¬┘è╪¼╪⌐ ╪º┘ä┘å┘ç╪º╪ª┘è╪⌐:")
        print(final_answer)
        print("="*50)
        
        # 3. ╪¡┘ü╪╕ ╪º┘ä┘å╪¬┘è╪¼╪⌐ ┘ü┘è ╪º┘ä╪░╪º┘â╪▒╪⌐ ┘ä┘ä╪¬╪╣┘ä┘à ╪º┘ä┘à╪│╪¬┘é╪¿┘ä┘è
        save_to_memory(question, final_answer)
        print(f"\n[Γ£ö] ╪¬┘à ╪¡┘ü╪╕ ┘ç╪░┘ç ╪º┘ä┘à╪╣┘ä┘ê┘à╪⌐ ┘ü┘è ╪░╪º┘â╪▒╪¬┘è ┘ä╪│╪▒╪╣╪⌐ ╪º┘ä╪º╪│╪¬╪▒╪¼╪º╪╣ ┘à╪│╪¬┘é╪¿┘ä╪º┘ï.")
        
    except Exception as e:
        print(f"╪«╪╖╪ú: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "┘à╪º ┘ç┘è Digilians"
    smart_ai_agent(query)
