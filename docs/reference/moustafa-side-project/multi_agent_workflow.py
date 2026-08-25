import os
import time
import json
import requests
import re
import itertools
from datetime import datetime
import unicodedata
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ╪¬╪¡┘à┘è┘ä ╪º┘ä╪Ñ╪╣╪»╪º╪»╪º╪¬ ┘à┘å ┘à┘ä┘ü .env
load_dotenv(os.path.join("C:\\AI_Agents_Project", ".env"))

# 1. ╪º┘ä╪Ñ╪╣╪»╪º╪»╪º╪¬
PRIMARY_MODEL = "deepseek/deepseek-chat"
BACKUP_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
FALLBACK_MODEL = "google/gemini-flash-1.5-8b"

BASE_DIR = "C:\\AI_Agents_Project"
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
MEMORY_FILE = os.path.join(BASE_DIR, "ai_memory.json")

# ╪¼┘à╪╣ ┘â╪º┘ü╪⌐ ┘à┘ü╪º╪¬┘è╪¡ API ╪º┘ä┘à╪¬╪º╪¡╪⌐
api_keys = [os.getenv(f"OPENROUTER_API_KEY_{i}") for i in range(1, 11) if os.getenv(f"OPENROUTER_API_KEY_{i}")]
if not api_keys:
    single_key = os.getenv("OPENROUTER_API_KEY")
    if single_key:
        api_keys = [single_key]

print(f"[ΓÅ│] ╪¬┘à ╪º┘ä╪╣╪½┘ê╪▒ ╪╣┘ä┘ë {len(api_keys)} ┘à┘ü╪º╪¬┘è╪¡ API. ╪¼╪º╪▒┘è ╪┤╪¡┘å ╪º┘ä┘å╪╕╪º┘à ╪º┘ä╪º╪│╪¬╪«╪¿╪º╪▒╪º╪¬┘è ╪º┘ä┘à╪¬┘â╪º┘à┘ä...")
hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

class ProMultiAgentSystem:
    def __init__(self):
        if not api_keys:
            raise ValueError("[!] ╪«╪╖╪ú: ┘ä┘à ┘è╪¬┘à ╪º┘ä╪╣╪½┘ê╪▒ ╪╣┘ä┘ë ╪ú┘è ┘à┘ü╪º╪¬┘è╪¡ API.")
        
        self.key_cycle = itertools.cycle(api_keys)
        self.current_key = next(self.key_cycle)
        self.max_tokens = 1500
        self._init_llms(PRIMARY_MODEL)
        
        self.memory = self._load_memory()
        self.state = {
            "task": "",
            "raw_data": "",
            "analysis": "",
            "debate": "",
            "fact_check": "",
            "feedback": "None",
            "iterations": 0,
            "past_context": self._get_past_context(),
            "sources": []
        }
        self._ensure_dirs()

    def _rotate_key(self):
        self.current_key = next(self.key_cycle)
        print(f"[≡ƒöä] ╪¬┘à ╪¬╪¿╪»┘è┘ä ┘à┘ü╪¬╪º╪¡ API ┘ä╪¬┘ê╪▓┘è╪╣ ╪º┘ä╪╢╪║╪╖...")

    def _init_llms(self, model_name):
        self.current_model = model_name
        self.llm_fast = ChatOpenAI(model=model_name, api_key=self.current_key, base_url="https://openrouter.ai/api/v1", temperature=0.1, max_tokens=self.max_tokens, timeout=300)
        self.llm_smart = ChatOpenAI(model=model_name, api_key=self.current_key, base_url="https://openrouter.ai/api/v1", temperature=0.1, max_tokens=self.max_tokens, timeout=300)
        self.llm_creative = ChatOpenAI(model=model_name, api_key=self.current_key, base_url="https://openrouter.ai/api/v1", temperature=0.3, max_tokens=self.max_tokens, timeout=300)

    def _ensure_dirs(self):
        for d in [KNOWLEDGE_BASE_DIR, REPORTS_DIR]:
            if not os.path.exists(d): os.makedirs(d)

    def _load_memory(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except:
                    return {"sessions": []}
        return {"sessions": []}

    def _save_memory(self):
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=4)

    def _get_past_context(self):
        if not self.memory.get("sessions"): return "┘ä╪º ╪¬┘ê╪¼╪» ╪«╪¿╪▒╪º╪¬ ╪│╪º╪¿┘é╪⌐."
        last_sessions = self.memory["sessions"][-3:]
        context = "\n".join([f"- ┘à┘ç┘à╪⌐: {s.get('task','')}\n  ┘à┘ä╪«╪╡: {s.get('summary','')}" for s in last_sessions])
        return context

    def robust_invoke(self, agent_type, prompt_template, inputs):
        models_to_try = [PRIMARY_MODEL, BACKUP_MODEL, FALLBACK_MODEL]
        for model in models_to_try:
            self._init_llms(model)
            llm = self.llm_smart if agent_type == "smart" else (self.llm_fast if agent_type == "fast" else self.llm_creative)
            chain = prompt_template | llm | StrOutputParser()
            for key_attempt in range(len(api_keys)):
                try:
                    return chain.invoke(inputs)
                except Exception as e:
                    error_str = str(e).lower()
                    if any(code in error_str for code in ["429", "402", "rate_limit", "insufficient_quota", "credit"]):
                        print(f"[ΓÅ│] ╪╢╪║╪╖ ╪ú┘ê ╪º┘å╪¬┘ç╪º╪í ╪▒╪╡┘è╪» ({model}). ╪¼╪º╪▒┘è ╪¬╪¿╪»┘è┘ä ╪º┘ä┘à┘ü╪¬╪º╪¡...")
                        self._rotate_key()
                        self._init_llms(model)
                        time.sleep(5)
                    elif "404" in error_str:
                        print(f"[ΓÜá∩╕Å] ╪º┘ä┘å┘à┘ê╪░╪¼ {model} ╪║┘è╪▒ ┘à╪¬╪º╪¡. ╪¬╪¼╪▒╪¿╪⌐ ╪º┘ä╪¿╪»┘è┘ä...")
                        break
                    else:
                        print(f"[ΓÜá∩╕Å] ╪«╪╖╪ú: {e}. ┘à╪¡╪º┘ê┘ä╪⌐ ╪¬╪¿╪»┘è┘ä ╪º┘ä┘à┘ü╪¬╪º╪¡...")
                        self._rotate_key()
                        self._init_llms(model)
                        time.sleep(2)
            print(f"[≡ƒöä] ╪º┘ä╪º┘å╪¬┘é╪º┘ä ┘ä┘ä┘å┘à┘ê╪░╪¼ ╪º┘ä╪¬╪º┘ä┘è...")
        return "ΓÜá∩╕Å ┘ü╪┤┘ä╪¬ ╪º┘ä┘à╪¡╪º┘ê┘ä╪º╪¬ ╪º┘ä╪│╪¡╪º╪¿┘è╪⌐. ┘è╪▒╪¼┘ë ╪º┘ä┘à╪¡╪º┘ê┘ä╪⌐ ┘ä╪º╪¡┘é╪º┘ï."

    def local_rag_agent(self, task):
        print(f"\n[1/7] ≡ƒôÜ Local Agent (RAG): ╪º┘ä╪¿╪¡╪½ ╪º┘ä┘à╪¡┘ä┘è...")
        try:
            loaders = [
                DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.txt", loader_cls=TextLoader),
                DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
                DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.md", loader_cls=TextLoader)
            ]
            documents = []
            for loader in loaders: documents.extend(loader.load())
            if not documents: return "┘ä╪º ╪¬┘ê╪¼╪» ┘à┘ä┘ü╪º╪¬ ┘à╪¡┘ä┘è╪⌐."
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
            splits = text_splitter.split_documents(documents)
            vectorstore = FAISS.from_documents(splits, hf_embeddings)
            results = vectorstore.similarity_search(task, k=3)
            return "\n".join([doc.page_content for doc in results])
        except Exception as e:
            return f"╪«╪╖╪ú RAG: {e}"

    def researcher_agent(self, task):
        print(f"[2/7] ≡ƒöì Researcher Agent: ╪º╪│╪¬┘é╪╡╪º╪í ╪º┘ä┘ê┘è╪¿ ┘ê╪º┘ä┘à╪╕┘ä┘à...")
        from langchain_community.tools import DuckDuckGoSearchRun
        from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
        wrapper = DuckDuckGoSearchAPIWrapper(max_results=10)
        search = DuckDuckGoSearchRun(api_wrapper=wrapper)
        try:
            results = search.run(task)
            links = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', results)
            for link in links: self.state["sources"].append(link)
            return results
        except Exception as e:
            return f"Researcher Error: {e}"

    def darkweb_researcher_agent(self, task):
        print(f"[≡ƒò╡∩╕Å] DarkWeb Agent: ╪¼╪º╪▒┘è ╪º┘ä╪¿╪¡╪½ ┘ü┘è ╪º┘ä┘ü╪╢╪º╪í ╪º┘ä┘à╪╕┘ä┘à...")
        url = f"https://ahmia.fi/search/?q={task}"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('li', class_='result')
                dark_info = []
                for res in results[:10]:
                    link = res.find('cite').text if res.find('cite') else "No Link"
                    snippet = res.find('p').text if res.find('p') else "No Snippet"
                    dark_info.append(f"Link: {link}\nSnippet: {snippet}")
                    if ".onion" in link: self.state["sources"].append(f"Dark Web Link: {link}")
                return "\n\n".join(dark_info) if dark_info else "┘ä┘à ┘è╪¬┘à ╪º┘ä╪╣╪½┘ê╪▒ ╪╣┘ä┘ë ┘å╪¬╪º╪ª╪¼ ┘à╪╕┘ä┘à╪⌐."
            return "┘ü╪┤┘ä ╪º┘ä┘ê╪╡┘ê┘ä ┘ä┘à╪¡╪▒┘â ╪º┘ä╪¿╪¡╪½ ╪º┘ä┘à╪╕┘ä┘à."
        except Exception as e:
            return f"╪«╪╖╪ú DarkWeb: {e}"

    def analyst_agent(self, raw_data):
        print(f"[3/7] ≡ƒºá Analyst Agent: ╪¬╪¡┘ä┘è┘ä ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪º┘ä┘à╪│╪¬╪«╪▒╪¼╪⌐...")
        prompt = ChatPromptTemplate.from_template("""╪ú┘å╪¬ ┘à╪¡┘ä┘ä ╪¿┘è╪º┘å╪º╪¬ ╪º╪│╪¬╪«╪¿╪º╪▒╪º╪¬┘è. ┘é╪»┘à ╪¬╪¡┘ä┘è┘ä╪º┘ï ╪┤╪º┘à┘ä╪º┘ï ┘ä┘ä╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪¬╪º┘ä┘è╪⌐:
        ╪│┘è╪º┘é ╪│╪º╪¿┘é: {past_context}
        ╪º┘ä┘à┘ç┘à╪⌐: {task}
        ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪«╪º┘à: {raw_data}
        ╪º┘ä┘à╪╖┘ä┘ê╪¿: ╪º╪│╪¬╪«┘ä╪╡ ╪º┘ä╪¡┘é╪º╪ª┘é ┘ê╪º┘ä╪¬┘ç╪»┘è╪»╪º╪¬ ┘à╪╣ ╪º┘ä╪¡┘ü╪º╪╕ ╪╣┘ä┘ë ╪º┘ä╪▒┘ê╪º╪¿╪╖ ╪¡┘é┘è┘é┘è╪⌐ ┘ê┘â┘à╪º ┘ç┘è.""")
        self.state["analysis"] = self.robust_invoke("smart", prompt, {
            "task": self.state["task"], "raw_data": raw_data, "past_context": self.state["past_context"]
        })

    def debater_agent(self, analysis):
        print(f"[4/7] ΓÜû∩╕Å Debater Agent (Adversarial): ╪¬╪¡╪»┘è ╪º┘ä┘à╪╣┘ä┘ê┘à╪º╪¬...")
        prompt = ChatPromptTemplate.from_template("""╪ú┘å╪¬ "┘à╪¡╪º┘à┘è ╪º┘ä╪┤┘è╪╖╪º┘å" ┘ê╪«╪¿┘è╪▒ ┘ü┘è ┘â╪┤┘ü ╪º┘ä╪¬╪╢┘ä┘è┘ä. 
        ┘à┘ç┘à╪¬┘â ┘ç┘è ╪º┘ä╪¬╪┤┘â┘è┘â ┘ü┘è ╪º┘ä╪¬╪¡┘ä┘è┘ä ╪º┘ä╪¬╪º┘ä┘è╪î ╪«╪º╪╡╪⌐ ╪º┘ä┘à╪╣┘ä┘ê┘à╪º╪¬ ╪º┘ä┘à╪│╪¬┘à╪»╪⌐ ┘à┘å ╪º┘ä┘ê┘è╪¿ ╪º┘ä┘à╪╕┘ä┘à:
        ╪º┘ä╪¬╪¡┘ä┘è┘ä: {analysis}
        ╪º╪¿╪¡╪½ ╪╣┘å ╪º┘ä┘ü╪«╪º╪«╪î ╪º┘ä╪¬╪╢┘ä┘è┘ä╪î ┘ê╪º┘ä╪º╪»╪╣╪º╪í╪º╪¬ ╪║┘è╪▒ ╪º┘ä┘à┘ê╪½┘é╪⌐. ┘é╪º╪▒┘å ┘à╪╣ ┘à╪╣╪º┘è┘è╪▒ NIST/MITRE.""")
        self.state["debate"] = self.robust_invoke("creative", prompt, {"analysis": analysis})

    def fact_checker_agent(self):
        print(f"[5/7] Γ£à Fact Checker Agent: ╪¬╪»┘é┘è┘é ╪º┘ä╪¡┘é╪º╪ª┘é...")
        prompt = ChatPromptTemplate.from_template("""┘ê╪º╪▓┘å ╪¿┘è┘å ╪º┘ä╪¬╪¡┘ä┘è┘ä ╪º┘ä╪ú╪╡┘ä┘è ┘ê╪º╪╣╪¬╪▒╪º╪╢╪º╪¬ ┘ê┘â┘è┘ä ╪º┘ä┘à╪╣╪º╪▒╪╢╪⌐ (Debater).
        ╪º┘ä╪¬╪¡┘ä┘è┘ä: {analysis}
        ╪º┘ä┘à╪╣╪º╪▒╪╢╪⌐: {debate}
        ╪ú╪╣╪╖┘É ╪º┘ä╪¡┘â┘à ╪º┘ä┘å┘ç╪º╪ª┘è ╪¡┘ê┘ä ┘à╪º ┘ç┘ê ╪¡┘é┘è┘é┘è ┘ê┘à╪º ┘ç┘ê ┘à╪┤┘â┘ê┘â ┘ü┘è┘ç.""")
        self.state["fact_check"] = self.robust_invoke("smart", prompt, {
            "analysis": self.state["analysis"], "debate": self.state["debate"]
        })

    def reviewer_agent(self):
        print(f"[6/7] ΓÜû∩╕Å Reviewer Agent: ┘à╪▒╪º╪¼╪╣╪⌐ ╪º┘ä╪¼┘ê╪»╪⌐...")
        prompt = ChatPromptTemplate.from_template("╪▒╪º╪¼╪╣ ╪¼┘ê╪»╪⌐ ╪º┘ä╪¬╪¡┘ä┘è┘ä ╪º┘ä┘å┘ç╪º╪ª┘è ┘ê╪º┘ä╪¬╪»┘é┘è┘é: {fact_check}")
        return self.robust_invoke("creative", prompt, {"fact_check": self.state["fact_check"]})

    def writer_agent(self):
        print(f"[7/7] ≡ƒô¥ Writer Agent: ╪╡┘è╪º╪║╪⌐ ╪º┘ä╪¬┘é╪▒┘è╪▒ ╪º┘ä┘à┘ê╪½┘é...")
        unique_sources = list(set(self.state["sources"]))
        sources_list = "\n".join([f"- {s}" for s in unique_sources])
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        prompt = ChatPromptTemplate.from_template("""╪╡╪║ ╪¬┘é╪▒┘è╪▒╪º┘ï ╪º╪│╪¬╪«╪¿╪º╪▒╪º╪¬┘è╪º┘ï ╪º╪¡╪¬╪▒╪º┘ü┘è╪º┘ï ╪¿┘Ç Markdown.
        ╪º┘ä╪¬┘ê┘é┘è╪¬: {current_time}
        ╪º┘ä╪¬╪¡┘ä┘è┘ä: {analysis}
        ╪º╪╣╪¬╪▒╪º╪╢╪º╪¬ ╪º┘ä┘à╪╣╪º╪▒╪╢: {debate}
        ╪¬╪»┘é┘è┘é ╪º┘ä╪¡┘é╪º╪ª┘é: {fact_check}
        ╪º┘ä┘à╪╡╪º╪»╪▒: {sources}
        ┘è╪¼╪¿ ╪ú┘å ┘è╪¡╪¬┘ê┘è ╪º┘ä╪¬┘é╪▒┘è╪▒ ╪╣┘ä┘ë ╪ú┘é╪│╪º┘à: ╪º┘ä┘à╪╣┘ä┘ê┘à╪º╪¬ ╪º┘ä┘à╪ñ┘â╪»╪⌐╪î ╪¬╪¡╪░┘è╪▒╪º╪¬ ╪º┘ä┘à╪╣╪º╪▒╪╢╪⌐╪î ┘ê╪º┘ä┘à╪╡╪º╪»╪▒ ╪º┘ä┘à┘ê╪½┘é╪⌐.""")
        return self.robust_invoke("creative", prompt, {
            "current_time": current_time, "analysis": self.state["analysis"], 
            "debate": self.state["debate"], "fact_check": self.state["fact_check"], "sources": sources_list
        })

    def memory_agent(self, final_report):
        """┘ê┘â┘è┘ä ╪º┘ä╪░╪º┘â╪▒╪⌐ (Memory Agent) ┘ä╪ú╪▒╪┤┘ü╪⌐ ╪º┘ä╪¼┘ä╪│╪º╪¬"""
        print(f"\n[≡ƒºá] Memory Agent: ╪ú╪▒╪┤┘ü╪⌐ ╪º┘ä╪¼┘ä╪│╪⌐...")
        sum_prompt = ChatPromptTemplate.from_template("┘ä╪«╪╡ ┘ç╪░┘ç ╪º┘ä┘à┘ç┘à╪⌐ ┘ê┘å╪¬╪º╪ª╪¼┘ç╪º ┘ü┘è ╪│╪╖╪▒┘è┘å: ╪º┘ä┘à┘ç┘à╪⌐: {task} | ╪º┘ä╪¬┘é╪▒┘è╪▒: {report}")
        summary = self.robust_invoke("fast", sum_prompt, {"task": self.state["task"], "report": final_report})
        
        self.memory["sessions"].append({
            "timestamp": datetime.now().isoformat(),
            "task": self.state["task"],
            "summary": summary
        })
        self._save_memory()

    def save_report(self, report, start_time):
        fail_msgs = ["ΓÜá∩╕Å ╪╣╪░╪▒╪º┘ï", "ΓÜá∩╕Å ┘ü╪┤┘ä╪¬ ╪º┘ä┘à╪¡╪º┘ê┘ä╪º╪¬"]
        if any(msg in report for msg in fail_msgs):
            print("\n[ΓÜá∩╕Å] ╪¬┘à ╪Ñ┘ä╪║╪º╪í ╪¡┘ü╪╕ ╪º┘ä╪¬┘é╪▒┘è╪▒ ┘ä╪╣╪»┘à ┘ê╪¼┘ê╪» ╪¿┘è╪º┘å╪º╪¬ ┘à┘ü┘è╪»╪⌐.")
            return

        safe_text = unicodedata.normalize('NFKD', self.state["task"]).encode('ascii', 'ignore').decode('ascii')
        filename_base = re.sub(r'[^\w\s-]', '', safe_text).strip().replace(' ', '_')[:30]
        if not filename_base: filename_base = "Cyber_Intelligence"
        filename = f"{filename_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = os.path.join(REPORTS_DIR, filename)
        with open(report_path, "w", encoding="utf-8") as f: f.write(report)
        rag_path = os.path.join(KNOWLEDGE_BASE_DIR, f"Last_Session_{filename}")
        with open(rag_path, "w", encoding="utf-8") as f: f.write(report)
        print(f"\nΓÅ▒ ╪º┘ä┘ê┘é╪¬: {round(time.time() - start_time, 2)} ╪½╪º┘å┘è╪⌐ | [≡ƒÆ╛] ╪¡┘ü╪╕: {filename}")

    def run(self, task):
        self.state["task"] = task
        start_time = time.time()
        
        local_info = self.local_rag_agent(task)
        web_info = self.researcher_agent(task)
        dark_info = self.darkweb_researcher_agent(task)
        combined = f"LOCAL:\n{local_info}\n\nWEB:\n{web_info}\n\nDARK WEB:\n{dark_info}"
        
        self.analyst_agent(combined)
        self.debater_agent(self.state["analysis"])
        self.fact_checker_agent()
        
        while self.state["iterations"] < 2:
            feedback = self.reviewer_agent()
            if "APPROVED" in feedback.upper(): break
            else: self.state["feedback"] = feedback; self.state["iterations"] += 1
        
        final_report = self.writer_agent()
        self.save_report(final_report, start_time)
        
        # Memory
        sum_prompt = ChatPromptTemplate.from_template("┘ä╪«╪╡ ╪º┘ä┘à┘ç┘à╪⌐: {task} | ╪º┘ä╪¬┘é╪▒┘è╪▒: {report}")
        summary = self.robust_invoke("fast", sum_prompt, {"task": task, "report": final_report})
        self.memory["sessions"].append({"timestamp": datetime.now().isoformat(), "task": task, "summary": summary})
        self._save_memory()

if __name__ == "__main__":
    system = ProMultiAgentSystem()
    user_task = input("\n┘à╪º ┘ç┘è ╪º┘ä┘à┘ç┘à╪⌐ ╪º┘ä╪º╪│╪¬╪«╪¿╪º╪▒╪º╪¬┘è╪⌐ ┘ä┘ä┘è┘ê┘à╪ƒ ")
    system.run(user_task)
