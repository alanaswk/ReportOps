# ReportOps

ReportOps is an agentic reporting and data-quality copilot for recurring spreadsheet workflows. It validates uploaded operational data, calculates KPIs with deterministic Python functions, creates interactive visualizations, and answers questions using analysis tools and cited reporting guidance. The project combines reliable data processing with a lightweight LangGraph workflow and a RAG pipeline.

## Live demo

ReportOps is deployed publicly with Streamlit Community Cloud.

**Live application:** [Open ReportOps](https://reportops-alanaswk.streamlit.app/)

## Why this project

Recurring business reports often begin with spreadsheets that contain missing fields, duplicated records, invalid values, or inconsistent totals. Finding these problems manually is slow, and asking an LLM to perform calculations directly can produce unreliable results.

ReportOps separates those responsibilities: deterministic Python functions handle validation and arithmetic, while the LLM interprets verified results, classifies natural-language requests, and generates grounded explanations from calculated results or retrieved reporting guidance.

## Core capabilities

ReportOps:

* Loads included demo data or user-uploaded CSV and Excel files.
* Detects five classes of data-quality issues.
* Calculates four operational KPIs using deterministic Python functions.
* Displays three interactive Plotly charts.
* Generates a structured executive summary from validated facts.
* Routes natural-language questions to analysis, validation, or retrieval tools through LangGraph.
* Retrieves KPI definitions, reporting rules, and escalation guidance from Markdown and PDF knowledge sources with citations.
* Runs as a publicly deployed Streamlit application.
* Includes automated evaluation for validation accuracy, KPI correctness, request routing, retrieval quality, and response grounding.

## Application workflow

The Streamlit application is organized into three primary sections:

### Data Quality

Reviews the selected dataset for predefined validation issues and displays the underlying data for inspection.

### Report

Displays deterministic KPI calculations, a grounded executive summary, supporting findings and evidence, interactive Plotly charts, and downloadable results.

### Ask ReportOps

Allows users to ask natural-language questions about calculated performance, validation issues, KPI definitions, and reporting guidance. LangGraph classifies each request and routes it to the appropriate tool before generating a grounded response.

## Demo dataset

The synthetic dataset represents 15 locations across several regions and 12 monthly periods.

| Field            | Description                                    |
| ---------------- | ---------------------------------------------- |
| `location_id`    | Stable synthetic location identifier           |
| `location_name`  | Synthetic location name                        |
| `region`         | Region used for grouped reporting              |
| `month`          | Reporting period                               |
| `revenue`        | Actual revenue                                 |
| `budget_revenue` | Budgeted revenue                               |
| `labor_expense`  | Actual labor expense                           |
| `other_expense`  | Other operating expense                        |
| `total_expense`  | Reported total used for expense reconciliation |
| `volume`         | Synthetic operational volume                   |

The generator creates one clean operations dataset and five corrupted variants with known expected errors. A fixed random seed makes every run reproducible.

## Validation rules

1. **Required columns:** detect missing fields needed for reporting.
2. **Duplicate records:** detect repeated `location_id` and `month` combinations.
3. **Missing values:** detect blank required identifiers or numeric values.
4. **Impossible values:** detect values such as negative volume or invalid dates.
5. **Reconciliation:** when a total-expense field is supplied, detect rows where its components do not add to the reported total.

Validation issues are represented with structured Pydantic models containing the issue type, severity, source, explanation, and suggested action.

## KPI definitions

| KPI                             | Calculation                                                        |
| ------------------------------- | ------------------------------------------------------------------ |
| Revenue variance to budget      | `revenue - budget_revenue`, reported as both amount and percentage |
| Month-over-month revenue change | Change in revenue from the prior reporting month                   |
| Operating margin                | `(revenue - labor_expense - other_expense) / revenue`              |
| Labor expense percentage        | `labor_expense / revenue`                                          |

## LangGraph request workflow

The LangGraph workflow stays intentionally small. ReportOps uses tool routing rather than multiple autonomous agents.

A classifier first identifies the user's request type and routes the request to one of three paths.

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

| Route       | Example request                                                   | Primary capability                         |
| ----------- | ----------------------------------------------------------------- | ------------------------------------------ |
| Analyze     | How is revenue performing against budget?                         | Use deterministic calculated metrics       |
| Investigate | Why was this row flagged?                                         | Explain structured validation results      |
| Define      | What happens if a source file arrives after the reporting cutoff? | Retrieve cited handbook or policy guidance |

The LLM does not perform KPI arithmetic. Calculations are completed before response generation and passed to the model as trusted facts.

## RAG pipeline

ReportOps uses retrieval-augmented generation for reporting definitions, rules, and escalation guidance. Numeric spreadsheet rows are not embedded or retrieved through RAG.

The knowledge base currently contains two document types:

* A Markdown reporting handbook containing KPI definitions, validation rules, and reporting guidance.
* A PDF reporting escalation policy containing escalation and reporting-procedure guidance.

The retrieval pipeline:

1. Loads content from Markdown and PDF sources.
2. Extracts structured sections and source metadata.
3. Creates Gemini embeddings.
4. Stores document chunks in ChromaDB.
5. Retrieves the most relevant chunks for a user's question.
6. Passes retrieved guidance to the response-generation step.
7. Returns source information with the grounded answer.

PDF ingestion preserves source and page metadata so retrieved guidance can be traced back to the originating document.

## Retrieval chunking experiment

ReportOps compares structure-aware section chunking with fixed-size character chunking across both Markdown and PDF knowledge sources.

| Source               | Section-based Top-1 | Section-based Top-3 | Fixed-size Top-1 | Fixed-size Top-3 |
| -------------------- | ------------------: | ------------------: | ---------------: | ---------------: |
| Markdown handbook    |        10/10 (100%) |        10/10 (100%) |       5/10 (50%) |     10/10 (100%) |
| PDF reporting policy |         5/6 (83.3%) |          6/6 (100%) |      1/6 (16.7%) |       6/6 (100%) |

Section-based chunking produced substantially better Top-1 retrieval accuracy than fixed-size character chunking.

Both approaches achieved 100% Top-3 recall on the tested questions, suggesting that fixed-size chunking often retrieved the relevant information but ranked it less effectively.

Based on these results, ReportOps uses structure-aware section chunking for its production retrieval pipeline.

## Structured executive summary

ReportOps can generate an executive summary using Gemini, but the model receives only validated inputs and already-calculated metrics.

Structured output includes:

* Major findings
* Concerns
* Executive summary

Each supported claim includes evidence tied to provided metrics or validation results.

If the LLM is unavailable or the request fails, ReportOps falls back to a deterministic template-based summary so the core reporting workflow remains usable.

## Technology

* **Python** for application logic
* **Pandas** for ingestion, normalization, validation, and KPI calculations
* **Pydantic** for structured validation issues and model responses
* **Plotly** for interactive reporting visualizations
* **Streamlit** for the user interface and public deployment
* **LangGraph** for lightweight request classification and tool routing
* **Gemini** for structured summaries, request classification, grounded responses, and embeddings
* **ChromaDB** for multi-document vector retrieval
* **pypdf** for PDF text extraction and page-level source metadata
* **Pytest** for validation, KPI, routing, workflow, retrieval, and evaluation tests

## Repository structure

```text
ReportOps/
├── app.py
├── src/
│   └── reportops/
│       ├── __init__.py
│       ├── charts.py
│       ├── graph.py
│       ├── ingestion.py
│       ├── metrics.py
│       ├── model_client.py
│       ├── models.py
│       ├── reporting.py
│       ├── retrieval.py
│       ├── summary.py
│       ├── tools.py
│       └── validation.py
├── data/
│   └── demo/
├── docs/
│   └── reporting_handbook/
│       ├── reporting_handbook.md
│       └── reporting_escalation_policy.pdf
├── scripts/
│   └── generate_demo_data.py
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Local setup

Python 3.11 or later is recommended.

Clone the repository:

```bash
git clone https://github.com/alanaswk/ReportOps.git
cd ReportOps
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set:

```text
GEMINI_API_KEY=your_api_key_here
```

The Gemini API key enables structured summaries, request classification, grounded chat responses, and embeddings.

## Running the project

Regenerate the reproducible demo files with:

```bash
python scripts/generate_demo_data.py
```

Run the Streamlit application locally with:

```bash
streamlit run app.py
```

Run the full test suite with:

```bash
python -m pytest -q
```

## Evaluation results

ReportOps was evaluated on validation accuracy, deterministic KPI calculations, request routing, retrieval quality, and response grounding.

The evaluation set is intentionally small and targeted to the supported MVP workflows.

| Evaluation              | Result                                            |
| ----------------------- | ------------------------------------------------- |
| Single-error validation | 5/5 corrupted files correctly identified          |
| Clean-file validation   | 0 validation issues detected                      |
| Multi-error validation  | 4/4 seeded issue types detected together          |
| KPI correctness         | 4/4 manually verified calculations matched        |
| Request routing         | 20/20 representative prompts correctly classified |
| Grounding review        | 3/3 sampled responses supported by tool output    |

These results are produced from reproducible test cases included in the repository rather than estimated performance claims.

## Architecture

```text
                    ┌───────────────────────┐
                    │   Streamlit Interface │
                    └───────────┬───────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             v                  v                  v
      Data Quality           Report          Ask ReportOps
             │                  │                  │
             v                  v                  v
       Validation          Metrics +         LangGraph
          Tools              Charts          Classifier
             │                  │                  │
             │                  │        ┌─────────┼─────────┐
             │                  │        │         │         │
             │                  │        v         v         v
             │                  │     Analyze  Investigate  Define
             │                  │        │         │         │
             │                  │        │         │         v
             │                  │        │         │       RAG
             │                  │        │         │         │
             │                  │        └─────────┴─────────┘
             │                  │                  │
             └──────────────────┴──────────────────┘
                                │
                                v
                     Grounded LLM Response
```

The system separates deterministic processing from generative reasoning. Validation and KPI calculations are performed by Python functions, while the LLM is used for classification, interpretation, summarization, and grounded response generation.

## Scope and limitations

ReportOps is a focused portfolio project, not a production enterprise platform.

Future improvements could include broader document support, more flexible uploaded-data schemas, and additional reporting metrics.
