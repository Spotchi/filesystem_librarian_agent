
from typing import Literal
from pydantic import BaseModel

class StepChoice(BaseModel):
    """A choice of the nextstep to take."""
    type: Literal['clarification', 'operations', 'confirmation']
    reason: str

