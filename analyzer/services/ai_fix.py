import os
import json
import re

from groq import Groq


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def _normalize_issue_text(text):
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", str(text)).strip().lower()
    return cleaned


def summarize_ai_changes(changes):
    if not changes:
        return []

    grouped = {}
    for change in changes:
        issue = str(change.get("issue", "")).strip()
        if not issue:
            continue

        normalized = _normalize_issue_text(issue)
        if normalized in {"trailing whitespace", "whitespace", "extra whitespace", "blank line", "blank lines"}:
            continue

        entry = grouped.setdefault(normalized, {
            "issue": issue,
            "count": 0,
            "lines": [],
            "reason": change.get("reason") or "",
        })
        entry["count"] += 1
        line = change.get("line")
        if line is not None:
            entry["lines"].append(int(line))

    result = []
    for key, entry in grouped.items():
        if entry["count"] <= 0:
            continue
        result.append({
            "issue": entry["issue"],
            "count": entry["count"],
            "lines": entry["lines"],
            "reason": entry["reason"],
        })

    return sorted(result, key=lambda item: (-item["count"], item["issue"].lower()))


def summarize_ai_suggestions(suggestions):
    if not suggestions:
        return []

    grouped = {}
    for suggestion in suggestions:
        text = str(suggestion).strip()
        if not text:
            continue

        normalized = _normalize_issue_text(text)
        if normalized in {"trailing whitespace", "whitespace", "extra whitespace", "blank line", "blank lines"}:
            continue

        entry = grouped.setdefault(normalized, {"text": text, "count": 0})
        entry["count"] += 1

    result = []
    for normalized, entry in grouped.items():
        if entry["count"] <= 0:
            continue
        label = entry["text"] if entry["count"] == 1 else f"{entry['text']} ({entry['count']} times)"
        result.append(label)

    return sorted(result, key=lambda item: (item.count("(") == 0, item.lower()))


def generate_ai_fix(source_code, pylint_report, security_report):

    prompt = f"""
You are a Senior Python Software Engineer.

Your job is to REVIEW the Python code.

DO NOT rewrite the whole program.

DO NOT create a new implementation.

DO NOT add unnecessary imports.

DO NOT change working code.

ONLY suggest fixes for the reported issues.

For every issue provide:

1. line number
2. issue
3. current code
4. suggested replacement
5. reason

If no change is required return an empty list.

Return ONLY valid JSON.

Do NOT use markdown.

Do NOT use ```.

Return EXACTLY this JSON:

{{
    "changes":[
        {{
            "line":15,
            "issue":"Missing docstring",
            "old":"class UploadForm(forms.ModelForm):",
            "new":"class UploadForm(forms.ModelForm):\\n    \\"\\"\\"Upload form.\\"\\"\\"",
            "reason":"Adds documentation."
        }}
    ],

    "explanation":"Brief summary of the suggested improvements."
}}

=========================
SOURCE CODE
=========================

{source_code}

=========================
PYLINT REPORT
=========================

{pylint_report}

=========================
BANDIT REPORT
=========================

{security_report}

"""

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            temperature=0.2,

            response_format={"type": "json_object"},

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        print("=" * 80)
        print("AI FIX RESPONSE")
        print(response.choices[0].message.content)
        print("=" * 80)

        result = json.loads(
            response.choices[0].message.content
        )

        changes = result.get("changes", [])
        summary_changes = summarize_ai_changes(changes)

        return {

            "changes": changes,
            "summary_changes": summary_changes,
            "fixed_code": result.get("fixed_code", ""),
            "explanation": result.get(
                "explanation",
                ""
            )

        }

    except Exception as e:

        import traceback

        print("=" * 80)
        print("AI FIX ERROR")
        print(e)
        traceback.print_exc()
        print("=" * 80)

        return {

            "changes": [],
            "summary_changes": [],
            "fixed_code": "",
            "explanation": "AI Fix unavailable."

        }