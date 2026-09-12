from src.reportops.graph import report_graph
from src.reportops.ingestion import load_data


CASES = [
    {
        "prompt": "What is the overall operating margin?",
        "file": "data/demo/clean_operations_data.csv",
    },
    {
        "prompt": "Why was this row flagged as a duplicate?",
        "file": "data/demo/corrupted_duplicate_record.csv",
    },
    {
        "prompt": "How is operating margin calculated?",
        "file": "data/demo/clean_operations_data.csv",
    },
]


def main():
    for index, case in enumerate(CASES, start=1):
        df = load_data(case["file"])

        result = report_graph.invoke(
            {
                "user_request": case["prompt"],
                "df": df,
                "source": case["file"],
            }
        )

        print()
        print("=" * 80)
        print(f"CASE {index}")
        print("=" * 80)

        print(f"Prompt: {case['prompt']}")
        print(f"Route: {result['request_type']}")
        print(f"Tool: {result['tool_used']}")

        if "calculated_metrics" in result:
            print("\nSUPPLIED METRICS:")
            print(result["calculated_metrics"])

        if "validation_issues" in result:
            print("\nSUPPLIED VALIDATION ISSUES:")
            print(result["validation_issues"])

        if "retrieved_rules" in result:
            print("\nSUPPLIED RETRIEVED RULES:")
            print(result["retrieved_rules"])

        print("\nGENERATED RESPONSE:")
        print(result["response"])


if __name__ == "__main__":
    main()