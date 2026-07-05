from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_llm
from app.core.rag import RAGEngine, RAGConfig
from app.core.memory.memory_service import ArgusMemory
import json
import os
import re
import time
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

    def _run_tools_direct(self, query: str) -> str:
        target = query.strip()
        for line in query.split('\n'):
            line = line.strip()
            if line.startswith('http://') or line.startswith('https://'):
                target = line
                break
            if '.' in line and not line.startswith('#'):
                maybe = line.split()[-1].strip()
                if maybe.startswith('http://') or maybe.startswith('https://'):
                    target = maybe
                    break

        results = []
        for tool in self.tools:
            name = tool.name
            desc = tool.description
            try:
                print(f"[BRAIN] Running tool: {name}")
                result = tool.func(target)
                truncated = str(result)[:1000]
                results.append(f"--- {name} ---\n{truncated}")
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

    def graph_ask(self, query: str) -> Dict[str, Any]:
        """Run a LangGraph workflow instead of linear tool execution.

        Uses create_react_agent for models with tool_calls support,
        or a custom text-based ReAct graph for other models.
        """
        from langchain_ollama import ChatOllama
        from app.core.workflow import build_workflow
        from app.core.workflow.state import ArgusAgentState

        chat_llm = ChatOllama(
            model=self.llm.model if hasattr(self.llm, "model") else str(self.llm),
            temperature=0.2,
            num_predict=4096,
            top_p=0.9,
            num_gpu=0,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

        target = self._extract_target(query)
        blackboard = self._blackboard_context or "No findings yet."

        graph = build_workflow(
            llm=chat_llm,
            tools=list(self.tool_map.values()) if hasattr(self, "tool_map") else self.tools,
            memory=self.memory,
        )

        initial = {
            "messages": [HumanMessage(content=query)],
            "target": target,
            "phase": "init",
            "blackboard_summary": blackboard,
            "iteration_count": 0,
            "max_iterations": 15,
            "remaining_steps": 15,
            "tool_name": None,
            "tool_input": None,
            "tool_result": None,
            "tool_error": None,
        }

        try:
            result = graph.invoke(initial)

            # Extract the final answer from messages
            messages = result.get("messages", [])
            output = ""
            if messages:
                last = messages[-1]
                if hasattr(last, "content") and last.content:
                    output = last.content
                elif hasattr(last, "text") and last.text:
                    output = last.text
                else:
                    output = str(last)

            # Use blackboard summary if messages are empty
            if not output:
                output = result.get("blackboard_summary", "No output generated.")

            return self._process_output(output)
        except Exception as e:
            return {"output": {"error": "graph_failed", "message": str(e)}}

    @staticmethod
    def _extract_target(query: str) -> str:
        """Extract target URL/domain from a query string."""
        for part in query.split():
            part = part.strip(".,;!?\"'()[]")
            if part.startswith(("http://", "https://")):
                return part
            if "." in part and " " not in part:
                return part
        return query
