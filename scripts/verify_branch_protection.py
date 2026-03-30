from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


GRAPHQL_QUERY = """
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    branchProtectionRules(first: 100) {
      nodes {
        pattern
        isAdminEnforced
        requiresApprovingReviews
        requiredApprovingReviewCount
        requiresStatusChecks
        requiresStrictStatusChecks
        requiredStatusCheckContexts
        requiresConversationResolution
        allowsForcePushes
        allowsDeletions
      }
    }
  }
}
"""


@dataclass(frozen=True)
class ExpectedPolicy:
    required_contexts: tuple[str, ...] = ("tests",)
    requires_status_checks: bool = True
    requires_strict_status_checks: bool = True
    requires_approving_reviews: bool = True
    required_approving_review_count: int = 1
    requires_conversation_resolution: bool = True
    is_admin_enforced: bool = False
    allows_force_pushes: bool = False
    allows_deletions: bool = False


def _append_summary(lines: list[str]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _fetch_branch_rule(owner: str, repo: str, branch_pattern: str = "main") -> dict[str, object]:
    cmd = [
        "gh",
        "api",
        "graphql",
        "-f",
        f"owner={owner}",
        "-f",
        f"repo={repo}",
        "-f",
        f"query={GRAPHQL_QUERY}",
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    payload = json.loads(proc.stdout)
    rules = payload["data"]["repository"]["branchProtectionRules"]["nodes"]
    for rule in rules:
        if rule.get("pattern") == branch_pattern:
            return rule
    raise RuntimeError(f"Branch protection rule with pattern '{branch_pattern}' not found.")


def _validate(rule: dict[str, object], expected: ExpectedPolicy) -> list[str]:
    issues: list[str] = []
    actual_contexts = sorted(rule.get("requiredStatusCheckContexts") or [])

    missing_contexts = sorted(set(expected.required_contexts) - set(actual_contexts))
    if missing_contexts:
        issues.append(
            f"Missing required status checks: expected {list(expected.required_contexts)}, actual {actual_contexts}"
        )

    checks = [
        ("requiresStatusChecks", expected.requires_status_checks),
        ("requiresStrictStatusChecks", expected.requires_strict_status_checks),
        ("requiresApprovingReviews", expected.requires_approving_reviews),
        ("requiredApprovingReviewCount", expected.required_approving_review_count),
        ("requiresConversationResolution", expected.requires_conversation_resolution),
        ("isAdminEnforced", expected.is_admin_enforced),
        ("allowsForcePushes", expected.allows_force_pushes),
        ("allowsDeletions", expected.allows_deletions),
    ]

    for key, expected_value in checks:
        actual_value = rule.get(key)
        if actual_value != expected_value:
            issues.append(f"{key} drift: expected {expected_value!r}, actual {actual_value!r}")

    return issues


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo or "/" not in repo:
        print("GITHUB_REPOSITORY is required (owner/repo).", file=sys.stderr)
        return 2
    owner, name = repo.split("/", 1)

    expected = ExpectedPolicy()
    try:
        rule = _fetch_branch_rule(owner, name, branch_pattern="main")
    except Exception as exc:
        print(f"Unable to fetch branch protection rule: {exc}", file=sys.stderr)
        _append_summary(
            [
                "### Branch Protection Conformance",
                "- status: failed",
                f"- error: {exc}",
            ]
        )
        return 1

    issues = _validate(rule, expected)
    if issues:
        print("Branch protection drift detected:")
        for item in issues:
            print(f"- {item}")
        _append_summary(
            [
                "### Branch Protection Conformance",
                "- status: failed",
                "- details:",
                *[f"  - {item}" for item in issues],
            ]
        )
        return 1

    actual_contexts = sorted(rule.get("requiredStatusCheckContexts") or [])
    print("Branch protection matches expected policy.")
    print(f"- requiredStatusCheckContexts: {actual_contexts}")
    _append_summary(
        [
            "### Branch Protection Conformance",
            "- status: pass",
            f"- required checks: {actual_contexts}",
            f"- approving reviews: {rule.get('requiredApprovingReviewCount')}",
            f"- conversation resolution: {rule.get('requiresConversationResolution')}",
            f"- admin enforced: {rule.get('isAdminEnforced')}",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
