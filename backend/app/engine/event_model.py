from llama_index.core.llms import MessageRole
from pydantic import BaseModel


from typing import Any, Dict, List, Optional


class ToolInvocation(BaseModel):
    state: str
    args: Dict[str, Any]
    toolName: str
    toolCallId: str


class _Message(BaseModel):
    role: MessageRole
    content: str
    toolInvocations: Optional[List[Any]] = None