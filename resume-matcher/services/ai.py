import os
import json
import random
import anthropic

# Mock mode activates automatically if no real API key is set.
# This lets you test the entire app for free. Once you add a real
# ANTHROPIC_API_KEY to your .env file, this switches to live AI
# automatically — no code changes needed.
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MOCK_MODE = not API_KEY.startswith("sk-ant-")

if not MOCK_MODE:
    client = anthropic.Anthropic()


def _mock_analysis(resume_text: str, job_description: str) -> dict:
    """Returns a realistic fake analysis so you can test the full app for free."""
    score = random.randint(62, 88)
    label = (
        "Strong Match" if score >= 75 else
        "Good Match" if score >= 60 else
        "Fair Match"
    )
    return {
        "match_score": score,
        "match_label": label,
        "strengths": [
            "Your experience section shows relevant hands-on project work.",
            "You already list several tools mentioned in the job posting.",
            "Your resume format is clean and easy for recruiters to scan.",
        ],
        "gaps": [
            "The job description emphasizes cloud experience that isn't clearly shown.",
            "Quantified results (numbers, percentages) are missing from your bullet points.",
            "No mention of team collaboration or agile process experience.",
        ],
        "rewritten_summary": (
            "Results-driven professional with hands-on experience building scalable "
            "applications and a strong foundation in the core technologies this role "
            "requires. Known for translating business needs into clean, maintainable "
            "solutions delivered on time."
        ),
        "top_keywords": ["REST APIs", "cloud platforms", "agile", "SQL", "collaboration"],
        "quick_wins": [
            "Add specific metrics to your top 3 bullet points (e.g. 'reduced load time by 40%').",
            "Mention any cloud platform experience explicitly, even personal projects.",
            "Add a one-line summary at the top tailored to this specific role.",
        ],
        "_mock": True,
    }


def analyze_resume(resume_text: str, job_description: str) -> dict:
    """
    Send resume + job description to Claude and get back a structured analysis.
    Falls back to a mock response if no real API key is configured.
    """
    if MOCK_MODE:
        return _mock_analysis(resume_text, job_description)

    prompt = f"""
You are an expert resume coach and senior recruiter with 15 years of experience.

Analyze the resume below against the job description and return a JSON object.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Return ONLY a valid JSON object with exactly these keys (no extra text, no markdown):
{{
  "match_score": <integer 0-100>,
  "match_label": <"Poor Match" | "Fair Match" | "Good Match" | "Strong Match">,
  "strengths": [<3 specific strings explaining what already matches well>],
  "gaps": [<3 specific strings explaining what is missing or weak>],
  "rewritten_summary": "<a 2-3 sentence professional summary rewritten to target this specific job>",
  "top_keywords": [<5 important keywords from the job description to add to the resume>],
  "quick_wins": [<3 short actionable tips to improve the resume for this role immediately>]
}}
"""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())