import subprocess
import re
import sys


def analyze_python_file(file_path):

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pylint",
            file_path,
            "--score=y",
        ],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    print("========== PYLINT OUTPUT ==========")
    print(output)
    print("===================================")

    # -------------------------------
    # Extract Overall Score
    # -------------------------------

    score = "0.00"

    score_match = re.search(
        r"rated at (-?\d+\.?\d*)/10",
        output
    )

    if score_match:
        score = score_match.group(1)

    # -------------------------------
    # Count Issues
    # -------------------------------

    issue_matches = re.findall(
        r"\b[CRWEF]\d{4}\b",
        output
    )

    issue_count = len(issue_matches)

    # -------------------------------
    # Parse Every Pylint Issue
    # -------------------------------

    pylint_issues = []

    for line in output.splitlines():

        match = re.search(
            r".+:(\d+):\d+:\s([CRWEF]\d{4}):\s(.+?)\s\((.+?)\)",
            line
        )

        if match:

            code = match.group(2)

            if code.startswith("C"):
                severity = "Convention"

            elif code.startswith("W"):
                severity = "Warning"

            elif code.startswith("E"):
                severity = "Error"

            elif code.startswith("F"):
                severity = "Fatal"

            else:
                severity = "Refactor"

            pylint_issues.append({

                "line": match.group(1),

                "code": code,

                "message": match.group(3),

                "type": match.group(4),

                "severity": severity

            })

    # -------------------------------
    # Recommendations
    # -------------------------------

    recommendations = []

    if "missing-module-docstring" in output:
        recommendations.append(
            "Add module documentation at the top of the file."
        )

    if "missing-function-docstring" in output:
        recommendations.append(
            "Add docstrings to functions."
        )

    if "invalid-name" in output:
        recommendations.append(
            "Use meaningful variable and function names."
        )

    if "unused-import" in output:
        recommendations.append(
            "Remove unused imports."
        )

    if "unused-variable" in output:
        recommendations.append(
            "Remove unused variables."
        )

    if "line-too-long" in output:
        recommendations.append(
            "Keep line length within PEP-8 recommendations."
        )

    if not recommendations:
        recommendations.append(
            "No major code quality issues detected."
        )

    # -------------------------------
    # Quality Status
    # -------------------------------

    try:

        numeric_score = float(score)

        if numeric_score >= 8:
            quality = "Excellent"

        elif numeric_score >= 6:
            quality = "Good"

        elif numeric_score >= 4:
            quality = "Needs Improvement"

        else:
            quality = "Poor"

    except ValueError:

        quality = "Unknown"

    # -------------------------------
    # Return Data
    # -------------------------------

    return {

        "score": score,

        "issues": issue_count,

        "quality": quality,

        "recommendations": recommendations,

        "report": output,

        "pylint_issues": pylint_issues

    }