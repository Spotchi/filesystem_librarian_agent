import streamlit as st
import asyncio
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.agent.workflow import (
    AgentOutput,
    ToolCall,
    ToolCallResult,
)
from app.engine.workflows.para_workflow import para_workflow, ORCHESTRATE_PARA_WORKFLOW_ID
from app.telemetry_attributes import TelemetryAttributes
from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from openinference.instrumentation import using_metadata
from git import Repo

# Initialize git info
repo = Repo(search_parent_directories=True)
git_commit_hash = repo.head.commit.hexsha
git_commit_date = repo.head.commit.committed_date

# Initialize tracer
tracer = trace.get_tracer(__name__)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = ChatMemoryBuffer.from_defaults(token_limit=40000)

async def process_message(user_input):
    attributes = {
        SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN",
        SpanAttributes.USER_ID: "dev",
    }
    
    metadata = {
        TelemetryAttributes.WORKFLOW_ID: ORCHESTRATE_PARA_WORKFLOW_ID,
        TelemetryAttributes.GIT_COMMIT_HASH: git_commit_hash,
        TelemetryAttributes.GIT_COMMIT_DATE: git_commit_date
    }

    with tracer.start_as_current_span("chat", attributes=attributes, end_on_exit=True):
        with using_metadata(metadata):
            workflow = para_workflow()
            handler = workflow.run(user_msg=user_input, memory=st.session_state.memory)
            
            current_agent = None
            full_response = ""
            
            async for event in handler.stream_events():
                if (
                    hasattr(event, "current_agent_name")
                    and event.current_agent_name != current_agent
                ):
                    current_agent = event.current_agent_name
                    st.write(f"🤖 Agent: {current_agent}")
                
                if isinstance(event, AgentOutput):
                    if event.response.content:
                        full_response += event.response.content
                        st.write(full_response)
                # 
                elif isinstance(event, ToolCallResult):
                    st.write(f"Tool: {event.tool_name}")
                    st.code(event.tool_output, language="text")
                
                elif isinstance(event, ToolCall):
                    st.write(f"Using tool: {event.tool_name}")
                    if event.tool_kwargs:
                        st.code(str(event.tool_kwargs), language="python")
            
            # Save memory state
            with open("memory.json", "w") as f:
                f.write(st.session_state.memory.model_dump_json())
            
            del workflow
            return full_response

def main():
    st.title("🤖 Agent Workflow Interface")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to ask?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process the message
        with st.chat_message("assistant"):
            response = asyncio.run(process_message(prompt))
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 