import json
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def analyze_resume(resume_text: str, job_description: str) -> dict:
    """
    Send resume + job description to Claude and get back a structured analysis.
    Returns a dict with score, strengths, gaps, rewritten summary, and keywords.
    """
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
    # Strip markdown fences if Claude wraps the JSON
    if raw.startswith("`"):
        raw = raw.split("`")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
