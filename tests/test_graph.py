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
        "visualize",
        "investigate",
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
        request_type="visualize",
        chart_type="monthly_revenue",
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
            "user_request": "Show me monthly revenue.",
        }
    )

    assert result == {
        "request_type": "visualize",
        "chart_type": "monthly_revenue",
    }


def test_compiled_graph_routes_to_analyze(monkeypatch):
    sample_df = pd.DataFrame({"revenue": [100_000]})
    expected_metrics = {
        "operating_margin": {"amount": 25_000},
    }

    def fake_classify_request(state):
        return {
            "request_type": "analyze",
            "chart_type": None,
        }

    def fake_get_report_metrics(df):
        assert df is sample_df
        return expected_metrics

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