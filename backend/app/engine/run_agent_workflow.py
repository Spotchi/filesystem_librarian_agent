import asyncio

from llama_index.core.agent.workflow import (
    AgentOutput,
    ToolCall,
    ToolCallResult,
    AgentStream,
)
from llama_index.core.memory import ChatMemoryBuffer


from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from app.instrument import instrument
from app.engine.workflows.orchestrate_suggest import orchestrate_suggest_workflow, ORCHESTRATE_SUGGEST_WORKFLOW_ID
from openinference.instrumentation import using_metadata

from app.telemetry_attributes import TelemetryAttributes
from git import Repo


# Get git commit hash and date
instrument({})

tracer = trace.get_tracer(__name__)

repo = Repo(search_parent_directories=True)

git_commit_hash = repo.head.commit.hexsha
git_commit_date = repo.head.commit.committed_date


async def main():
    
    attributes = {
        SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN",
        SpanAttributes.USER_ID: "dev",
    }
    
    metadata = {
        TelemetryAttributes.WORKFLOW_ID: ORCHESTRATE_SUGGEST_WORKFLOW_ID,
        TelemetryAttributes.GIT_COMMIT_HASH: git_commit_hash,
        TelemetryAttributes.GIT_COMMIT_DATE: git_commit_date
    }

    memory = ChatMemoryBuffer.from_defaults(token_limit=40000)
    with tracer.start_as_current_span("chat", attributes=attributes, end_on_exit=True):
        with using_metadata(metadata):
            try:
                while True:
                    user_msg = input("user: ")
                    workflow = orchestrate_suggest_workflow()
                    handler = workflow.run(user_msg=user_msg, memory=memory)
                    current_agent = None
                    async for event in handler.stream_events():
                        if (
                            hasattr(event, "current_agent_name")
                            and event.current_agent_name != current_agent
                        ):
                            current_agent = event.current_agent_name
                            print(f"\n{'=' * 50}")
                            print(f"🤖 Agent: {current_agent}")
                            print(f"{'=' * 50}\n")
                        if isinstance(event, AgentStream):
                            continue
                        if isinstance(event, AgentOutput):
                            print(event.response.content)
                        elif isinstance(event, ToolCallResult):
                            print(event.tool_name, event.tool_id, event.tool_output)
                        elif isinstance(event, ToolCall):
                            print(event.tool_name, event.tool_id, event.tool_kwargs)
                        elif not isinstance(event, AgentStream):
                            print(type(event))

                    with open("memory.json", "w") as f:
                        f.write(memory.model_dump_json())
                    del workflow

            except Exception as e:
                print(e)

if __name__ == "__main__":
    asyncio.run(main())
