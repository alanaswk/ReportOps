import pandas as pd
from reportops.summary import generate_fallback_summary

def test_generate_fallback_summary():
    df = pd.DataFrame(
        {
            "month": pd.to_datetime(
                ["2026-01-01", "2026-02-01"]
            ),
            "revenue": [100, 120],
            "budget_revenue": [100, 100],
            "labor_expense": [30, 36],
            "other_expense": [50, 54],
        }
    )

    summary = generate_fallback_summary(df)

    assert "Total revenue was $220" in summary
    assert "$20 (10.0%)" in summary
    assert "above budget" in summary
    assert "Operating margin was 22.7%" in summary
    assert "Labor expense represented 30.0%" in summary
    assert "Revenue increased 20.0%" in summary