"""Check that every test reached the verdict its folder names, and report the run.

Usage: ``python scripts/check_verdicts.py <results folder>``
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# The folder a test sits in under tests/ is the verdict Tailoop must reach.
EXPECTED = {"pass": "passed", "fail": "failed", "inconclusive": "inconclusive"}


def check(tests: list[dict], version: str) -> tuple[str, int]:
    """Compare each test's verdict with the one its folder expects.

    Args:
        tests: The ``tests`` list from Tailoop's ``suite_summary.json``.
        version: The Tailoop build that ran, for the report's heading.

    Returns:
        A Markdown report, and how many verdicts were not the expected one.

    Example:
        report, wrong = check(summary["tests"], "latest")
    """
    rows = []
    wrong = 0
    for test in tests:
        folder = test["test_name"].split("/")[0]
        expected = EXPECTED.get(folder, f"(unknown folder '{folder}')")
        matched = test["status"] == expected
        wrong += not matched
        cost = test.get("cost_usd")
        cost_text = "n/a" if cost is None else f"${cost:.4f}"
        reason = (test.get("message") or "").replace("|", "\\|")
        rows.append(
            f"| {'ok' if matched else '**wrong**'} | `{test['test_name']}` | {expected} "
            f"| {test['status']} | {test['duration_seconds']:.0f}s | {cost_text} "
            f"| {reason} |"
        )
    total = sum(test.get("cost_usd") or 0 for test in tests)
    report = [
        f"## Tailoop {version}: {len(tests) - wrong} of {len(tests)} verdicts"
        " as expected",
        "",
        "| Result | Test | Expected | Verdict | Time | Cost | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
        f"Total cost: ${total:.4f}",
    ]
    return "\n".join(report), wrong


def main() -> None:
    """Read the run's summary, print the report, and fail on any wrong verdict."""
    results = Path(sys.argv[1])
    summaries = sorted(results.rglob("suite_summary.json"))
    if not summaries:
        sys.exit(f"No suite_summary.json under {results}: the run did not finish.")
    tests = json.loads(summaries[-1].read_text(encoding="utf-8"))["tests"]
    if not tests:
        sys.exit("The run finished without any tests.")

    report, wrong = check(tests, os.environ.get("TAILOOP_VERSION", "latest"))
    print(report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(report + "\n")
    if wrong:
        sys.exit(f"{wrong} verdict(s) were not the expected one.")


if __name__ == "__main__":
    main()
