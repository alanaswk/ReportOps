from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from reportops.charts import (
    create_actual_vs_budget_chart,
    create_largest_variances_chart,
    create_monthly_revenue_trend_chart,
)
from reportops.ingestion import load_data
from reportops.metrics import (
    calculate_labor_expense_percentage,
    calculate_month_over_month_revenue,
    calculate_operating_margin,
    calculate_revenue_variance,
)
from reportops.summary import generate_fallback_summary
from reportops.validation import validate_data


DATA_PATH = PROJECT_ROOT / "data/demo/clean_operations_data.csv"
OUTPUT_DIRECTORY = PROJECT_ROOT / "outputs/day3"


def main() -> None:
    """Run the complete deterministic reporting workflow."""

    df = load_data(DATA_PATH)

    validation_issues = validate_data(
        df,
        source=DATA_PATH.name,
    )

    if validation_issues:
        print(
            f"Validation failed with "
            f"{len(validation_issues)} issue(s):"
        )

        for issue in validation_issues:
            print(issue.model_dump_json(indent=2))

        raise SystemExit(1)

    print("Validation passed.")

    revenue_variance = calculate_revenue_variance(df)
    operating_margin = calculate_operating_margin(df)
    labor_percentage = calculate_labor_expense_percentage(df)
    monthly_revenue = calculate_month_over_month_revenue(df)

    print("\nRevenue variance:")
    print(revenue_variance)

    print("\nOperating margin:")
    print(operating_margin)

    print("\nLabor expense percentage:")
    print(labor_percentage)

    print("\nMonth-over-month revenue:")
    print(monthly_revenue.to_string(index=False))

    summary = generate_fallback_summary(df)

    print("\nFallback summary:")
    print(summary)

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    actual_vs_budget_chart = create_actual_vs_budget_chart(df)
    monthly_trend_chart = create_monthly_revenue_trend_chart(df)
    largest_variances_chart = create_largest_variances_chart(df)

    actual_vs_budget_chart.write_html(
        OUTPUT_DIRECTORY / "actual_vs_budget.html"
    )
    monthly_trend_chart.write_html(
        OUTPUT_DIRECTORY / "monthly_revenue_trend.html"
    )
    largest_variances_chart.write_html(
        OUTPUT_DIRECTORY / "largest_variances.html"
    )

    print(f"\nCharts saved to: {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()