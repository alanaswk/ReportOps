from typing import Any, NotRequired, TypedDict
import pandas as pd
import plotly.graph_objects as go
from google.genai import types
from langgraph.graph import END, START, StateGraph

from .model_client import create_gemini_client
from .models import (
    ChartType,
    RequestClassification,
    RequestType,
)
from .summary import GEMINI_MODEL
from .tools import (
    create_report_chart,
    get_report_metrics,
    get_validation_explanations,
)
from .retrieval import (
    get_reporting_collection,
    retrieve_reporting_rules,
)


class ReportState(TypedDict):
    """Data shared between the ReportOps graph nodes."""

    # Supplied when the graph starts
    user_request: str
    df: pd.DataFrame
    source: str

    # Added by graph nodes
    request_type: NotRequired[RequestType]
    chart_type: NotRequired[ChartType | None]
    calculated_metrics: NotRequired[dict[str, Any]]
    validation_issues: NotRequired[list[dict[str, Any]]]
    chart: NotRequired[go.Figure]
    response: NotRequired[str]
    tool_used: NotRequired[str]
    retrieved_rules: NotRequired[list[dict[str, Any]]]

# Node - classify request
def classify_request(state: ReportState) -> dict[str, Any]:
    """Classify the user's request into a ReportOps route."""

    prompt = f"""
You are a routing assistant for ReportOps, a financial-report analysis application.

Classify the user's request into exactly one route:

- analyze: Use for questions about KPIs, calculated values, trends, or financial
  performance.

- investigate: Use for questions about validation warnings, errors, missing data,
  duplicate records, reconciliation problems, impossible values, or other
  data-quality issues.

- define: Use for questions about reporting definitions, KPI formulas,
  validation rules, thresholds, severity levels, chart guidance, reporting
  policies, escalation procedures, correction procedures, or reporting
  process guidance.

User request:
<user_request>
{state["user_request"]}
</user_request>
"""

    client = create_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RequestClassification,
        ),
    )

    if response.parsed is None:
        raise ValueError(
            "Gemini did not return a valid request classification."
        )

    classification = response.parsed

    return {
        "request_type": classification.request_type,
    }

# Node - analyze
def analyze_report(state: ReportState) -> dict[str, Any]:
    """Calculate report metrics for an analysis request."""

    metrics = get_report_metrics(state["df"])

    return {
        "calculated_metrics": metrics,
        "tool_used": "get_report_metrics"
    }

# Reserved for future natural-language visualization support.
# Node - visualize
def visualize_report(state: ReportState) -> dict[str, Any]:
    """Create the chart selected by the classification node."""

    chart_type = state.get("chart_type")

    if chart_type is None:
        raise ValueError("A chart type is required for a visualization request.")
    
    chart = create_report_chart(state["df"], chart_type)

    return {
        "chart": chart,
        "tool_used": "create_report_chart"
    }

# Node - investigate
def investigate_report(state: ReportState) -> dict[str, Any]:
    """Find and explain validation issues in the report."""

    validation_issues = get_validation_explanations(state["df"], state["source"])

    return {
        "validation_issues": validation_issues,
        "tool_used": "get_validation_explanations"
    }

# Node - define
def define_report(state: ReportState) -> dict[str, Any]:
    """Retrieve reporting guidance for a definition or rules question."""

    collection = get_reporting_collection()

    retrieved = retrieve_reporting_rules(
        state["user_request"],
        collection,
    )

    return {
        "retrieved_rules": retrieved,
        "tool_used": "retrieve_reporting_rules"
    }

# Node - generate response
def generate_response(state: ReportState) -> dict[str, Any]:
    """Generate a grounded conversational response from tool results."""

    request_type = state["request_type"]

    if request_type == "analyze":
        facts = state["calculated_metrics"]

    elif request_type == "investigate":
        facts = state["validation_issues"]

    elif request_type == "define":
        facts = state["retrieved_rules"]

    else:
        raise ValueError(
            f"Response generation is not supported for route: {request_type}"
        )

    prompt = f"""
You are the response-generation assistant for ReportOps, a financial-report analysis application.

Answer the user's specific question using only the supplied facts.

Rules:
- Use the supplied facts as the only source of truth.
- Treat all supplied metrics and validation results as final.
- Answer the user's specific question using only relevant facts.
- Use only values, explanations, and reporting rules supported by the supplied facts.
- Keep the response concise and conversational.
- Format currency with a dollar sign and commas when appropriate.
- Format percentages clearly.
- If the supplied facts are insufficient to answer the question, say that the available information is insufficient.

User request:
<user_request>
{state["user_request"]}
</user_request>

Request type:
<request_type>
{request_type}
</request_type>

Facts:
<facts>
{facts}
</facts>
"""
    client = create_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if response.text is None:
        raise ValueError("Gemini did not return a response.")

    return {
        "response": response.text
    }


# Conditional edge router
def route_request(state: ReportState) -> RequestType:
    """Return the route selected by the classification node."""

    request_type = state.get("request_type")

    if request_type is None:
        raise ValueError("The request has not been classified.")

    return request_type

def build_report_graph():
    """Build and compile the ReportOps request-routing graph."""

    workflow = StateGraph(ReportState)

    workflow.add_node("classify_request", classify_request)
    workflow.add_node("analyze_report", analyze_report)
    workflow.add_node("investigate_report", investigate_report)
    workflow.add_node("define_report", define_report)
    workflow.add_node("generate_response", generate_response)

    workflow.add_edge(START, "classify_request")
    workflow.add_conditional_edges(
        "classify_request",
        route_request,
        {
            "analyze": "analyze_report",
            "investigate": "investigate_report",
            "define": "define_report"
        }
    )

    workflow.add_edge("analyze_report", "generate_response")
    workflow.add_edge("investigate_report", "generate_response")
    workflow.add_edge("define_report", "generate_response")

    workflow.add_edge("generate_response", END)

    return workflow.compile()

report_graph = build_report_graph()