import streamlit as st
from pathlib import Path
import pandas as pd

from src.reportops.ingestion import load_data
from src.reportops.validation import validate_data
from src.reportops.metrics import (
    calculate_revenue_variance,
    calculate_month_over_month_revenue,
    calculate_operating_margin,
    calculate_labor_expense_percentage,
)
from src.reportops.charts import (
    create_actual_vs_budget_chart,
    create_monthly_revenue_trend_chart,
    create_largest_variances_chart,
)
from src.reportops.summary import generate_summary
from src.reportops.graph import report_graph

st.set_page_config(
    page_title="ReportOps",
    page_icon="📊",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("ReportOps")
st.subheader("Agentic Reporting and Data Quality Copilot")

st.write(
    "Validate reporting data, calculate operational KPIs, "
    "and explore interactive charts."
)

st.sidebar.header("Data source")

source_type = st.sidebar.radio(
    "Choose a data source:",
    ("Demo data", "Upload a file"),
)

selected_file = None

if source_type == "Demo data":
    demo_folder = Path("data/demo")

    demo_files = sorted(
        list(demo_folder.glob("*.csv"))
        + list(demo_folder.glob("*.xlsx"))
        + list(demo_folder.glob("*.xls"))
    )

    if demo_files:
        selected_file = st.selectbox(
            "Choose a demo file:",
            demo_files,
            format_func=lambda file: file.name,
        )
    else:
        st.error("No demo files were found in data/demo.")

else:
    selected_file = st.file_uploader(
        "Upload a CSV or Excel file:",
        type=["csv", "xlsx", "xls"],
    )

if selected_file is None:
    st.info("Choose a demo file or upload a file to begin.")
    st.stop()
    
try:
    df = load_data(selected_file)

    st.success(
        f"Loaded {len(df):,} rows and {len(df.columns)} columns."
    )

    st.subheader("Data preview")
    st.dataframe(df.head(20))

    source_name = getattr(selected_file, "name", str(selected_file))
    validation_issues = validate_data(df, source_name)

    data_fingerprint = int(
        pd.util.hash_pandas_object(df, index=True).sum()
    )

    chat_data_key = f"{source_name}:{data_fingerprint}"

    if st.session_state.get("chat_data_key") != chat_data_key:
        st.session_state.messages = []
        st.session_state["chat_data_key"] = chat_data_key

    st.subheader("Validation results")

    if validation_issues:
        st.warning(
            f"Found {len(validation_issues)} validation issue(s)."
        )

        issue_records = [
            issue.model_dump()
            for issue in validation_issues
        ]

        st.dataframe(issue_records)

        issues_csv = pd.DataFrame(issue_records).to_csv(index=False)

        st.download_button(
            label="Download validation report",
            data=issues_csv,
            file_name="validation_issues.csv",
            mime="text/csv",
        )
    else:
        st.success("No validation issues were detected.")

        revenue_metrics = calculate_revenue_variance(df)
        monthly_metrics = calculate_month_over_month_revenue(df)
        margin_metrics = calculate_operating_margin(df)
        labor_metrics = calculate_labor_expense_percentage(df)

        latest_month = monthly_metrics.iloc[-1]
        calculated_metrics = {
            "revenue_variance": revenue_metrics,
            "latest_month_over_month_revenue": latest_month.to_dict(),
            "operating_margin": margin_metrics,
            "labor_expense_percentage": labor_metrics
        }

        st.subheader("Key performance indicators")

        revenue_column, monthly_column, margin_column, labor_column = st.columns(4)

        revenue_column.metric(
            label="Revenue variance",
            value=f"${revenue_metrics['variance_amount']:,.0f}",
            delta=(
                f"{revenue_metrics['variance_percent']:.1f}%"
                if revenue_metrics["variance_percent"] is not None
                else "N/A"
            ),
        )

        monthly_column.metric(
            label="Month-over-month change",
            value=f"${latest_month['change_amount']:,.0f}",
            delta=(
                f"{latest_month['change_percent']:.1f}%"
                if pd.notna(latest_month["change_percent"])
                else "N/A"
            ),
        )

        margin_column.metric(
            label="Operating margin",
            value=(
                f"{margin_metrics['operating_margin_percent']:.1f}%"
                if margin_metrics["operating_margin_percent"] is not None
                else "N/A"
            ),
        )

        labor_column.metric(
            label="Labor expense",
            value=(
                f"{labor_metrics['labor_expense_percent']:.1f}%"
                if labor_metrics["labor_expense_percent"] is not None
                else "N/A"
            ),
        )

        st.subheader("Charts")

        budget_tab, trend_tab, variance_tab = st.tabs(
            [
                "Actual vs. budget",
                "Monthly trend",
                "Largest variances",
            ]
        )

        with budget_tab:
            budget_chart = create_actual_vs_budget_chart(df)
            st.plotly_chart(budget_chart, use_container_width=True)

        with trend_tab:
            trend_chart = create_monthly_revenue_trend_chart(df)
            st.plotly_chart(trend_chart, use_container_width=True)

        with variance_tab:
            variance_chart = create_largest_variances_chart(df)
            st.plotly_chart(variance_chart, use_container_width=True)

        summary_key = f"{source_name}:{data_fingerprint}"

        if st.session_state.get("summary_key") != summary_key:
            summary_text, summary_source = generate_summary(
                df,
                calculated_metrics,
                validation_issues,
            )

            st.session_state["summary_key"] = summary_key
            st.session_state["summary_text"] = summary_text
            st.session_state["summary_source"] = summary_source

        summary_text = st.session_state["summary_text"]
        summary_source = st.session_state["summary_source"]
        display_summary = summary_text.replace("$", r"\$")

        st.markdown(display_summary)

        if summary_source == "gemini":
            st.caption("Generated by Gemini from validated, calculated facts.")
        else:
            st.caption("Gemini unavailable. Showing the deterministic fallback summary.")

        st.subheader("Downloads")

        data_csv = df.to_csv(index=False)

        download_data_column, download_summary_column = st.columns(2)

        with download_data_column:
            st.download_button(
                label="Download normalized data",
                data=data_csv,
                file_name="reportops_normalized_data.csv",
                mime="text/csv",
            )

        with download_summary_column:
            st.download_button(
                label="Download executive summary",
                data=summary_text,
                file_name="reportops_summary.txt",
                mime="text/plain",
            )

    st.divider()
    st.subheader("Ask ReportOps")

    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            display_content = message["content"].replace("$", r"\$")
            st.markdown(display_content)

            if message.get("chart") is not None:
                st.plotly_chart(
                    message["chart"],
                    use_container_width=True,
                    key=f"history_chart_{index}",
                )

            if message.get("tool_used"):
                st.caption(f"Tool used: {message['tool_used']}")

            if message.get("source_document") and message.get("source_section"):
                source_text = (
                    f"Source: {message['source_document']} — "
                    f"{message['source_section']}"
                )

                if message.get("source_page") is not None:
                    source_text += f" — Page {message['source_page']}"

                st.caption(source_text)
                
    prompt = st.chat_input("Ask a question about the report")

    if prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        result = report_graph.invoke({
            "user_request": prompt,
            "df": df,
            "source": source_name,
        })

        request_type = result["request_type"]
        tool_used = result["tool_used"]

        source_document = None
        source_section = None
        source_page = None
        chat_chart = None

        if request_type in {"analyze", "investigate", "define"}:
            assistant_response = result["response"]

            if request_type == "define":
                retrieved_rules = result["retrieved_rules"]

                if retrieved_rules:
                    top_result = retrieved_rules[0]

                    source_document = top_result["document"]
                    source_section = top_result["section"]
                    source_page = top_result.get("page")

        elif request_type == "visualize":
            assistant_response = "Here is the requested chart."
            chat_chart = result["chart"]

        with st.chat_message("assistant"):
            display_response = assistant_response.replace("$", r"\$")
            st.markdown(display_response)

            if chat_chart is not None:
                st.plotly_chart(
                    chat_chart,
                    use_container_width=True,
                    key=f"current_chart_{len(st.session_state.messages)}",
                )

            st.caption(f"Tool used: {tool_used}")

            if source_document and source_section:
                source_text = f"Source: {source_document} — {source_section}"

                if source_page is not None:
                    source_text += f" — Page {source_page}"

                st.caption(source_text)

        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response,
            "tool_used": tool_used,
            "source_document": source_document,
            "source_section": source_section,
            "source_page": source_page,
            "chart": chat_chart,
        })

except FileNotFoundError:
    st.error("The selected file could not be found.")

except pd.errors.EmptyDataError:
    st.error("The selected file is empty.")

except pd.errors.ParserError:
    st.error(
        "The file could not be parsed. Check that it is a valid CSV file."
    )

except ValueError as error:
    st.error(f"The file could not be processed: {error}")

except Exception as error:
    st.error(
        "An unexpected error occurred while processing the file."
    )

    with st.expander("Technical details"):
        st.code(str(error))