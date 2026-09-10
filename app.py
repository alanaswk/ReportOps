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


# Reduce Streamlit's default top padding and add light visual polish.
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2rem;
        }

        .reportops-hero {
            position: relative;
            background: #f8f9fb;
            border: 1px solid #e6e8ec;
            border-radius: 0.9rem;
            padding: 1.6rem 1.8rem 1.5rem 2rem;
            margin-bottom: 1rem;
        }

        .reportops-hero::before {
            content: "";
            position: absolute;
            left: 0;
            top: 1.2rem;
            bottom: 1.2rem;
            width: 4px;
            border-radius: 0 4px 4px 0;
            background: #ff4b4b;
        }

        .reportops-title {
            margin: 0 0 0.55rem 0;
            font-size: 3rem;
            font-weight: 700;
            line-height: 1.05;
            letter-spacing: -0.035em;
        }

        .reportops-subtitle {
            margin: 0 0 0.7rem 0;
            font-size: 1.65rem;
            font-weight: 650;
            line-height: 1.2;
        }

        .reportops-description {
            margin: 0;
            font-size: 1rem;
            line-height: 1.6;
            opacity: 0.82;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #fbfbfc;
            border-color: #e3e5e9;
            border-radius: 0.8rem;
        }

        div[data-testid="stMetric"] {
            background: #fafbfc;
            border: 1px solid #eceef1;
            border-radius: 0.7rem;
            padding: 0.9rem 1rem;
        }

        div[data-testid="stTabs"] button[role="tab"] {
            font-weight: 600;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }

        @media (prefers-color-scheme: dark) {
            .reportops-hero {
                background: rgba(255, 255, 255, 0.035);
                border-color: rgba(255, 255, 255, 0.10);
            }

            div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stMetric"] {
                background: rgba(255, 255, 255, 0.025);
                border-color: rgba(255, 255, 255, 0.09);
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []


TOOL_LABELS = {
    "get_report_metrics": "Performance analysis",
    "get_validation_explanations": "Validation analysis",
    "retrieve_reporting_rules": "Reporting guidance retrieval",
}


def format_tool_label(tool_name):
    if not tool_name:
        return None

    return TOOL_LABELS.get(
        tool_name,
        tool_name.replace("_", " ").title(),
    )


def split_summary_sections(summary_text):
    """Separate the executive summary from supporting findings."""

    supporting_marker = "### Major Findings"

    if supporting_marker not in summary_text:
        return summary_text, None

    executive_summary, supporting_details = summary_text.split(
        supporting_marker,
        1,
    )

    supporting_details = (
        supporting_marker
        + supporting_details
    )

    return (
        executive_summary.strip(),
        supporting_details.strip(),
    )


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="reportops-hero">
        <div class="reportops-title">ReportOps</div>
        <div class="reportops-subtitle">
            Agentic Reporting and Data Quality Copilot
        </div>
        <p class="reportops-description">
            Validate reporting data, calculate trusted KPIs,
            generate visualizations, and ask grounded questions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Compact dataset controls
# ---------------------------------------------------------

with st.container(border=True):
    dataset_column, source_column, file_column = st.columns(
        [0.7, 1.6, 4.7]
    )

    with dataset_column:
        st.markdown("**Dataset**")

    with source_column:
        source_type = st.radio(
            "Choose a data source:",
            ("Demo data", "Upload one file"),
            horizontal=True,
            label_visibility="collapsed",
        )

    selected_file = None

    with file_column:
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
                    label_visibility="collapsed",
                )
            else:
                st.error("No demo files were found in data/demo.")

        else:
            with st.popover(
                "Choose one CSV or Excel file",
                use_container_width=True,
            ):
                selected_file = st.file_uploader(
                    "Upload one CSV or Excel file:",
                    type=["csv", "xlsx", "xls"],
                    accept_multiple_files=False,
                    label_visibility="collapsed",
                )

            if selected_file is not None:
                st.caption(
                    f"Selected file: `{selected_file.name}`"
                )


if selected_file is None:
    st.info("Choose a demo file or upload a file to begin.")
    st.stop()


try:
    df = load_data(selected_file)

    source_name = getattr(
        selected_file,
        "name",
        str(selected_file),
    )

    validation_issues = validate_data(
        df,
        source_name,
    )

    data_fingerprint = int(
        pd.util.hash_pandas_object(
            df,
            index=True,
        ).sum()
    )

    chat_data_key = f"{source_name}:{data_fingerprint}"

    if st.session_state.get("chat_data_key") != chat_data_key:
        st.session_state.messages = []
        st.session_state["chat_data_key"] = chat_data_key

    st.caption(
        f"Current dataset: `{source_name}` · "
        f"{len(df):,} rows × {len(df.columns)} columns"
    )


    # -----------------------------------------------------
    # Main navigation
    # -----------------------------------------------------

    quality_tab, report_tab, chat_tab = st.tabs(
        [
            "Data Quality",
            "Report",
            "Ask ReportOps",
        ]
    )


    # =====================================================
    # DATA QUALITY TAB
    # =====================================================

    with quality_tab:
        st.subheader("Validation results")

        if validation_issues:
            st.warning(
                f"Validation completed · "
                f"{len(validation_issues)} issue(s) found · "
                f"{len(df):,} rows × {len(df.columns)} columns"
            )

            issue_records = [
                issue.model_dump()
                for issue in validation_issues
            ]

            st.dataframe(
                issue_records,
                use_container_width=True,
            )

            issues_csv = (
                pd.DataFrame(issue_records)
                .to_csv(index=False)
            )

            st.download_button(
                label="Download validation report",
                data=issues_csv,
                file_name="validation_issues.csv",
                mime="text/csv",
            )

        else:
            st.success(
                f"Validation passed · 0 issues · "
                f"{len(df):,} rows × {len(df.columns)} columns"
            )

        st.subheader("Data preview")

        st.dataframe(
            df.head(20),
            use_container_width=True,
        )


    # =====================================================
    # REPORT TAB
    # =====================================================

    with report_tab:
        if validation_issues:
            st.warning(
                "Report metrics are unavailable because this file "
                "contains validation issues. Review the Data Quality "
                "tab for details."
            )

        else:
            revenue_metrics = calculate_revenue_variance(df)

            monthly_metrics = (
                calculate_month_over_month_revenue(df)
            )

            margin_metrics = calculate_operating_margin(df)

            labor_metrics = (
                calculate_labor_expense_percentage(df)
            )

            latest_month = monthly_metrics.iloc[-1]

            calculated_metrics = {
                "revenue_variance": revenue_metrics,
                "latest_month_over_month_revenue":
                    latest_month.to_dict(),
                "operating_margin": margin_metrics,
                "labor_expense_percentage": labor_metrics,
            }

            # KPI cards
            st.subheader("Key performance indicators")

            (
                revenue_column,
                monthly_column,
                margin_column,
                labor_column,
            ) = st.columns(4)

            revenue_column.metric(
                label="Revenue variance to budget",
                value=f"${revenue_metrics['variance_amount']:,.0f}",
                delta=(
                    f"{revenue_metrics['variance_percent']:.1f}%"
                    if revenue_metrics["variance_percent"] is not None
                    else "N/A"
                ),
            )

            monthly_column.metric(
                label="Latest month-over-month change",
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
                label="Labor expense %",
                value=(
                    f"{labor_metrics['labor_expense_percent']:.1f}%"
                    if labor_metrics["labor_expense_percent"] is not None
                    else "N/A"
                ),
            )

            # Executive summary
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

            executive_summary, supporting_details = (
                split_summary_sections(summary_text)
            )

            display_executive_summary = executive_summary.replace(
                "$",
                r"\$",
            )

            st.markdown(display_executive_summary)

            if supporting_details:
                with st.expander(
                    "Supporting findings and evidence"
                ):
                    display_supporting_details = (
                        supporting_details.replace(
                            "$",
                            r"\$",
                        )
                    )

                    st.markdown(display_supporting_details)

            if summary_source == "gemini":
                st.caption(
                    "Generated by Gemini from validated, calculated facts."
                )
            else:
                st.caption(
                    "Gemini unavailable. Showing the deterministic "
                    "fallback summary."
                )

            # Charts
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

                st.plotly_chart(
                    budget_chart,
                    use_container_width=True,
                    key="report_budget_chart",
                )

            with trend_tab:
                trend_chart = create_monthly_revenue_trend_chart(df)

                st.plotly_chart(
                    trend_chart,
                    use_container_width=True,
                    key="report_trend_chart",
                )

            with variance_tab:
                variance_chart = create_largest_variances_chart(df)

                st.plotly_chart(
                    variance_chart,
                    use_container_width=True,
                    key="report_variance_chart",
                )

            # Downloads
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


    # =====================================================
    # ASK REPORTOPS TAB
    # =====================================================

    with chat_tab:
        left_spacer, chat_column, right_spacer = st.columns(
            [1, 8, 1]
        )

        with chat_column:
            heading_column, clear_column = st.columns(
                [6, 1]
            )

            with heading_column:
                st.subheader("Ask ReportOps")

            with clear_column:
                if st.button(
                    "Clear chat",
                    use_container_width=True,
                    disabled=not st.session_state.messages,
                ):
                    st.session_state.messages = []
                    st.rerun()

            st.caption(
                f"Chatting about `{source_name}`. "
                "Reporting definitions may also use the "
                "ReportOps Reporting Handbook."
            )

            # Suggested questions only appear before a conversation starts.
            example_prompt = None

            if not st.session_state.messages:
                with st.chat_message("assistant"):
                    st.markdown(
                        "Hi! I can answer questions about this report's "
                        "performance, validation results, and reporting definitions."
                    )

                st.markdown("**Try a question:**")

                question_row_1 = st.columns(2)

                with question_row_1[0]:
                    if st.button(
                        "How did revenue perform against budget?",
                        use_container_width=True,
                    ):
                        example_prompt = (
                            "How did revenue perform against budget?"
                        )

                with question_row_1[1]:
                    if st.button(
                        "What was the latest month-over-month revenue change?",
                        use_container_width=True,
                    ):
                        example_prompt = (
                            "What was the latest month-over-month revenue change?"
                        )

                question_row_2 = st.columns(2)

                with question_row_2[0]:
                    if st.button(
                        "Were any validation issues found?",
                        use_container_width=True,
                    ):
                        example_prompt = (
                            "Were any validation issues found?"
                        )

                with question_row_2[1]:
                    if st.button(
                        "How is operating margin calculated?",
                        use_container_width=True,
                    ):
                        example_prompt = (
                            "How is operating margin calculated?"
                        )

            # Chat conversation
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    display_content = (
                        message.get("content", "")
                        .replace("$", r"\$")
                    )

                    if display_content:
                        st.markdown(display_content)

                    if message.get("tool_used"):
                        tool_label = format_tool_label(
                            message["tool_used"]
                        )

                        st.caption(f"Tool: {tool_label}")

                    if (
                        message.get("source_document")
                        and message.get("source_section")
                    ):
                        source_text = (
                            f"Source: "
                            f"{message['source_document']} — "
                            f"{message['source_section']}"
                        )

                        if message.get("source_page") is not None:
                            source_text += (
                                f" — Page {message['source_page']}"
                            )

                        st.caption(source_text)

            typed_prompt = st.chat_input(
                "Ask a question about the report"
            )

            prompt = example_prompt or typed_prompt

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
                tool_used = result.get("tool_used")

                source_document = None
                source_section = None
                source_page = None

                assistant_response = (
                    result.get("response")
                    or "I could not generate a response."
                )

                if request_type == "define":
                    retrieved_rules = result.get(
                        "retrieved_rules",
                        [],
                    )

                    if retrieved_rules:
                        top_result = retrieved_rules[0]

                        source_document = top_result.get("document")
                        source_section = top_result.get("section")
                        source_page = top_result.get("page")

                with st.chat_message("assistant"):
                    display_response = assistant_response.replace(
                        "$",
                        r"\$",
                    )

                    st.markdown(display_response)

                    if tool_used:
                        tool_label = format_tool_label(tool_used)
                        st.caption(f"Tool: {tool_label}")

                    if source_document and source_section:
                        source_text = (
                            f"Source: {source_document} — "
                            f"{source_section}"
                        )

                        if source_page is not None:
                            source_text += (
                                f" — Page {source_page}"
                            )

                        st.caption(source_text)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "tool_used": tool_used,
                    "source_document": source_document,
                    "source_section": source_section,
                    "source_page": source_page,
                })

                st.rerun()


except FileNotFoundError:
    st.error("The selected file could not be found.")

except pd.errors.EmptyDataError:
    st.error("The selected file is empty.")

except pd.errors.ParserError:
    st.error(
        "The file could not be parsed. "
        "Check that it is a valid CSV file."
    )

except ValueError as error:
    st.error(
        f"The file could not be processed: {error}"
    )

except Exception as error:
    st.error(
        "An unexpected error occurred while processing the file."
    )

    with st.expander("Technical details"):
        st.code(str(error))
