from llama_index.utils.workflow import draw_all_possible_flows
from llama_index.core.agent.workflow import AgentWorkflow


if __name__ == "__main__":
    draw_all_possible_flows(AgentWorkflow, filename="agent_workflow.html")