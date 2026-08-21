from typing import Literal
from pydantic import BaseModel

class ValidationIssue(BaseModel):
    """A class to represent a validation issue in the data."""
    type: str
    severity: Literal["error", "warning"]
    source: str
    explanation: str
    suggested_action: str