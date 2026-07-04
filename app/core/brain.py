from langchain_core.output_parsers import PydanticOutputParser
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_llm
from app.core.prompts import get_argus_prompt
from app.core.rag import RAGEngine, RAGConfig
from app.core.memory.memory_service import ArgusMemory
import json
import os
import re
from typing import Dict, Any, Optional


class ArgusBrain:
    """
    Enhanced brain with ReAct → SimpleChain fallback and RAG + Blackboard context fusion.

    When WhiteRabbitNeo has format issues with ReAct, automatically
    falls back to a simpler sequential execution model.
    """

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

        # Lazy load executors
        self._react_agent = None
        self._simple_chain = None

        # Always use SimpleChain for local models (CPU/no GPU) to avoid ReAct format issues
        self.use_react = False

        print(f"[BRAIN] Using SimpleChain for model: {model_name}")

    def _get_react_agent(self):
        if self._react_agent is not None:
            return self._react_agent

        try:
            from app.core.agent_factory import build_agent_executor
            format_instructions = self.output_parser.get_format_instructions()
            prompt = get_argus_prompt(format_instructions)
            self._react_agent = build_agent_executor(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            return self._react_agent
        except Exception as e:
            print(f"[BRAIN] Failed to load ReAct agent: {e}")
            return None

    def _get_simple_chain(self):
        if self._simple_chain is not None:
            return self._simple_chain

        try:
            self._simple_chain = build_agent_executor(
                llm=self.llm,
                tools=self.tools,
                prompt=get_argus_prompt(self.output_parser.get_format_instructions()),
                verbose=False
            )
            return self._simple_chain
        except Exception as e:
            print(f"[BRAIN] Failed to load Simple Chain: {e}")
            return None

    @staticmethod
    def _load_rag_config() -> Optional[Dict[str, Any]]:
        try:
            from app.core.config import ArgusConfig
            cfg = ArgusConfig.load()
            return cfg.to_rag_dict() if cfg.rag.enabled else None
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

    def ask(self, query: str, callbacks=None) -> Dict[str, Any]:
        self._refresh_blackboard()
        augmented_query = self._enrich_with_rag(query)

        if self.use_react:
            try:
                react_agent = self._get_react_agent()
                if react_agent:
                    print("[BRAIN] Attempting ReAct agent...")
                    result = react_agent.invoke(
                        {"input": augmented_query},
                        config={"callbacks": callbacks}
                    )

                    if isinstance(result, dict):
                        output = result.get("output", result)

                        if isinstance(output, dict) and "error" in output:
                            error_msg = str(output.get("message", ""))
                            if "Invalid Format" in error_msg or "Missing 'Action:'" in error_msg or "parsing_error" in output.get("error", ""):
                                print(f"[BRAIN] ReAct format error detected: {error_msg}")
                                self.use_react = False
                                return self._ask_simple_chain(augmented_query, callbacks)

                        return self._process_output(output, str(result))

            except Exception as e:
                error_msg = str(e)
                if "Invalid Format" in error_msg or "Missing 'Action:'" in error_msg:
                    print(f"[BRAIN] ReAct format error exception: {error_msg}")
                    self.use_react = False
                    return self._ask_simple_chain(augmented_query, callbacks)
                print(f"[BRAIN] ReAct attempt failed: {error_msg}")

        print("[BRAIN] Using Simple Chain as primary or fallback executor...")
        return self._ask_simple_chain(augmented_query, callbacks)

    def _ask_simple_chain(self, query: str, callbacks=None) -> Dict[str, Any]:
        try:
            simple_chain = self._get_simple_chain()
            if not simple_chain:
                return {
                    "output": {
                        "error": "executor_unavailable",
                        "message": "Neither ReAct nor Simple Chain could be initialized. Check logs."
                    }
                }

            print("[BRAIN] Using Simple Chain executor...")
            result = simple_chain.invoke(
                {"input": query},
                config={"callbacks": callbacks} if callbacks else {}
            )

            return self._process_output(result.get("output", result), str(result))

        except Exception as e:
            return {
                "output": {
                    "error": "simple_chain_failed",
                    "message": str(e)
                }
            }

    def _process_output(self, output: Any, raw_output: str = "") -> Dict[str, Any]:
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
