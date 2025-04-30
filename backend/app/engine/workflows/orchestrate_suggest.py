from llama_index.core.agent.workflow import (
    AgentWorkflow,
)

from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent


from app.engine.suggestion_tool import suggestion_tool, apply_file_operations_tool
from app.engine.vault_tool import get_vault_tree_tool

from app.engine.prompts import orchestrating_agent_prompt, suggestion_agent_prompt


ORCHESTRATE_SUGGEST_WORKFLOW_ID = "orchestrate_suggest_workflow"

def orchestrate_suggest_workflow() -> AgentWorkflow:

    llm = OpenAI(temperature=0.5, model="gpt-4o-mini")

    orchestrating_agent = FunctionAgent(
        name="orchestrating_agent",
        description="This agent is responsible for orchestrating the other agents",
        llm=llm,
        tools=[get_vault_tree_tool, apply_file_operations_tool],
        system_prompt=orchestrating_agent_prompt,
        can_handoff_to=["Suggestion Agent"],
    )

    suggestion_agent = FunctionAgent(
        name="suggestion_agent",
        description="This agent is responsible for suggesting a new structure for the files",
        llm=llm,
        tools=[suggestion_tool],
        system_prompt=suggestion_agent_prompt,
        can_handoff_to=[orchestrating_agent.name],
    )

    workflow = AgentWorkflow(agents=[orchestrating_agent, suggestion_agent],
                             root_agent=orchestrating_agent.name,
                             )
    
    return workflow