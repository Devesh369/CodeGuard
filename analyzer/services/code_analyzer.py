import subprocess
import re
import sys


def analyze_python_file(file_path):

    try:

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

        # Extract score
        score = "0.00"

        score_match = re.search(
            r"rated at (-?\d+\.?\d*)/10",
            output
        
        )
        print("========== PYLINT OUTPUT ==========")
        print(output)
        print("===================================")


        if score_match:
            score = score_match.group(1)

        # Count pylint issues
        issue_matches = re.findall(
            r"\b[CRWEF]\d{4}\b",
            output
        )

        issue_count = len(issue_matches)

        # Recommendations
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
                "Keep line length within PEP8 recommendations."
            )

        if not recommendations:
            recommendations.append(
                "No major code quality issues detected."
            )

        # Quality Status
        print("========== PYLINT OUTPUT ==========")
        print(output)
        print("===================================")
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
            
            
    
        return {
            "score": score,
            "issues": issue_count,
            "quality": quality,
            "recommendations": recommendations,
            "report": output,
        }

    except Exception as e:
        
        

        return {
            "score": "0.00",
            "issues": 0,
            "quality": "Error",
            "recommendations": [
                f"Analyzer Error: {str(e)}"
            ],
            "report": str(e),
        }
        
