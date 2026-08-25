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
    # بحث بسيط عن الكلمات المفتاحية في الأسئلة السابقة
    for entry in memory:
        if question.lower() in entry["question"].lower():
            return entry
    return None

def smart_ai_agent(question):
    print(f"\n[?] السؤال: {question}")
    
    # 1. البحث في الذاكرة أولاً
    past_info = search_memory(question)
    if past_info:
        print(f"[!] وجدت معلومة مشابهة في ذاكرتي (بتاريخ {past_info['date']})...")
        print(f"\n[الذاكرة]: {past_info['answer']}")
        print("\nهل تريد تحديث هذه المعلومة ببحث جديد؟ (نعم/لا)")
        # في وضع السكريبت سنفترض لا إلا لو المستخدم طلب تحديث، لكن للتبسيط سنعرضها فقط
        return

    # 2. إذا لم توجد، ابحث في الإنترنت
    print(f"[1/2] لم أجد المعلومة في ذاكرتي. جاري البحث في الويب...")
    wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)
    
    try:
        search_results = search.run(question)
        if not search_results:
            print("لم يتم العثور على نتائج.")
            return
    except Exception as e:
        print(f"فشل البحث: {e}")
        return

    print(f"[2/2] جاري تحليل النتائج وتلخيصها...")

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
        print("النتيجة النهائية:")
        print(final_answer)
        print("="*50)
        
        # 3. حفظ النتيجة في الذاكرة للتعلم المستقبلي
        save_to_memory(question, final_answer)
        print(f"\n[✔] تم حفظ هذه المعلومة في ذاكرتي لسرعة الاسترجاع مستقبلاً.")
        
    except Exception as e:
        print(f"خطأ: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "ما هي Digilians"
    smart_ai_agent(query)
