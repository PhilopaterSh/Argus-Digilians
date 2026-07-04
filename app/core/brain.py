from langchain_core.output_parsers import PydanticOutputParser
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_llm
from app.core.rag import RAGEngine, RAGConfig
from app.core.memory.memory_service import ArgusMemory
import json
import os
import re
import time
import concurrent.futures
from typing import Dict, Any, Optional


class ArgusBrain:
    def __init__(self, model_name, tools_list, rag_config: Optional[dict] = None, memory: Optional[ArgusMemory] = None):
        self.llm = build_llm(model_name)
        self.tools = tools_list
        self.tool_map = {tool.name: tool for tool in tools_list}
        self.output_parser = PydanticOutputParser(pydantic_object=SecurityReport)
        self.memory = memory

        if rag_config is None:
            rag_config = self._load_rag_config()
        self.rag_enabled = rag_config is not None and rag_config.get("enabled", False)

        self._rag_engine = None
        if self.rag_enabled:
            try:
                config = RAGConfig.from_dict(rag_config or {})
                self._rag_engine = RAGEngine(config=config, model_name=model_name)
                self._rag_engine.initialize()
                print(f"[BRAIN] RAG initialized with {self._rag_engine.vector_store.index_size} indexed chunks")
            except Exception as e:
                print(f"[BRAIN] RAG initialization skipped: {e}")
                self.rag_enabled = False

        self._blackboard_context = ""
        self._refresh_blackboard()

    @staticmethod
    def _load_rag_config() -> Optional[Dict[str, Any]]:
        try:
            import yaml
            config_path = os.getenv("ARGUS_CONFIG", "config.yaml")
            if os.path.exists(config_path):
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                return cfg.get("rag")
        except Exception:
            pass
        return None

    def _refresh_blackboard(self):
        if self.memory is None:
            self._blackboard_context = ""
            return
        try:
            blackboard = self.memory.get_blackboard_summary()
            insights = self.memory.get_graph_insights()
            parts = []
            if blackboard and blackboard != "{}":
                parts.append(f"[Blackboard Intelligence]\n{blackboard}")
            if insights:
                parts.append(f"[Knowledge Graph Relations]\n{insights}")
            self._blackboard_context = "\n\n".join(parts)
        except Exception as e:
            print(f"[BRAIN] Blackboard refresh failed: {e}")
            self._blackboard_context = ""

    def refresh_blackboard(self):
        self._refresh_blackboard()

    def _enrich_with_rag(self, query: str) -> str:
        if not self.rag_enabled or self._rag_engine is None:
            if self._blackboard_context:
                return (
                    f"===== LIVE TARGET STATE (current findings) =====\n"
                    f"{self._blackboard_context}\n\n"
                    f"Question: {query}"
                )
            return query

        try:
            combined = self._rag_engine.format_combined_context(
                query=query,
                blackboard_context=self._blackboard_context,
            )
            if combined:
                enriched = (
                    f"{combined}\n\n"
                    f"Question: {query}\n\n"
                    f"Instructions:\n"
                    f"- STATIC KNOWLEDGE is general pentest techniques, cheatsheets, and reference material.\n"
                    f"- LIVE TARGET STATE is what Argus has actively discovered about the current target.\n"
                    f"- When answering, prioritize live target state over generic knowledge.\n"
                    f"- If live data contradicts static knowledge, note the discrepancy."
                )
                print(f"[BRAIN] Fusion context: RAG + Blackboard ({len(combined)} chars)")
                return enriched
        except Exception as e:
            print(f"[BRAIN] RAG enrichment failed: {e}")

        if self._blackboard_context:
            return (
                f"===== LIVE TARGET STATE =====\n"
                f"{self._blackboard_context}\n\n"
                f"Question: {query}"
            )
        return query

    def _extract_target(self, query: str) -> str:
        urls = re.findall(r'https?://[^\s,;)]+', query)
        if urls:
            return urls[0]
        domains = re.findall(r'(?:https?://)?([a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s,;)]*)?)', query)
        if domains:
            return domains[0]
        return query.strip()

    def _run_tools_direct(self, query: str) -> str:
        target = self._extract_target(query)

        quick_tools = {
            "Check_Reachability", "Smart_Web_Search", "Exploit_Suggester",
            "Query_Memory", "Query_Knowledge_Graph",
        }
        medium_tools = {
            "Run_Nikto", "Subdomain_Enumeration", "Archive_Research_Subagent",
            "System_Self_Heal",
        }

        results = []
        print("[BRAIN] Running quick tools (15s timeout)...")
        for tool in self.tools:
            name = tool.name
            if name not in quick_tools and name not in medium_tools:
                continue
            try:
                print(f"[BRAIN] Running tool: {name} -> {target}")
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    fut = pool.submit(tool.func, target)
                    result = fut.result(timeout=15)
                truncated = str(result)[:800]
                results.append(f"--- {name} ---\n{truncated}")
            except concurrent.futures.TimeoutError:
                results.append(f"--- {name} ---\nTIMEOUT (15s)")
            except Exception as e:
                results.append(f"--- {name} ---\nERROR: {e}")

        return "\n\n".join(results)

    def ask(self, query: str, callbacks=None) -> Dict[str, Any]:
        self._refresh_blackboard()
        augmented_query = self._enrich_with_rag(query)

        print("[BRAIN] Running tools directly...")
        tool_results = self._run_tools_direct(augmented_query)

        analysis_prompt = (
            f"You are Argus AI, a senior security researcher.\n\n"
            f"Below are reconnaissance results for a security target.\n"
            f"Analyze them and produce a comprehensive security assessment.\n\n"
            f"Query: {query}\n\n"
            f"Tool Results:\n{tool_results}\n\n"
            f"Provide your final analysis as a JSON object with these keys:\n"
            f"- summary: executive summary\n"
            f"- attack_surface_stats: summary of findings\n"
            f"- findings: array of objects with target, issue, severity, description, remediation\n"
            f"- overall_risk_score: number 1-10\n"
            f"- next_steps: array of strings\n"
            f"- output: full markdown report"
        )

        print("[BRAIN] Calling LLM for final analysis...")
        try:
            response = self.llm.invoke(analysis_prompt)
            output = str(response)
            return self._process_output(output)
        except Exception as e:
            return {"output": {"error": "llm_failed", "message": str(e)}}

    def _process_output(self, output: str, raw_output: str = "") -> Dict[str, Any]:
        if isinstance(output, dict) and "error" in output:
            return {"output": output}

        try:
            parsed = self.output_parser.parse(str(output))
            return {"output": parsed.dict()}
        except Exception as e:
            print(f"[BRAIN] Pydantic parsing failed: {e}")

        try:
            output_str = str(output)
            for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
                match = re.search(pattern, output_str)
                if match:
                    obj = json.loads(match.group(0))
                    return {"output": obj}
        except Exception:
            pass

        return {"output": output}

    def simple_ask(self, prompt):
        response = self.llm.invoke(prompt)
        return {"output": response}
