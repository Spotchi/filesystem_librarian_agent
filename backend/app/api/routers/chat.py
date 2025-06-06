from typing import List, Tuple
import logging
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
import nest_asyncio

from app.engine.event_model import _Message
from app.engine.source_model import _SourceNodes

from app.engine.workflows.orchestrate_suggest import orchestrate_suggest_workflow

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.agent.workflow import AgentStream, ToolCall, ToolCallResult
from llama_index.core.memory import ChatMemoryBuffer
from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from pydantic import BaseModel
import os
import httpx
import json

from app.supabase_utils import get_memory, save_memory

nest_asyncio.apply()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

tracer = trace.get_tracer(__name__)

chat_router = r = APIRouter()


@r.head("/healthcheck")
@r.get("/healthcheck")
def healthcheck():
    return "Hello world!"


class _ChatData(BaseModel):
    id: str
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


class _Result(BaseModel):
    result: _Message
    nodes: List[_SourceNodes]


async def parse_chat_data(data: _ChatData) -> Tuple[str, List[ChatMessage]]:
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
        
    messages = [
        ChatMessage(role=m.role, content=m.content, tool_calls=m.toolInvocations)
        for m in data.messages
    ]
    return last_message.content, messages


# streaming endpoint - delete if not needed
@r.post("")
async def chat(
    request: Request,
    data: _ChatData,
):
    run_id = data.id
    attributes = {SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"}
    if (session_id := request.headers.get("X-Session-Id", None)) is not None:
        attributes[SpanAttributes.SESSION_ID] = session_id
    if (user_id := request.headers.get("X-User-Id", None)) is not None:
        attributes[SpanAttributes.USER_ID] = user_id

    memory = get_memory(run_id)
    if memory is None:
        memory = ChatMemoryBuffer.from_defaults(token_limit=40000)

    with tracer.start_as_current_span(
        "chat", attributes=attributes, end_on_exit=False
    ) as span:
        
        workflow = orchestrate_suggest_workflow()
        
        last_message_content, messages = await parse_chat_data(data)
        span.set_attribute(SpanAttributes.INPUT_VALUE, last_message_content)

        handler = workflow.run(
            user_msg=last_message_content,
            # chat_history=messages,
            memory=memory,
        )

        async def event_generator():
            full_response = ""
            async for event in handler.stream_events():

                # capture InputRequiredEvent
                if isinstance(event, ToolCallResult):
                    tool_call_result = {
                        "toolCallId": event.tool_id,
                        "result": event.tool_output.model_dump(),
                    }
                    yield f"a:{json.dumps(tool_call_result)}\n"
                elif isinstance(event, ToolCall):
                    tool_call = {
                        "toolCallId": event.tool_id,
                        "toolName": event.tool_name,
                        "args": event.tool_kwargs,
                    }
                    yield f"9:{json.dumps(tool_call)}\n"
                elif isinstance(event, AgentStream):
                    if event.delta:
                        yield f"0:{json.dumps(event.delta)}\n"
                else:
                    print(type(event))
            yield 'd:{"finishReason":"stop","usage":{"promptTokens":10,"completionTokens":20},"isContinued":false}\n'
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, full_response)
            logger.info(f"Saving memory to disk: {id}")
            with open(f"checkpoints/{id}.json", "w") as f:
                f.write(memory.model_dump_json())
                
            # save memory to supabase
            save_memory(run_id=run_id, memory=memory)

            span.end()

        return StreamingResponse(event_generator(), media_type="text/plain")


class _FeedbackRequest(BaseModel):
    span_id: str
    feedback_score: int

    class Config:
        json_schema_extra = {"example": {"span_id": "abc123", "feedback_score": 1}}


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
                            "explanation": (
                                "Negative feedback from user"
                                if data.feedback_score == 0
                                else "Positive feedback from user"
                            ),
                        },
                    }
                ]
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send feedback",
            )

        return {"status": "success"}
