import json
import re
from groq import Groq

from django.conf import settings


client = Groq(
    api_key=settings.GROQ_API_KEY
)


def generate_ai_review(code, pylint_report, security_report):

    try:
            prompt = f"""
        You are a Senior Python Code Reviewer.

        Analyze the Python code.

        Return ONLY valid JSON.

        Do not write markdown.

        Do not write explanations.

        Do not wrap JSON inside ```.

        Return EXACTLY this structure:

        {{
            "overall_score":8,
            "summary":"...",
            "strengths":["..."],
            "weaknesses":["..."],
            "suggestions":["...","...","..."],
            "security":"Unknown",
            "maintainability":7,
            "readability":8

        }}
        ==============================
        SOURCE CODE
        ==============================

        {code}

        ==============================
        PYLINT REPORT
        ==============================

        {pylint_report}

        ==============================
        SECURITY REPORT
        ==============================

        {security_report}
        """

            response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            temperature=0.2,

            response_format={"type": "json_object"},

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
            print("=" * 80)
            print(response)
            print("=" * 80)
            answer = response.choices[0].message.content

        # Remove markdown code fences if present
            answer = re.sub(r"^```json", "", answer)
            answer = re.sub(r"^```", "", answer)
            answer = re.sub(r"```$", "", answer)
            answer = answer.strip()

            
            return json.loads(answer)

    except Exception as e:
        print(e)

        return {
            "overall_score": 0,
            "summary": "AI Review Failed",
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],   # <-- add this
            "security": "Unknown",
            "maintainability": 0,
            "readability": 0,   
    }