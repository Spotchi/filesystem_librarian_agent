import asyncio

from llama_index.core.workflow.events import InputRequiredEvent, HumanResponseEvent
from llama_index.core.agent.workflow import (
    AgentWorkflow,
    AgentOutput,
    ToolCall,
    ToolCallResult,
    AgentStream,
)
from llama_index.core.workflow import Context
from llama_index.core.memory import ChatMemoryBuffer

from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI

from app.engine.get_agent import get_agent
from app.engine.suggestion_tool import suggestion_tool, apply_file_operations_tool
from app.engine.vault_tool import get_vault_tree_tool
from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from app.instrument import instrument

import logging
import sys

instrument()

tracer = trace.get_tracer(__name__)


async def main():
    
    llm = OpenAI(temperature=0.5, model="gpt-4o-mini")

    agent = get_agent(
        llm,
        [
            suggestion_tool,
            apply_file_operations_tool,
            get_vault_tree_tool,
            # FunctionTool.from_defaults(user_ask_confirmation),
        ],
    )
    
    attributes = {
        SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN",
        SpanAttributes.USER_ID: "dev",
    }
    
    memory = ChatMemoryBuffer.from_defaults(token_limit=40000)
    with tracer.start_as_current_span(
        "chat", attributes=attributes, end_on_exit=True
    ):
        try:
            while True:
                user_msg = input("user: ")
                workflow = AgentWorkflow(agents=[agent])
                handler = workflow.run(user_msg=user_msg, memory=memory)
                async for event in handler.stream_events():
                    if isinstance(event, AgentStream):
                        continue
                    if isinstance(event, AgentOutput):
                        print(event.response.content)
                        print("Tool calls: ", event.tool_calls)
                    elif isinstance(event, ToolCallResult):
                        print("Got tool call result!!!!!!!!!!")
                        print(event.tool_name, event.tool_id, event.tool_output)
                    elif isinstance(event, ToolCall):
                        print(event.tool_name, event.tool_id, event.tool_kwargs)
                        print("Expecting tool call result!!!!!!!!!!")
                    # elif isinstance(event, InputRequiredEvent):
                    #     print("Asking for input")
                    #     # here, we can handle human input however you want
                    #     # this means using input(), websockets, accessing async state, etc.
                    #     # here, we just use input()
                    #     response = input(event.prefix)
                    #     handler.ctx.send_event(
                    #         HumanResponseEvent(response=response),
                    #     )
                    elif not isinstance(event, AgentStream):
                        print(type(event))
                        
                with open("memory.json", "w") as f:
                    f.write(memory.model_dump_json())
                print("Done one workflow")

        except Exception as e:
            print(e)
        
        # span.set_attribute(SpanAttributes.OUTPUT_VALUE, full_response)

if __name__ == "__main__":
    asyncio.run(main())
