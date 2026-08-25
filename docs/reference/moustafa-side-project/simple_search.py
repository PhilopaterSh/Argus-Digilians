import sys
import json
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_ollama import ChatOllama

def simple_search_agent(question):
    print(f"\n[1/2] جاري البحث في الإنترنت عن: {question}...")
    
    # 1. إعداد محرك البحث لجلب 10 نتائج لضمان الحصول على السعر
    wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)
    
    try:
        search_results = search.run(question)
        if not search_results:
            print("لم يتم العثور على نتائج في البحث.")
            return
    except Exception as e:
        print(f"فشل البحث: {e}")
        return

    print(f"[2/2] جاري تحليل النتائج وتلخيصها باستخدام الموديل المحلي (Llama 3.2 3B)...")

    # 2. إعداد الموديل المحلي
    llm = ChatOllama(
        model="llama3.2:3b",
        temperature=0.1, # حرارة منخفضة لضمان الدقة في الأرقام
        timeout=600
    )

    # 3. بناء الـ Prompt بشكل احترافي
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
        print("النتيجة النهائية:")
        print(response.content)
        print("="*50)
    except Exception as e:
        print(f"فشل الموديل في الرد: {e}")

if __name__ == "__main__":
    # استخدام سؤال افتراضي إذا لم يتم توفير واحد
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "سعر الذهب اليوم في مصر عيار 21"
    simple_search_agent(query)
