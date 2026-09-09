import pytest

from src.reportops.retrieval import (
    load_handbook_sections,
    load_handbook_fixed_chunks,
    build_reporting_collection,
    retrieve_reporting_rules,
    load_pdf_sections
)

HANDBOOK_PATH = "docs/reporting_handbook/reporting_handbook.md"
PDF_PATH = "docs/reporting_handbook/reporting_escalation_policy.pdf"

RETRIEVAL_CASES = [
    (
        "How is operating margin calculated?",
        "Operating Margin",
    ),
    (
        "What does a duplicate record mean?",
        "Duplicate Records",
    ),
    (
        "How do I calculate revenue variance to budget?",
        "Revenue Variance to Budget",
    ),
    (
        "What chart should I use to compare actual revenue with budget?",
        "Chart Selection Guidance",
    ),
    (
        "What happens if revenue is zero when calculating labor expense percentage?",
        "Labor Expense Percentage",
    ),
]

def test_load_handbook_sections():
    sections = load_handbook_sections(HANDBOOK_PATH)

    section_names = [section["section"] for section in sections]

    assert "Operating Margin" in section_names

@pytest.mark.integration
def test_retrieve_operating_margin():
    sections = load_handbook_sections(HANDBOOK_PATH)
    collection = build_reporting_collection(sections, [])

    results = retrieve_reporting_rules(
        "How is operating margin calculated?",
        collection,
    )

    top_section = results[0]["section"]

    assert top_section == "Operating Margin"

@pytest.mark.integration
def test_retrieve_duplicate_records():
    sections = load_handbook_sections(HANDBOOK_PATH)
    collection = build_reporting_collection(sections, [])

    results = retrieve_reporting_rules(
        "What does a duplicate record mean?",
        collection,
    )

    top_section = results[0]["section"]

    assert top_section == "Validation Rules"

@pytest.mark.integration
def test_fixed_chunk_retrieval_operating_margin():
    chunks = load_handbook_fixed_chunks(HANDBOOK_PATH)
    collection = build_reporting_collection(chunks, [])

    results = retrieve_reporting_rules(
        "How is operating margin calculated?",
        collection,
    )

    top_text = results[0]["text"]

    assert "Operating margin" in top_text

def calculate_retrieval_accuracy(chunks, test_cases):
    collection = build_reporting_collection(chunks, [])

    correct = 0

    for question, expected_section in test_cases:
        results = retrieve_reporting_rules(
            question,
            collection,
            n_results=3,
        )

        retrieved_text = " ".join(
            result["text"]
            for result in results
        )

        if expected_section in retrieved_text:
            correct += 1

    return correct / len(test_cases)

@pytest.mark.integration
def test_compare_chunking_strategies():
    section_chunks = load_handbook_sections(HANDBOOK_PATH)
    fixed_chunks = load_handbook_fixed_chunks(HANDBOOK_PATH)

    section_accuracy = calculate_retrieval_accuracy(
        section_chunks,
        RETRIEVAL_CASES,
    )

    fixed_accuracy = calculate_retrieval_accuracy(
        fixed_chunks,
        RETRIEVAL_CASES,
    )

    print(f"Section-based accuracy: {section_accuracy:.0%}")
    print(f"Fixed-size accuracy: {fixed_accuracy:.0%}")

    assert section_accuracy >= 0.8

def test_load_pdf_sections_returns_sections_with_pages():
    sections = load_pdf_sections(PDF_PATH)

    assert len(sections) > 0
    assert "section" in sections[0]
    assert "text" in sections[0]
    assert "page" in sections[0]

@pytest.mark.integration
def test_retrieve_pdf_policy():
    handbook_sections = load_handbook_sections(HANDBOOK_PATH)
    pdf_sections = load_pdf_sections(PDF_PATH)

    collection = build_reporting_collection(
        handbook_sections,
        pdf_sections,
    )

    results = retrieve_reporting_rules(
        "What should happen if a source file arrives after the reporting cutoff?",
        collection,
    )

    top_result = results[0]

    assert top_result["document"] == "ReportOps Reporting Escalation Policy"
    assert top_result["source_type"] == "pdf"
    assert top_result["section"] == "2. Reporting cutoff and late source files"
    assert "page" in top_result