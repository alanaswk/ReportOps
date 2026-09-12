# ReportOps

ReportOps is an agentic reporting and data-quality copilot for recurring spreadsheet workflows. It validates uploaded operational data, calculates KPIs with deterministic Python functions, creates interactive visualizations, and answers questions using analysis tools and cited reporting guidance. The project combines reliable data processing with a small LangGraph workflow and a focused RAG pipeline.

## Why this project

Recurring business reports often begin with spreadsheets that contain missing fields, duplicated records, invalid values, or inconsistent totals. Finding these problems manually is slow, and asking an LLM to perform calculations directly can produce unreliable results.

ReportOps separates those responsibilities: Python handles validation and arithmetic, while the LLM interprets verified results, routes natural-language requests, and explains reporting rules. The demo uses fully synthetic multi-location operations data and does not contain confidential or real company information.

## Planned MVP

The first release will:

- Load included demo data or user-uploaded CSV and Excel files.
- Detect five classes of data-quality issues.
- Calculate four operational KPIs using deterministic functions.
- Display three interactive Plotly charts.
- Generate a structured executive summary from validated facts.
- Route natural-language questions to analysis, visualization, validation, or retrieval tools.
- Retrieve KPI definitions and reporting rules from a small knowledge base with citations.
- Run as a public Streamlit application.

## Demo dataset

The synthetic dataset represents 15 locations across several regions and 12 monthly periods.

| Field | Description |
| --- | --- |
| `location_id` | Stable synthetic location identifier |
| `location_name` | Synthetic location name |
| `region` | Region used for grouped reporting |
| `month` | Reporting period |
| `revenue` | Actual revenue |
| `budget_revenue` | Budgeted revenue |
| `labor_expense` | Actual labor expense |
| `other_expense` | Other operating expense |
| `total_expense` | Reported total used for expense reconciliation |
| `volume` | Synthetic operational volume |

The generator creates one clean operations dataset and five corrupted variants with known expected errors. A fixed random seed makes every run reproducible.

## Validation rules

1. **Required columns:** detect missing fields needed for reporting.
2. **Duplicate records:** detect repeated `location_id` and `month` combinations.
3. **Missing values:** detect blank required identifiers or numeric values.
4. **Impossible values:** detect values such as negative volume or invalid dates.
5. **Reconciliation:** when a total-expense field is supplied, detect rows where its components do not add to the total.

## KPI definitions

| KPI | Calculation |
| --- | --- |
| Revenue variance to budget | `revenue - budget_revenue`, reported as both amount and percentage |
| Month-over-month revenue change | Change in revenue from the prior reporting month |
| Operating margin | `(revenue - labor_expense - other_expense) / revenue` |
| Labor expense percentage | `labor_expense / revenue` |

Division-by-zero and missing-input behavior will be handled explicitly and covered by tests.

### LangGraph request workflow

The graph stays intentionally small: one classifier chooses the appropriate tool path, and only analysis, investigation, and retrieval routes require conversational response generation.

```text
User request
    |
    v
Classify request
    |
    +----------------+----------------+
    |                |                |
    v                v                v
Analyze          Investigate        Define
    |                |                |
    v                v                v
Calculated       Validation      Reporting guidance
metrics           results          from RAG
    |                |                |
    +----------------+----------------+
                     |
                     v
          Generate grounded response
                     |
                     v
            Return to Streamlit
```

| Route | Example request | Primary capability |
| --- | --- | --- |
| Analyze | What is the operating margin? | Use deterministic calculated metrics |
| Investigate | Why was this row flagged? | Explain validation results |
| Define | What happens if a source file arrives after the reporting cutoff? | Retrieve cited handbook or policy guidance |

## Technology

- Python and Pandas for ingestion, validation, and KPI calculations
- Pydantic for structured validation issues and model responses
- Plotly and Streamlit for the interactive application
- LangGraph for lightweight request classification and tool routing
- Gemini for structured summaries, request classification, grounded responses, and embeddings
- ChromaDB for multi-document vector retrieval
- pypdf for PDF text extraction and page metadata
- Pytest for unit, workflow, and retrieval tests

## Repository structure

```text
ReportOps/
├── app.py
├── src/reportops/
│   ├── __init__.py
│   ├── charts.py
│   ├── graph.py
│   ├── ingestion.py
│   ├── metrics.py
│   ├── model_client.py
│   ├── models.py
│   ├── reporting.py
│   ├── retrieval.py
│   ├── summary.py
│   ├── tools.py
│   └── validation.py
├── data/demo/
├── scripts/generate_demo_data.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

This is the target structure; modules will be added as each milestone is implemented.

## Local setup

Python 3.11 is recommended.

```bash
git clone <your-repository-url>
cd reportops

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` to enable Gemini summaries and request classification.

## Running the project

Regenerate the reproducible demo files with:

```bash
python scripts/generate_demo_data.py
```

Run the Streamlit application locally with:

```bash
streamlit run app.py
```

Run the test suite with:

```bash
python -m pytest -q
```

## Development plan

- [X] Day 1: Repository setup and reproducible synthetic data
- [X] Day 2: Ingestion, validation models, and validation tests
- [X] Day 3: KPI calculations, charts, and fallback summary
- [X] Day 4: Initial Streamlit application and early deployment
- [X] Day 5: Structured Gemini summary grounded in calculated facts
- [X] Day 6: LangGraph request routing
- [X] Day 7: Reporting handbook and evaluated RAG pipeline
- [X] Day 8: Chat integration
- [ ] Day 9: Validation, metric, routing, retrieval, and grounding evaluation
- [ ] Day 10: Documentation, screenshots, demo video, and portfolio polish

## Evaluation results

ReportOps was evaluated on validation accuracy, deterministic KPI calculations, request routing, retrieval quality, and response grounding. The evaluation set is intentionally small and targeted to the supported MVP workflows.

| Evaluation | Result |
| --- | --- |
| Single-error validation | 5/5 corrupted files correctly identified |
| Clean-file validation | 0 validation issues detected |
| Multi-error validation | 4/4 seeded issue types detected together |
| KPI correctness | 4/4 manually verified calculations matched |
| Request routing | 20/20 representative prompts correctly classified |
| Markdown section-based retrieval | 10/10 Top-1, 10/10 Top-3 |
| Markdown fixed-size retrieval | 5/10 Top-1, 10/10 Top-3 |
| PDF section-based retrieval | 5/6 Top-1, 6/6 Top-3 |
| PDF fixed-size retrieval | 1/6 Top-1, 6/6 Top-3 |
| Grounding review | 3/3 sampled responses supported by tool output |

### Retrieval experiment

Two chunking strategies were compared across both the Markdown reporting handbook and the PDF reporting policy.

Section-based chunking produced substantially better Top-1 retrieval accuracy than fixed-size character chunking. On the Markdown evaluation set, section-based chunks achieved 100% Top-1 accuracy compared with 50% for fixed-size chunks. On the PDF evaluation set, section-based chunks achieved 83.3% Top-1 accuracy compared with 16.7% for fixed-size chunks.

Both strategies achieved 100% Top-3 recall on the tested questions, suggesting that fixed-size chunking often retrieved the relevant information but ranked it less effectively. Based on these results, ReportOps uses structure-aware section chunking for its production retrieval pipeline.

## Scope and limitations

The MVP intentionally excludes autonomous data correction, multiple collaborating agents, forecasting, authentication, databases, a separate API backend, and elaborate cloud infrastructure. These may be considered later only if they make the deployed demo clearer, more reliable, or more useful.