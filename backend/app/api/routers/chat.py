from typing import Any, Dict, List, Optional, Tuple
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from llama_index.core.chat_engine.types import (
    BaseChatEngine,
)
import nest_asyncio; nest_asyncio.apply()

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.workflow import Context
from llama_index.core.schema import NodeWithScore
from llama_index.core.agent.workflow import AgentStream, ToolCall, ToolCallResult
from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from pydantic import BaseModel
import os
import httpx
import json
from app.engine.suggestion_tool import apply_file_operations_tool, suggest_file_operations, suggestion_tool
import os
# from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent
from pydantic import BaseModel
from app.engine.vault_tool import get_vault_tree_tool
from app.engine import get_chat_engine
from app.engine.file_ops import FileOperationsResponse

tracer = trace.get_tracer(__name__)

chat_router = r = APIRouter()


system_prompt = """
You are an expert knowledge management assistant specializing in organizing directories and files on a personal computer.

You will be given a folder structure .
To solve the task, you must propose a reorganisation of the files and folders using one or more of the following guidelines:
- All files must be contained in a folder
- Folders should be named consistently and clearly, and be consistent with the names of the files they contain
- Reduce duplicates in the hierarchy

Here are a few examples of how to use these guidelines:
---
Structure:
.
├── AI
│   └── Reinforcement learning
└── Agent.md

Suggested structure:
.
├── AI
│  ├── Reinforcement learning
│  └ Agent.md
└── Cooking

Explanation:
- All files must be contained in a folder : I moved `Agent.md` into the `AI` folder since it is related to AI not related to Cooking.

---
Structure:
.
├── AI
│   └── Deep learning
│       ├── gradient descent.md
│       └── vegetable masala.md
└── Cooking
    └── stainless steel pans.md

Suggested structure:
.
├── AI
│   └── Deep learning
│       └── gradient descent.md
└── Cooking
    ├── stainless steel pans.md
    └── vegetable masala.md

Explanation:
- Folders should be named consistently and clearly, and be consistent with the names of the files they contain: Since `vegetable masala` was not related to `AI` but was related to `Cooking`, I moved it to that folder. 

Call the get_vault_tree_tool to get the current folder structure.

Translate the operations needed for this into a list of file operations and call the suggestion_tool if operations are needed. Also ask the user if they want to apply the operations.

If the user agrees, call the apply_file_operations tool.
"""

class ToolInvocation(BaseModel):
    state: str
    args: Dict[str, Any]
    toolName: str
    toolCallId: str

class _Message(BaseModel):
    role: MessageRole
    content: str
    toolInvocations: Optional[List[Any]] = None


@r.head("/healthcheck")
@r.get("/healthcheck")
def healthcheck():
    return "Hello world!"


class _ChatData(BaseModel):
    messages: List[_Message]

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "What standards for letters exist?",
                    }
                ]
            }
        }


class _SourceNodes(BaseModel):
    id: str
    metadata: Dict[str, Any]
    score: Optional[float]

    @classmethod
    def from_source_node(cls, source_node: NodeWithScore):
        return cls(
            id=source_node.node.node_id,
            metadata=source_node.node.metadata,
            score=source_node.score,
        )

    @classmethod
    def from_source_nodes(cls, source_nodes: List[NodeWithScore]):
        return [cls.from_source_node(node) for node in source_nodes]


class _Result(BaseModel):
    result: _Message
    nodes: List[_SourceNodes]


async def parse_chat_data(data: _ChatData, ctx: Context) -> Tuple[str, List[ChatMessage]]:
    # check preconditions and get last message
    if len(data.messages) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No messages provided",
        )
    last_message = data.messages.pop()
    if last_message.role != MessageRole.USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Last message must be from user",
        )
    # convert messages coming from the request to type ChatMessage
    for message in data.messages:
        if message.role == MessageRole.ASSISTANT:
            for tool_call in message.toolInvocations:
                if tool_call["toolName"] == "suggest_file_operations":
                    args = FileOperationsResponse(**tool_call["args"]["suggestion"])
                    suggestion_response = await suggest_file_operations(ctx, args)
                    logging.info(f"Suggestion response: {suggestion_response}")

    messages = [
        ChatMessage(
            role=m.role,
            content=m.content,
            tool_calls=m.toolInvocations
        )
        for m in data.messages
    ]
    return last_message.content, messages


# streaming endpoint - delete if not needed
@r.post("")
async def chat(
    request: Request,
    data: _ChatData,
    chat_engine: BaseChatEngine = Depends(get_chat_engine),
):
    attributes = {SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"}
    if (session_id := request.headers.get("X-Session-Id", None)) is not None:
        attributes[SpanAttributes.SESSION_ID] = session_id
    if (user_id := request.headers.get("X-User-Id", None)) is not None:
        attributes[SpanAttributes.USER_ID] = user_id
    llm = OpenAI(temperature=0.5, model="gpt-4o-mini")
    
    
    with tracer.start_as_current_span("chat", attributes=attributes,end_on_exit=False) as span:
        agent = FunctionAgent(
            name="Agent",
            description="You are a useful agent that suggests reorganization of a folder",
            llm=llm,
            tools=[suggestion_tool, apply_file_operations_tool, get_vault_tree_tool],
            system_prompt=system_prompt,
        )
        workflow = AgentWorkflow(agents=[agent])
        ctx = Context(workflow)

        last_message_content, messages = await parse_chat_data(data, ctx)
        span.set_attribute(SpanAttributes.INPUT_VALUE, last_message_content)
        

        handler = workflow.run(
            user_msg=last_message_content,
            chat_history=messages,
            context=ctx
        )
        
        
        async def event_generator():
            full_response = ""
            async for event in handler.stream_events():
                # capture InputRequiredEvent
                if isinstance(event, ToolCall):
                    tool_call = {
                        "toolCallId": event.tool_id,
                        "toolName": event.tool_name,
                        "args": event.tool_kwargs
                    }
                    yield f'9:{json.dumps(tool_call)}\n'
                elif isinstance(event, ToolCallResult):
                    
                    yield f'a:{event.model_dump_json()}\n'
                elif isinstance(event, AgentStream):
                    if event.delta:
                        yield f'0:{json.dumps(event.delta)}\n'
            yield f'd:{{"finishReason":"stop","usage":{{"promptTokens":10,"completionTokens":20}},"isContinued":false}}\n'
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, full_response)
            span.end()

        return StreamingResponse(event_generator(), media_type="text/plain")

class _FeedbackRequest(BaseModel):
    span_id: str
    feedback_score: int

    class Config:
        json_schema_extra = {
            "example": {
                "span_id": "abc123",
                "feedback_score": 1
            }
        }

PHOENIX_API_ENDPOINT = os.getenv("PHOENIX_API_ENDPOINT", "http://localhost:6006")
SPAN_ANNOTATIONS_ENDPOINT = f"{PHOENIX_API_ENDPOINT}/v1/span_annotations"

@r.post("/feedback")
async def feedback(request: Request, data: _FeedbackRequest):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            SPAN_ANNOTATIONS_ENDPOINT,
            json={
                "data": [
                    {
                        "span_id": data.span_id,
                        "annotator_kind": "HUMAN",
                        "name": "feedback",
                        "result": {
                            "label": "👎" if data.feedback_score == 0 else "👍",
                            "score": data.feedback_score,
                            "explanation": "Negative feedback from user" if data.feedback_score == 0 else "Positive feedback from user"
                        }
                    }
                ]
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send feedback"
            )
            
        return {"status": "success"}
