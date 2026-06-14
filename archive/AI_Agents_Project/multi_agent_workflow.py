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

# تحميل الإعدادات من ملف .env
load_dotenv(os.path.join("C:\\AI_Agents_Project", ".env"))

# 1. الإعدادات
PRIMARY_MODEL = "deepseek/deepseek-chat"
BACKUP_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
FALLBACK_MODEL = "google/gemini-flash-1.5-8b"

BASE_DIR = "C:\\AI_Agents_Project"
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
MEMORY_FILE = os.path.join(BASE_DIR, "ai_memory.json")

# جمع كافة مفاتيح API المتاحة
api_keys = [os.getenv(f"OPENROUTER_API_KEY_{i}") for i in range(1, 11) if os.getenv(f"OPENROUTER_API_KEY_{i}")]
if not api_keys:
    single_key = os.getenv("OPENROUTER_API_KEY")
    if single_key:
        api_keys = [single_key]

print(f"[⏳] تم العثور على {len(api_keys)} مفاتيح API. جاري شحن النظام الاستخباراتي المتكامل...")
hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

class ProMultiAgentSystem:
    def __init__(self):
        if not api_keys:
            raise ValueError("[!] خطأ: لم يتم العثور على أي مفاتيح API.")
        
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
        print(f"[🔄] تم تبديل مفتاح API لتوزيع الضغط...")

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
        if not self.memory.get("sessions"): return "لا توجد خبرات سابقة."
        last_sessions = self.memory["sessions"][-3:]
        context = "\n".join([f"- مهمة: {s.get('task','')}\n  ملخص: {s.get('summary','')}" for s in last_sessions])
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
                        print(f"[⏳] ضغط أو انتهاء رصيد ({model}). جاري تبديل المفتاح...")
                        self._rotate_key()
                        self._init_llms(model)
                        time.sleep(5)
                    elif "404" in error_str:
                        print(f"[⚠️] النموذج {model} غير متاح. تجربة البديل...")
                        break
                    else:
                        print(f"[⚠️] خطأ: {e}. محاولة تبديل المفتاح...")
                        self._rotate_key()
                        self._init_llms(model)
                        time.sleep(2)
            print(f"[🔄] الانتقال للنموذج التالي...")
        return "⚠️ فشلت المحاولات السحابية. يرجى المحاولة لاحقاً."

    def local_rag_agent(self, task):
        print(f"\n[1/7] 📚 Local Agent (RAG): البحث المحلي...")
        try:
            loaders = [
                DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.txt", loader_cls=TextLoader),
                DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader),
                DirectoryLoader(KNOWLEDGE_BASE_DIR, glob="**/*.md", loader_cls=TextLoader)
            ]
            documents = []
            for loader in loaders: documents.extend(loader.load())
            if not documents: return "لا توجد ملفات محلية."
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
            splits = text_splitter.split_documents(documents)
            vectorstore = FAISS.from_documents(splits, hf_embeddings)
            results = vectorstore.similarity_search(task, k=3)
            return "\n".join([doc.page_content for doc in results])
        except Exception as e:
            return f"خطأ RAG: {e}"

    def researcher_agent(self, task):
        print(f"[2/7] 🔍 Researcher Agent: استقصاء الويب والمظلم...")
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
        print(f"[🕵️] DarkWeb Agent: جاري البحث في الفضاء المظلم...")
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
                return "\n\n".join(dark_info) if dark_info else "لم يتم العثور على نتائج مظلمة."
            return "فشل الوصول لمحرك البحث المظلم."
        except Exception as e:
            return f"خطأ DarkWeb: {e}"

    def analyst_agent(self, raw_data):
        print(f"[3/7] 🧠 Analyst Agent: تحليل البيانات المستخرجة...")
        prompt = ChatPromptTemplate.from_template("""أنت محلل بيانات استخباراتي. قدم تحليلاً شاملاً للبيانات التالية:
        سياق سابق: {past_context}
        المهمة: {task}
        البيانات الخام: {raw_data}
        المطلوب: استخلص الحقائق والتهديدات مع الحفاظ على الروابط حقيقية وكما هي.""")
        self.state["analysis"] = self.robust_invoke("smart", prompt, {
            "task": self.state["task"], "raw_data": raw_data, "past_context": self.state["past_context"]
        })

    def debater_agent(self, analysis):
        print(f"[4/7] ⚖️ Debater Agent (Adversarial): تحدي المعلومات...")
        prompt = ChatPromptTemplate.from_template("""أنت "محامي الشيطان" وخبير في كشف التضليل. 
        مهمتك هي التشكيك في التحليل التالي، خاصة المعلومات المستمدة من الويب المظلم:
        التحليل: {analysis}
        ابحث عن الفخاخ، التضليل، والادعاءات غير الموثقة. قارن مع معايير NIST/MITRE.""")
        self.state["debate"] = self.robust_invoke("creative", prompt, {"analysis": analysis})

    def fact_checker_agent(self):
        print(f"[5/7] ✅ Fact Checker Agent: تدقيق الحقائق...")
        prompt = ChatPromptTemplate.from_template("""وازن بين التحليل الأصلي واعتراضات وكيل المعارضة (Debater).
        التحليل: {analysis}
        المعارضة: {debate}
        أعطِ الحكم النهائي حول ما هو حقيقي وما هو مشكوك فيه.""")
        self.state["fact_check"] = self.robust_invoke("smart", prompt, {
            "analysis": self.state["analysis"], "debate": self.state["debate"]
        })

    def reviewer_agent(self):
        print(f"[6/7] ⚖️ Reviewer Agent: مراجعة الجودة...")
        prompt = ChatPromptTemplate.from_template("راجع جودة التحليل النهائي والتدقيق: {fact_check}")
        return self.robust_invoke("creative", prompt, {"fact_check": self.state["fact_check"]})

    def writer_agent(self):
        print(f"[7/7] 📝 Writer Agent: صياغة التقرير الموثق...")
        unique_sources = list(set(self.state["sources"]))
        sources_list = "\n".join([f"- {s}" for s in unique_sources])
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        prompt = ChatPromptTemplate.from_template("""صغ تقريراً استخباراتياً احترافياً بـ Markdown.
        التوقيت: {current_time}
        التحليل: {analysis}
        اعتراضات المعارض: {debate}
        تدقيق الحقائق: {fact_check}
        المصادر: {sources}
        يجب أن يحتوي التقرير على أقسام: المعلومات المؤكدة، تحذيرات المعارضة، والمصادر الموثقة.""")
        return self.robust_invoke("creative", prompt, {
            "current_time": current_time, "analysis": self.state["analysis"], 
            "debate": self.state["debate"], "fact_check": self.state["fact_check"], "sources": sources_list
        })

    def memory_agent(self, final_report):
        """وكيل الذاكرة (Memory Agent) لأرشفة الجلسات"""
        print(f"\n[🧠] Memory Agent: أرشفة الجلسة...")
        sum_prompt = ChatPromptTemplate.from_template("لخص هذه المهمة ونتائجها في سطرين: المهمة: {task} | التقرير: {report}")
        summary = self.robust_invoke("fast", sum_prompt, {"task": self.state["task"], "report": final_report})
        
        self.memory["sessions"].append({
            "timestamp": datetime.now().isoformat(),
            "task": self.state["task"],
            "summary": summary
        })
        self._save_memory()

    def save_report(self, report, start_time):
        fail_msgs = ["⚠️ عذراً", "⚠️ فشلت المحاولات"]
        if any(msg in report for msg in fail_msgs):
            print("\n[⚠️] تم إلغاء حفظ التقرير لعدم وجود بيانات مفيدة.")
            return

        safe_text = unicodedata.normalize('NFKD', self.state["task"]).encode('ascii', 'ignore').decode('ascii')
        filename_base = re.sub(r'[^\w\s-]', '', safe_text).strip().replace(' ', '_')[:30]
        if not filename_base: filename_base = "Cyber_Intelligence"
        filename = f"{filename_base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        report_path = os.path.join(REPORTS_DIR, filename)
        with open(report_path, "w", encoding="utf-8") as f: f.write(report)
        rag_path = os.path.join(KNOWLEDGE_BASE_DIR, f"Last_Session_{filename}")
        with open(rag_path, "w", encoding="utf-8") as f: f.write(report)
        print(f"\n⏱ الوقت: {round(time.time() - start_time, 2)} ثانية | [💾] حفظ: {filename}")

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
        sum_prompt = ChatPromptTemplate.from_template("لخص المهمة: {task} | التقرير: {report}")
        summary = self.robust_invoke("fast", sum_prompt, {"task": task, "report": final_report})
        self.memory["sessions"].append({"timestamp": datetime.now().isoformat(), "task": task, "summary": summary})
        self._save_memory()

if __name__ == "__main__":
    system = ProMultiAgentSystem()
    user_task = input("\nما هي المهمة الاستخباراتية لليوم؟ ")
    system.run(user_task)
