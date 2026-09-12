import time

from src.reportops.graph import classify_request


ROUTING_CASES = [
    # Analyze
    {
        "prompt": "What's our overall operating margin?",
        "expected_route": "analyze",
    },
    {
        "prompt": "How did revenue change compared with last month?",
        "expected_route": "analyze",
    },
    {
        "prompt": "Are we running above or below budget?",
        "expected_route": "analyze",
    },
    {
        "prompt": "How much of our revenue is going toward labor?",
        "expected_route": "analyze",
    },
    {
        "prompt": "How are we doing against budget overall?",
        "expected_route": "analyze",
    },
    {
        "prompt": "Did revenue get better or worse this month?",
        "expected_route": "analyze",
    },
    {
        "prompt": "What stands out in the revenue, expenses, and margin numbers?",
        "expected_route": "analyze",
    },

    # Investigate
    {
        "prompt": "Why did this row get flagged as a duplicate?",
        "expected_route": "investigate",
    },
    {
        "prompt": "Are we missing any data in this file?",
        "expected_route": "investigate",
    },
    {
        "prompt": "Why am I getting a reconciliation error?",
        "expected_route": "investigate",
    },
    {
        "prompt": "Is there anything wrong with the data I uploaded?",
        "expected_route": "investigate",
    },
    {
        "prompt": "Why is this record showing up as invalid?",
        "expected_route": "investigate",
    },
    {
        "prompt": "Did you find any problems with this report?",
        "expected_route": "investigate",
    },

    # Define
    {
        "prompt": "How do we calculate operating margin?",
        "expected_route": "define",
    },
    {
        "prompt": "What exactly counts as a duplicate record?",
        "expected_route": "define",
    },
    {
        "prompt": "When are we supposed to escalate an issue?",
        "expected_route": "define",
    },
    {
        "prompt": "What's the rule if revenue is missing?",
        "expected_route": "define",
    },
    {
        "prompt": "Why do we calculate operating margin that way?",
        "expected_route": "define",
    },
    {
        "prompt": "What are we supposed to do if a file comes in late?",
        "expected_route": "define",
    },
    {
        "prompt": "Which kind of chart should I use for this report?",
        "expected_route": "define",
    },
]


def get_route_value(route):
    if hasattr(route, "value"):
        return route.value

    return route


def main():
    correct = 0

    for case in ROUTING_CASES:
        result = classify_request(
            {
                "user_request": case["prompt"],
            }
        )

        actual_route = get_route_value(result["request_type"])
        expected_route = case["expected_route"]

        passed = actual_route == expected_route

        if passed:
            correct += 1

        print(
            f"{'PASS' if passed else 'FAIL'} | "
            f"Expected: {expected_route:<11} | "
            f"Actual: {actual_route:<11} | "
            f"{case['prompt']}"
        )

        time.sleep(5)

    total = len(ROUTING_CASES)
    accuracy = correct / total * 100

    print()
    print(f"Routing accuracy: {correct}/{total} ({accuracy:.1f}%)")


if __name__ == "__main__":
    main()