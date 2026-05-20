from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.schemas import SecurityReport
import os
import json

class ArgusBrain:
    def __init__(self, model_name, tools_list):
        self.llm = OllamaLLM(
            model=model_name, 
            timeout=3600,  # Increased to 1 hour for large models
            temperature=0.1,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        self.tools = tools_list
        self.output_parser = PydanticOutputParser(pydantic_object=SecurityReport)
        self.agent_executor = self._setup_agent()

    def _setup_agent(self):
        format_instructions = self.output_parser.get_format_instructions()
        
        template = """You are Argus AI, a senior security researcher and penetration testing expert.
Your goal is to analyze target security posture based on reconnaissance data.

CRITICAL OPERATIONAL RULES:
1. PHASE 1 (Connectivity): Always verify if the target is reachable using 'Check_Reachability'.
2. PHASE 2 (Subdomains): If reachable, execute 'Subdomain_Enumeration' to map the attack surface.
3. PHASE 3 (Discovery): Perform 'Recon_Suite' on the target for deep intelligence.
4. PHASE 4 (Memory): Use 'Query_Memory' to get a consolidated view of all discovered data. Use 'Query_Knowledge_Graph' to identify high-value links between targets (e.g., shared IPs, shared secrets, or common tech stacks).
5. PHASE 5 (Exploitation): For each identified vulnerability type, use 'Exploit_Suggester' to find relevant test payloads.
6. PHASE 6 (Analysis): Analyze the findings. Look for:
   - Lateral Movement opportunities discovered via 'Query_Knowledge_Graph'.
   - Server Fingerprints & Version vulnerabilities.
   - WAF presence and bypass potential.
   - Exposed headers (missing security headers like HSTS, CSP, etc.).
   - Open ports and services (from nmap).

7. FINAL ANSWER FORMAT: Your final answer MUST be a valid JSON object matching the following structure:
{format_instructions}

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
Thought: I will query my memory to get a structured summary of all findings.
Action: Query_Memory
Action Input: ""
Observation: (structured data)
Thought: I found a potential XSS vulnerability. I will fetch payloads for it.
Action: Exploit_Suggester
Action Input: "xss"
Observation: (payload list)
Thought: I have sufficient technical evidence and payloads. I will now synthesize the security analysis.
Final Answer: (The valid JSON object ONLY)

Available tool names: {tool_names}

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            partial_variables={"format_instructions": format_instructions}
        )
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=50,
            early_stopping_method="generate"
        )

    def ask(self, query, callbacks=None):
        raw_result = self.agent_executor.invoke({"input": query}, config={"callbacks": callbacks})
        
        # Try to parse the final answer into our Pydantic model
        try:
            # The agent's final answer should be in result["output"]
            parsed_report = self.output_parser.parse(raw_result["output"])
            return {"output": parsed_report.dict(), "raw": raw_result["output"]}
        except Exception as e:
            print(f"[!] Pydantic Parsing Error: {e}")
            return raw_result

    def simple_ask(self, prompt):
        """Direct LLM call for analysis when tools are not needed, bypassing agent overhead."""
        response = self.llm.invoke(prompt)
        return {"output": response}
