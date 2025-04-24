from llama_index.core.workflow import step, Event
from llama_index.core.workflow.retry_policy import RetryPolicy
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Type

from llama_index.core.bridge.pydantic import BaseModel, ConfigDict

from llama_index.core.workflow.errors import WorkflowValidationError
from llama_index.core.workflow.utils import (
    is_free_function,
    validate_step_signature,
    inspect_signature,
    ServiceDefinition,
)
from llama_index.core.workflow.decorators import StepConfig

if TYPE_CHECKING:  # pragma: no cover
    from llama_index.core.workflow import Workflow
from llama_index.core.workflow.retry_policy import RetryPolicy


from typing import Any, Callable, Optional, Type


def visible_step(
    *args: Any,
    workflow: Optional[Type["Workflow"]] = None,
    pass_context: bool = False,
    num_workers: int = 4,
    retry_policy: Optional[RetryPolicy] = None,
) -> Callable:
    
    def decorator(func: Callable) -> Callable:
        decorated_step = step(
            *args,
            workflow=workflow,
            pass_context=pass_context,
            num_workers=num_workers,
            retry_policy=retry_policy,
        )(func)
        def function_wrapper(*args, **kwargs) -> Any:
            res = decorated_step(*args, **kwargs)
            # raise Exception("visible_step")
            print(res)
            print("visible_step")
            if isinstance(res, Event):
                workflow.ctx.write_event_to_stream(res)

            return res
        function_wrapper.__step_config = decorated_step.__step_config
        # print(function_wrapper.__step_config)
        return decorated_step
    print("visible_step run ")
    return decorator
