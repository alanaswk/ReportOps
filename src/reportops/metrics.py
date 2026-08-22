import pandas as pd


def calculate_revenue_variance(df: pd.DataFrame) -> dict:
    """Calculate total actual revenue variance against budget."""

    actual_revenue = df["revenue"].sum()
    budget_revenue = df["budget_revenue"].sum()

    variance_amount = actual_revenue - budget_revenue
    if budget_revenue == 0:
        variance_percent = None
    else:
        variance_percent = (variance_amount / budget_revenue) * 100

    return {
        "actual_revenue": actual_revenue,
        "budget_revenue": budget_revenue,
        "variance_amount": variance_amount,
        "variance_percent": variance_percent,
    }

def calculate_month_over_month_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly revenue and its change from the prior month."""

    monthly_revenue = (
        df.groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")
        .reset_index(drop=True)
    )

    monthly_revenue["prior_month_revenue"] = monthly_revenue["revenue"].shift(1)
    monthly_revenue["change_amount"] = monthly_revenue["revenue"] - monthly_revenue["prior_month_revenue"]
    monthly_revenue["change_percent"] =(monthly_revenue["change_amount"] / monthly_revenue["prior_month_revenue"]) * 100

    return monthly_revenue

def calculate_operating_margin(df: pd.DataFrame) -> dict:
    """Calculate operating income and operating margin."""

    total_revenue = df["revenue"].sum()
    total_expense = df["labor_expense"].sum() + df["other_expense"].sum()
    operating_income = total_revenue - total_expense
    
    if total_revenue == 0:
        operating_margin_percent = None
    else:
        operating_margin_percent = (operating_income / total_revenue) * 100

    return {
        "total_revenue": total_revenue,
        "total_expense": total_expense,
        "operating_income": operating_income,
        "operating_margin_percent": operating_margin_percent
    }

def calculate_labor_expense_percentage(df: pd.DataFrame) -> dict:
    """Calculate labor expense as a percentage of revenue."""

    total_labor_expense = df["labor_expense"].sum()
    total_revenue = df["revenue"].sum()

    if total_revenue == 0:
        labor_expense_percent = None
    else:
        labor_expense_percent = (total_labor_expense / total_revenue) * 100

    return {
        "total_labor_expense": total_labor_expense,
        "total_revenue": total_revenue,
        "labor_expense_percent": labor_expense_percent
    }