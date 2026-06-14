from langchain_core.output_parsers import PydanticOutputParser
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_llm
from app.core.agent_factory import build_agent_executor
from app.core.prompts import get_argus_prompt

class ArgusBrain:
    def __init__(self, model_name, tools_list):
        self.llm = build_llm(model_name)
        self.tools = tools_list
        self.output_parser = PydanticOutputParser(pydantic_object=SecurityReport)
        
        format_instructions = self.output_parser.get_format_instructions()
        prompt = get_argus_prompt(format_instructions)
        
        self.agent_executor = build_agent_executor(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

    def ask(self, query, callbacks=None):
        raw_result = self.agent_executor.invoke({"input": query}, config={"callbacks": callbacks})
        
        try:
            parsed_report = self.output_parser.parse(raw_result["output"])
            return {"output": parsed_report.dict(), "raw": raw_result["output"]}
        except Exception as e:
            print(f"[!] Pydantic Parsing Error: {e}")
            return raw_result

    def simple_ask(self, prompt):
        """Direct LLM call for analysis when tools are not needed."""
        response = self.llm.invoke(prompt)
        return {"output": response}
