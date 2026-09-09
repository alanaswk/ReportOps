import pytest
import pandas as pd
from types import SimpleNamespace

from src.reportops.graph import route_request
import src.reportops.graph as graph_module
from src.reportops.models import RequestClassification

@pytest.mark.parametrize(
    "request_type",
    [
        "analyze",
        "investigate",
        "define",
    ],
)
def test_route_request_returns_selected_route(request_type):
    state = {
        "request_type": request_type,
    }

    result = route_request(state)

    assert result == request_type


def test_route_request_requires_classification():
    state = {}

    with pytest.raises(
        ValueError,
        match="The request has not been classified",
    ):
        route_request(state)

def test_analyze_report_uses_metrics_tool(monkeypatch):
    sample_df = pd.DataFrame({"revenue": [100_000]})
    expected_metrics = {
        "operating_margin": {"amount": 25_000},
    }

    def fake_get_report_metrics(df):
        assert df is sample_df
        return expected_metrics

    monkeypatch.setattr(
        graph_module,
        "get_report_metrics",
        fake_get_report_metrics,
    )

    result = graph_module.analyze_report(
        {
            "df": sample_df,
        }
    )

    assert result == {
        "calculated_metrics": expected_metrics,
        "tool_used": "get_report_metrics",
    }

# Tests reserved visualization functionality for possible future use.
def test_visualize_report_uses_selected_chart_type(monkeypatch):
    sample_df = pd.DataFrame({"revenue": [100_000]})
    expected_chart = object()

    def fake_create_report_chart(df, chart_type):
        assert df is sample_df
        assert chart_type == "monthly_revenue"
        return expected_chart

    monkeypatch.setattr(
        graph_module,
        "create_report_chart",
        fake_create_report_chart,
    )

    result = graph_module.visualize_report(
        {
            "df": sample_df,
            "chart_type": "monthly_revenue",
        }
    )

    assert result == {
        "chart": expected_chart,
        "tool_used": "create_report_chart",
    }

# Tests reserved visualization functionality for possible future use.
def test_visualize_report_requires_chart_type():
    state = {
        "df": pd.DataFrame(),
        "chart_type": None,
    }

    with pytest.raises(
        ValueError,
        match="A chart type is required",
    ):
        graph_module.visualize_report(state)

def test_investigate_report_uses_validation_tool(monkeypatch):
    sample_df = pd.DataFrame({"location_id": ["L001"]})
    source = "sample.csv"

    expected_issues = [
        {
            "type": "duplicate_record",
            "severity": "warning",
            "source": source,
            "explanation": "A duplicate record was found.",
            "suggested_action": "Review the duplicate record.",
        }
    ]

    def fake_get_validation_explanations(df, supplied_source):
        assert df is sample_df
        assert supplied_source == source
        return expected_issues

    monkeypatch.setattr(
        graph_module,
        "get_validation_explanations",
        fake_get_validation_explanations,
    )

    result = graph_module.investigate_report(
        {
            "df": sample_df,
            "source": source,
        }
    )

    assert result == {
                "validation_issues": expected_issues,
                "tool_used": "get_validation_explanations"
            }

def test_classify_request_returns_parsed_classification(monkeypatch):
    classification = RequestClassification(
        request_type="analyze",
    )

    fake_response = SimpleNamespace(parsed=classification)

    class FakeModels:
        def generate_content(self, **kwargs):
            return fake_response

    fake_client = SimpleNamespace(models=FakeModels())

    monkeypatch.setattr(
        graph_module,
        "create_gemini_client",
        lambda: fake_client,
    )

    result = graph_module.classify_request(
        {
            "user_request": "What is the operating margin?",
        }
    )

    assert result == {
        "request_type": "analyze",
    }


def test_compiled_graph_routes_to_analyze(monkeypatch):
    sample_df = pd.DataFrame({"revenue": [100_000]})
    expected_metrics = {
        "operating_margin": {"amount": 25_000},
    }

    def fake_classify_request(state):
        return {
            "request_type": "analyze",
        }

    def fake_get_report_metrics(df):
        assert df is sample_df
        return expected_metrics

    def fake_generate_response(state):
        assert state["calculated_metrics"] == expected_metrics
        return {
            "response": "The operating margin is $25,000."
        }
    
    monkeypatch.setattr(
        graph_module,
        "classify_request",
        fake_classify_request,
    )
    monkeypatch.setattr(
        graph_module,
        "get_report_metrics",
        fake_get_report_metrics,
    )
    monkeypatch.setattr(
        graph_module,
        "generate_response",
        fake_generate_response,
    )
    

    # Rebuild after monkeypatching so the graph registers the fake classifier.
    test_graph = graph_module.build_report_graph()

    result = test_graph.invoke(
        {
            "user_request": "What is the operating margin?",
            "df": sample_df,
            "source": "sample.csv",
        }
    )

    assert result["request_type"] == "analyze"
    assert result["calculated_metrics"] == expected_metrics
    assert result["tool_used"] == "get_report_metrics"
    assert "chart" not in result
    assert "validation_issues" not in result
    assert result["response"] == "The operating margin is $25,000."

def test_define_report_uses_retrieval_tool(monkeypatch):
    expected_rules = [
        {
            "section": "Operating Margin",
            "document": "ReportOps Reporting Handbook",
            "text": "Operating margin is...",
            "distance": 0.1,
        }
    ]

    fake_collection = object()

    monkeypatch.setattr(
        graph_module,
        "get_reporting_collection",
        lambda: fake_collection,
    )

    def fake_retrieve_reporting_rules(question, collection):
        assert question == "How is operating margin calculated?"
        assert collection is fake_collection
        return expected_rules

    monkeypatch.setattr(
        graph_module,
        "retrieve_reporting_rules",
        fake_retrieve_reporting_rules,
    )

    result = graph_module.define_report(
        {
            "user_request": "How is operating margin calculated?",
        }
    )

    assert result == {
        "retrieved_rules": expected_rules,
        "tool_used": "retrieve_reporting_rules",
    }

def test_generate_response_uses_analyze_facts(monkeypatch):
    fake_response = SimpleNamespace(
        text="The operating margin is 25.0%."
    )

    class FakeModels:
        def generate_content(self, **kwargs):
            assert "operating_margin" in kwargs["contents"]
            assert "What is the operating margin?" in kwargs["contents"]
            return fake_response

    fake_client = SimpleNamespace(models=FakeModels())

    monkeypatch.setattr(
        graph_module,
        "create_gemini_client",
        lambda: fake_client,
    )

    result = graph_module.generate_response(
        {
            "user_request": "What is the operating margin?",
            "request_type": "analyze",
            "calculated_metrics": {
                "operating_margin": {
                    "operating_margin_percent": 25.0,
                }
            },
        }
    )

    assert result == {
        "response": "The operating margin is 25.0%."
    }