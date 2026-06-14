import sys
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain.tools import tool


@tool 
def sum (a,b):
    '''
    to sum two nums 
    '''
    return a + b 


# 1. إعداد الموديل المحلي
llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0,
    num_ctx=4096,
    timeout=600
)

# 2. إعداد أداة البحث
tools = [DuckDuckGoSearchRun()]

# 3. جلب الـ Prompt القياسي لـ React Agent
prompt = hub.pull("hwchase17/react")

# 4. إنشاء الوكيل
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def ask_ai(question):
    print(f"\n[الوكيل الذكي]: جاري البحث والتفكير في سؤالك: {question}")
    try:
        full_prompt = f"البحث عن: {question}. أجب باللغة العربية فقط في النهاية."
        # استخدام التنسيق المطلوب من الـ React Prompt
        response = agent_executor.invoke({"input": full_prompt})
        print("\n" + "="*50)
        print(f"النتيجة النهائية:\n{response['output']}")
        print("="*50)
    except Exception as e:
        print(f"\nحدث خطأ: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "سعر الذهب اليوم في مصر عيار 21"
    ask_ai(query)
