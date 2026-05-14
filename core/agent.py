from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

class ArgusBrain:
    def __init__(self, model_name, tools_list):
        self.llm = OllamaLLM(model=model_name, timeout=300, temperature=0.1)
        self.tools = tools_list
        self.agent_executor = self._setup_agent()

    def _setup_agent(self):
        template = """You are Argus AI, a senior security researcher and penetration testing expert.
Your goal is to analyze target security posture based on reconnaissance data.

CRITICAL OPERATIONAL RULES:
1. PHASE 1 (Connectivity): Always verify if the target is reachable using 'Check_Reachability'.
2. PHASE 2 (Subdomains): If reachable, execute 'Subdomain_Enumeration' to map the attack surface.
3. PHASE 3 (Discovery): Perform 'Recon_Suite' on the target for deep intelligence.
4. PHASE 4 (Analysis): Analyze the findings. Look for:
   - Server Fingerprints & Version vulnerabilities.
   - WAF presence and bypass potential.
   - Exposed headers (missing security headers like HSTS, CSP, etc.).
   - Open ports and services (from nmap).
5. FINAL ANSWER: Provide a comprehensive, structured report including:
   - 🛡️ Summary of Findings
   - ⚠️ Identified Risks & Vulnerabilities
   - 🛠️ Recommended Mitigation Steps
   - 🎯 Next Steps for deeper testing

Tools: {tools}

Format:
Question: {input}
Thought: I need to check if the target is online first.
Action: Check_Reachability
Action Input: (target)
Observation: (result)
Thought: Target is online. Now I must discover its subdomains to map the surface.
Action: Subdomain_Enumeration
Action Input: (target)
Observation: (subdomain data)
Thought: Now I will perform a full parallel recon suite for deep evidence.
Action: Recon_Suite
Action Input: (target)
Observation: (recon data)
Thought: I have sufficient technical evidence. I will now synthesize the security analysis.
Final Answer: (Detailed, structured security report)

Available tool names: {tool_names}

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="force"
        )

    def ask(self, query):
        return self.agent_executor.invoke({"input": query})
