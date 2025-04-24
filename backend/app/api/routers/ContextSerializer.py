from llama_index.core.workflow.context_serializers import BaseSerializer

import json
from typing import Any
import base64
import json
import pickle
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

from llama_index.core.schema import BaseComponent
from llama_index.core.workflow.utils import import_module_from_qualified_name, get_qualified_name
from llama_index.core.workflow.context import Context
from llama_index.core.memory.chat_memory_buffer import ChatMemoryBuffer

class ContextSerializer(BaseSerializer):
    def _serialize_value(self, value: Any) -> Any:
        """Helper to serialize a single value."""
        if isinstance(value, BaseComponent):
            return {
                "__is_component": True,
                "value": value.to_dict(),
                "qualified_name": get_qualified_name(value),
            }
        elif isinstance(value, BaseModel):
            return None
            # print(value.model_dump())
            # return {
            #     "__is_pydantic": True,
            #     "value": value.model_dump(),
            #     "qualified_name": get_qualified_name(value),
            # }
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, ChatMemoryBuffer):
            return None
        return None
        # return value
    
    
    def serialize(self, value: Any) -> str:
        try:
            serialized_value = self._serialize_value(value)
            return json.dumps(serialized_value)
        except Exception as e:
            print(e)
            raise ValueError(f"Failed to serialize value: {type(value)}: {value!s}")


    def _deserialize_value(self, data: Any) -> Any:
        """Helper to deserialize a single value."""
        if isinstance(data, dict):
            if data.get("__is_pydantic") and data.get("qualified_name"):
                module_class = import_module_from_qualified_name(data["qualified_name"])
                return module_class.model_validate(data["value"])
            elif data.get("__is_component") and data.get("qualified_name"):
                module_class = import_module_from_qualified_name(data["qualified_name"])
                return module_class.from_dict(data["value"])
            return {k: self._deserialize_value(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deserialize_value(item) for item in data]
        return data

    def deserialize(self, value: str) -> Any:
        data = json.loads(value)
        return self._deserialize_value(data)
