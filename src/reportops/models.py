from typing import Literal
from pydantic import BaseModel, Field

class ValidationIssue(BaseModel):
    """A class to represent a validation issue in the data."""
    type: str
    severity: Literal["error", "warning"]
    source: str
    explanation: str
    suggested_action: str

class SupportedClaim(BaseModel):
    statement: str = Field(
        description="A concise observation directly supported by the supplied facts."
    )
    evidence: list[str] = Field(
        min_length=1,
        description=(
            "One or more exact metric names, values, or validation results "
            "that support the statement."
        ),
    )

class ReportSummary(BaseModel):
    major_findings: list[SupportedClaim] = Field(
        min_length=1,
        description="The most important observations supported by the report facts.",
    )
    concerns: list[SupportedClaim] = Field(
        description=(
            "Unfavorable results or validation problems supported by the facts. "
            "Use an empty list when there are none."
        ),
    )
    executive_summary: str = Field(
        description=(
            "A two-to-four-sentence overview of the supported findings and concerns."
        ),
    )