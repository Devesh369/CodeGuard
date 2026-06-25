import subprocess
import json
import sys


def analyze_security(file_path):

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "bandit",
                "-f",
                "json",
                file_path
            ],
            capture_output=True,
            text=True
        )

        if not result.stdout.strip():

            return {
                "issue_count": 0,
                "issues": []
            }

        data = json.loads(result.stdout)

        findings = []

        for issue in data.get("results", []):

            findings.append({

                "severity": issue.get("issue_severity"),

                "confidence": issue.get("issue_confidence"),

                "line": issue.get("line_number"),

                "test": issue.get("test_name"),

                "text": issue.get("issue_text"),

                "cwe": (
                    issue["issue_cwe"]["id"]
                    if issue.get("issue_cwe")
                    else ""
                ),

                "more_info": issue.get("more_info"),
            })

        return {
            "issue_count": len(findings),
            "issues": findings,
        }

    except Exception as e:

        print("Bandit Error:", e)

        return {
            "issue_count": 0,
            "issues": [],
        }