
from typing import List
from llama_index.core.llms.llm import BaseLLM
from llama_index.core.tools import BaseTool
from llama_index.core.agent.workflow import FunctionAgent

from app.engine.prompts import system_prompt, agent_description

def get_agent(llm: BaseLLM, tools: List[BaseTool], name: str = "Agent", system_prompt: str = system_prompt) -> FunctionAgent:
    return FunctionAgent(
        name=name,
        description=agent_description,
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
    )

