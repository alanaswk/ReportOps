import pytest
import pandas as pd
from pydantic import ValidationError
from reportops.models import SupportedClaim
from reportops.summary import (
    prepare_summary_facts,
    build_summary_prompt,
    generate_summary
)

def test_prepare_summary_facts_packages_trusted_inputs():
    metrics = {
        "revenue_variance_dollars": -5000.0,
        "operating_margin_percent": 18.5
    }

    facts = prepare_summary_facts(calculated_metrics=metrics, validation_issues=[])

    assert facts["calculated_metrics"] == metrics
    assert facts["validation_issues"] == []

def test_build_summary_prompt_contains_trusted_facts():
    facts = {
        "calculated_metrics": {
            "revenue_variance_dollars = -5000.0"
        },
        "validation_issues": []
    }

    prompt = build_summary_prompt(facts=facts)

    assert "revenue_variance_dollars" in prompt
    assert "-5000.0" in prompt

def test_supported_claim_requires_evidence():
    with pytest.raises(ValidationError):
        SupportedClaim(statement="Revenue was below budget.", evidence=[])

def test_generate_summary_uses_fallback_when_llm_fails(monkeypatch):
    df = pd.DataFrame(
        {
            "month": pd.to_datetime(["2026-01-01", "2026-02-01"]),
            "revenue": [100000, 110000],
            "budget_revenue": [105000, 105000],
            "labor_expense": [40000, 42000],
            "other_expense": [30000, 32000],
            "total_expense": [70000, 74000],
        }
    )

    def fake_llm_failure(*args, **kwargs):
        raise RuntimeError("Simulated Gemini failure")

    monkeypatch.setattr(
        "reportops.summary.generate_llm_summary",
        fake_llm_failure,
    )

    summary_text, source = generate_summary(
        df=df,
        calculated_metrics={},
        validation_issues=[],
    )

    assert source == "fallback"
    assert "Total revenue was" in summary_text