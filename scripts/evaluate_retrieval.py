from uuid import uuid4

from src.reportops.retrieval import (
    load_handbook_sections,
    load_handbook_fixed_chunks,
    load_pdf_sections,
    load_pdf_fixed_chunks,
    build_reporting_collection,
    retrieve_reporting_rules,
)

HANDBOOK_PATH = "docs/reporting_handbook/reporting_handbook.md"
PDF_PATH = "docs/reporting_handbook/reporting_escalation_policy.pdf"

RETRIEVAL_CASES = [
    ("How is operating margin calculated?", "Operating Margin"),
    ("What does a duplicate record mean?", "Duplicate Records"),
    ("How do I calculate revenue variance to budget?", "Revenue Variance to Budget"),
    ("What chart should I use to compare actual revenue with budget?", "Chart Selection Guidance"),
    ("What happens if revenue is zero when calculating labor expense percentage?", "Labor Expense Percentage"),
    ("How much money did we make compared with what we planned?", "Revenue Variance to Budget"),
    ("How do we measure how much revenue is left after expenses?", "Operating Margin"),
    ("How can I tell what share of revenue is being spent on labor?", "Labor Expense Percentage"),
    ("What should I look at to compare this month with the month before?", "Month-over-Month Revenue Change"),
    ("What's the recommended visualization for showing performance against budget?", "Chart Selection Guidance"),
]

PDF_CASES = [
    (
        "What should we do if a source file comes in after the cutoff?",
        "2. Reporting cutoff and late source files",
    ),
    (
        "If we correct something after the report has already been sent out, what are we supposed to do?",
        "3.1 Corrections after report distribution",
    ),
    (
        "How should we keep track of changes between different versions of a report?",
        "4. Change documentation and version history",
    ),
    (
        "What happens if we keep having the same reconciliation problem?",
        "5. Repeated reconciliation failures",
    ),
    (
        "After we make a correction, do we need to run the report again?",
        "6. Re-running reports after changes",
    ),
    (
        "Who should this go to if the reconciliation issue still isn't resolved?",
        "5.1 Escalation sequence",
    ),
]


def evaluate_handbook_strategy(chunks, strategy_name):
    collection = build_reporting_collection(
        chunks,
        [],
        collection_name=f"evaluation_{strategy_name}_{uuid4().hex[:8]}",
    )

    top_1_correct = 0
    top_3_correct = 0

    print(f"\n{strategy_name} retrieval")
    print("-" * 80)

    for question, expected_text in RETRIEVAL_CASES:
        results = retrieve_reporting_rules(
            question,
            collection,
            n_results=3,
        )

        retrieved_text = " ".join(
            result["text"]
            for result in results
        )

        top_1_text = results[0]["text"]

        top_1_passed = expected_text in top_1_text
        top_3_passed = expected_text in retrieved_text

        if top_1_passed:
            top_1_correct += 1

        if top_3_passed:
            top_3_correct += 1

        retrieved_sections = [
            result["section"]
            for result in results
        ]

        print(
            f"Top-1: {'PASS' if top_1_passed else 'FAIL'} | "
            f"Top-3: {'PASS' if top_3_passed else 'FAIL'} | "
            f"Expected: {expected_text} | "
            f"Retrieved: {retrieved_sections}"
        )

    total = len(RETRIEVAL_CASES)

    print()
    print(
        f"{strategy_name} Top-1 accuracy: "
        f"{top_1_correct}/{total} "
        f"({top_1_correct / total * 100:.1f}%)"
    )
    print(
        f"{strategy_name} Top-3 recall: "
        f"{top_3_correct}/{total} "
        f"({top_3_correct / total * 100:.1f}%)"
    )

    return top_1_correct, top_3_correct, total


def evaluate_pdf_strategy(
    handbook_sections,
    pdf_chunks,
    strategy_name,
):
    collection = build_reporting_collection(
        handbook_sections,
        pdf_chunks,
        collection_name=f"evaluation_pdf_{strategy_name}_{uuid4().hex[:8]}",
    )

    top_1_correct = 0
    top_3_correct = 0

    print(f"\nPDF {strategy_name} retrieval")
    print("-" * 80)

    for question, expected_section in PDF_CASES:
        results = retrieve_reporting_rules(
            question,
            collection,
            n_results=3,
        )

        if strategy_name == "Section-based":
            top_1_passed = results[0]["section"] == expected_section

            top_3_passed = any(
                result["section"] == expected_section
                for result in results
            )

        else:
            top_1_passed = expected_section in results[0]["text"]

            top_3_passed = any(
                expected_section in result["text"]
                for result in results
            )

        if top_1_passed:
            top_1_correct += 1

        if top_3_passed:
            top_3_correct += 1

        retrieved_sections = [
            result["section"]
            for result in results
        ]

        print(
            f"Top-1: {'PASS' if top_1_passed else 'FAIL'} | "
            f"Top-3: {'PASS' if top_3_passed else 'FAIL'} | "
            f"Expected: {expected_section} | "
            f"Retrieved: {retrieved_sections}"
        )

    total = len(PDF_CASES)

    print()
    print(
        f"PDF {strategy_name} Top-1 accuracy: "
        f"{top_1_correct}/{total} "
        f"({top_1_correct / total * 100:.1f}%)"
    )
    print(
        f"PDF {strategy_name} Top-3 recall: "
        f"{top_3_correct}/{total} "
        f"({top_3_correct / total * 100:.1f}%)"
    )

    return top_1_correct, top_3_correct, total


def main():
    section_chunks = load_handbook_sections(HANDBOOK_PATH)
    fixed_chunks = load_handbook_fixed_chunks(HANDBOOK_PATH)
    pdf_sections = load_pdf_sections(PDF_PATH)
    pdf_fixed_chunks = load_pdf_fixed_chunks(PDF_PATH)

    section_top_1, section_top_3, section_total = evaluate_handbook_strategy(
        section_chunks,
        "Section-based",
    )

    fixed_top_1, fixed_top_3, fixed_total = evaluate_handbook_strategy(
        fixed_chunks,
        "Fixed-size",
    )

    pdf_section_top_1, pdf_section_top_3, pdf_total = evaluate_pdf_strategy(
        section_chunks,
        pdf_sections,
        "Section-based",
    )

    pdf_fixed_top_1, pdf_fixed_top_3, _ = evaluate_pdf_strategy(
        section_chunks,
        pdf_fixed_chunks,
        "Fixed-size",
    )

    print("\nEvaluation summary")
    print("=" * 80)

    print(
        f"Section-based Top-1: "
        f"{section_top_1}/{section_total} "
        f"({section_top_1 / section_total * 100:.1f}%)"
    )
    print(
        f"Section-based Top-3: "
        f"{section_top_3}/{section_total} "
        f"({section_top_3 / section_total * 100:.1f}%)"
    )

    print(
        f"Fixed-size Top-1: "
        f"{fixed_top_1}/{fixed_total} "
        f"({fixed_top_1 / fixed_total * 100:.1f}%)"
    )
    print(
        f"Fixed-size Top-3: "
        f"{fixed_top_3}/{fixed_total} "
        f"({fixed_top_3 / fixed_total * 100:.1f}%)"
    )

    print(
        f"PDF section-based Top-1: "
        f"{pdf_section_top_1}/{pdf_total} "
        f"({pdf_section_top_1 / pdf_total * 100:.1f}%)"
    )
    print(
        f"PDF section-based Top-3: "
        f"{pdf_section_top_3}/{pdf_total} "
        f"({pdf_section_top_3 / pdf_total * 100:.1f}%)"
    )

    print(
        f"PDF fixed-size Top-1: "
        f"{pdf_fixed_top_1}/{pdf_total} "
        f"({pdf_fixed_top_1 / pdf_total * 100:.1f}%)"
    )
    print(
        f"PDF fixed-size Top-3: "
        f"{pdf_fixed_top_3}/{pdf_total} "
        f"({pdf_fixed_top_3 / pdf_total * 100:.1f}%)"
    )


if __name__ == "__main__":
    main()