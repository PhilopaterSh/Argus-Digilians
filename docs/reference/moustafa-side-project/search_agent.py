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


# 1. ╪Ñ╪╣╪»╪º╪» ╪º┘ä┘à┘ê╪»┘è┘ä ╪º┘ä┘à╪¡┘ä┘è
llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0,
    num_ctx=4096,
    timeout=600
)

# 2. ╪Ñ╪╣╪»╪º╪» ╪ú╪»╪º╪⌐ ╪º┘ä╪¿╪¡╪½
tools = [DuckDuckGoSearchRun()]

# 3. ╪¼┘ä╪¿ ╪º┘ä┘Ç Prompt ╪º┘ä┘é┘è╪º╪│┘è ┘ä┘Ç React Agent
prompt = hub.pull("hwchase17/react")

# 4. ╪Ñ┘å╪┤╪º╪í ╪º┘ä┘ê┘â┘è┘ä
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def ask_ai(question):
    print(f"\n[╪º┘ä┘ê┘â┘è┘ä ╪º┘ä╪░┘â┘è]: ╪¼╪º╪▒┘è ╪º┘ä╪¿╪¡╪½ ┘ê╪º┘ä╪¬┘ü┘â┘è╪▒ ┘ü┘è ╪│╪ñ╪º┘ä┘â: {question}")
    try:
        full_prompt = f"╪º┘ä╪¿╪¡╪½ ╪╣┘å: {question}. ╪ú╪¼╪¿ ╪¿╪º┘ä┘ä╪║╪⌐ ╪º┘ä╪╣╪▒╪¿┘è╪⌐ ┘ü┘é╪╖ ┘ü┘è ╪º┘ä┘å┘ç╪º┘è╪⌐."
        # ╪º╪│╪¬╪«╪»╪º┘à ╪º┘ä╪¬┘å╪│┘è┘é ╪º┘ä┘à╪╖┘ä┘ê╪¿ ┘à┘å ╪º┘ä┘Ç React Prompt
        response = agent_executor.invoke({"input": full_prompt})
        print("\n" + "="*50)
        print(f"╪º┘ä┘å╪¬┘è╪¼╪⌐ ╪º┘ä┘å┘ç╪º╪ª┘è╪⌐:\n{response['output']}")
        print("="*50)
    except Exception as e:
        print(f"\n╪¡╪»╪½ ╪«╪╖╪ú: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "╪│╪╣╪▒ ╪º┘ä╪░┘ç╪¿ ╪º┘ä┘è┘ê┘à ┘ü┘è ┘à╪╡╪▒ ╪╣┘è╪º╪▒ 21"
    ask_ai(query)
