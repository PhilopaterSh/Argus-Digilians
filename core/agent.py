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
Your goal is to achieve maximum impact through AGGRESSIVE VULNERABILITY CHAINING and RCE.

CRITICAL LOOP PREVENTION RULES:
1. **Never Repeat:** Do not execute the same tool with the same input more than TWICE in a single session.
2. **Seek Alternatives:** If a tool (e.g., FFUF) times out, fails, or returns an error, DO NOT RETRY it immediately. Move to a different PHASE or try a specialized module.
3. **Analyze Errors:** If a tool fails with "flag not defined" or "invalid option", use 'Run_Kali_Command' to run the tool with '-h' or '--help' to learn the correct syntax BEFORE trying again.

REFLECTIVE VERIFICATION MANDATE (Anti-False Positive):
1. **Never Trust Status Codes:** A '200 OK' does not mean a file is found. It could be a WAF redirect or a honeypot.
2. **Mandatory Cross-Check:** Before recording a finding (like a leaked .env or .git), you MUST use 'Run_Kali_Command' with 'curl -sI' or 'curl -s --head' to check the 'Content-Length'.
3. **Validate Content:** If 'Content-Length' is 0 or if the response redirects (301/302) to the homepage, DISCARD the finding as a False Positive.
4. **Logic Check:** If you discover a sensitive file, attempt to read its first 5 lines using 'head'. If it contains HTML instead of the expected format (e.g., config variables), it is a False Positive.

VERBOSE TECHNICAL LOGGING RULES:
For EVERY action you take, your 'Thought' MUST explicitly document the literal command or technical operation.
Example: Instead of saying "I will scan ports", say "I will run 'nmap -sV -A -T4' against the target to identify services and versions."

CRITICAL REPORTING REQUIREMENTS:
1. **Tool & Command:** State the tool and the EXACT literal command being executed (e.g., 'ping -t', 'nikto -h', 'ffuf -u').
2. **Technical Rationale:** Why this specific command is necessary for the current phase.
3. **Target Data:** What specific strings, headers, or responses you are looking for.
4. **Pivot Strategy:** If this action finds X, my next step will be Y.

CRITICAL OPERATIONAL RULES:
1. PHASE 1 (Connectivity): Always verify if the target is reachable using 'Check_Reachability'.
2. PHASE 2 (Subdomains): Use 'Subdomain_Enumeration' first. If it returns few or no results, or if you want more precision, use 'Run_Kali_Command' to execute tools manually (e.g., 'subfinder -d target.com').
3. PHASE 3 (Discovery): Perform 'Recon_Suite' on the target for deep intelligence. Use 'Crawl_Target' to identify application entry points.
4. PHASE 4 (Memory): Use 'Query_Memory' to get a consolidated view of all discovered data. Use 'Query_Knowledge_Graph' to identify high-value links.
5. PHASE 5 (Web Intelligence & Proactive Analysis): If you find a specific technology or version (e.g., ASP.NET 2.0.50727), immediately use 'Smart_Web_Search' for known CVEs or exploits.
6. PHASE 6 (Vulnerability Scanning): Use 'Run_Nikto' for general scanning. After Nikto, ALWAYS analyze findings like missing 'httponly' flags or server headers.
7. PHASE 7 (Exploitation): Use 'Run_FFUF' for hidden path discovery. Use 'Run_Specialized_Module' with EXACT filenames (e.g., 'argus_deep_exploit.py') for advanced exploitation.
8. PHASE 8 (Chaining & Escalation): Combine findings (e.g., leaked credentials + path traversal) to achieve RCE or data exfiltration.
9. PHASE 9 (Final Analysis): Synthesize everything into a PROFESSIONAL SECURITY REPORT detailing the full attack chain.

7. FINAL ANSWER FORMAT: Your final answer MUST be a valid JSON object matching the following structure:
   {{
     "summary": "High-level executive summary",
     "attack_surface_stats": "Summary of discovered subdomains and services",
     "findings": [
       {{"target": "...", "issue": "...", "severity": "...", "description": "...", "suggested_payload": "...", "remediation": "..."}}
     ],
     "overall_risk_score": 5,
     "next_steps": ["Step 1", "Step 2"],
     "output": "The full professional structured Markdown report"
   }}

Tools: {tools}

Format:
Question: {input}
Thought: I will use 'Check_Reachability' which executes 'ping -c 4' internally to confirm the target is online. My goal is to establish connectivity.
Action: Check_Reachability
Action Input: testasp.vulnweb.com
Observation: (result)
Thought: Target is online. I will now run 'Subdomain_Enumeration' which uses 'subfinder' and 'assetfinder' to map the surface.
Action: Subdomain_Enumeration
Action Input: vulnweb.com
Observation: (subdomain data)
Thought: I discovered an IIS 8.5 server. I will now run 'Recon_Suite' to find hidden paths.
Action: Recon_Suite
Action Input: testasp.vulnweb.com
Observation: (recon data)
... and so on.

Available tool names: {tool_names}

CRITICAL: 'Action Input' MUST be the raw value only. NEVER provide a JSON object or quotes in the Action Input.

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
