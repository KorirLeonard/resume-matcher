import os
import json
import anthropic
from typing import Dict, Any

"""
Robust Anthropic wrapper for analyze_resume.

Notes:
- This module never passes `proxies=` into the client constructor.
- If you need proxies, set HTTP_PROXY/HTTPS_PROXY in the environment or configure the SDK transport/session per the SDK docs.
- The wrapper tolerates different SDK shapes and strips markdown fences.
"""


def _create_anthropic_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_KEY")
    ClientClass = getattr(anthropic, "Client", None) or getattr(anthropic, "Anthropic", None)
    if ClientClass is None:
        raise RuntimeError("anthropic SDK not found or has an unexpected API. Install/update the 'anthropic' package.")

    # Try passing api_key if the SDK accepts it; otherwise fallback to default ctor.
    if api_key:
        try:
            return ClientClass(api_key=api_key)
        except TypeError:
            return ClientClass()
    return ClientClass()


try:
    _AN_CLIENT = _create_anthropic_client()
    _AN_CLIENT_INIT_ERROR = None
except Exception as e:
    _AN_CLIENT = None
    _AN_CLIENT_INIT_ERROR = e


def _extract_text_from_anthropic_response(resp: Any) -> str:
    """
    Try several common response shapes to extract assistant text.
    """
    # plain string
    if isinstance(resp, str):
        return resp

    # dict-like shapes
    if isinstance(resp, dict):
        for key in ("text", "completion", "content", "message", "output"):
            if key in resp and isinstance(resp[key], str):
                return resp[key]
        # content could be a list with dict/text inside
        if "content" in resp and isinstance(resp["content"], list) and len(resp["content"]) > 0:
            first = resp["content"][0]
            if isinstance(first, dict) and "text" in first and isinstance(first["text"], str):
                return first["text"]
            if isinstance(first, str):
                return first

    # object/attribute shapes (message.content[0].text, .completion, etc.)
    try:
        message = getattr(resp, "message", None) or getattr(resp, "result", None) or getattr(resp, "response", None) or resp
        if message is not None:
            content = getattr(message, "content", None)
            if content and isinstance(content, (list, tuple)) and len(content) > 0:
                first = content[0]
                text = getattr(first, "text", None) or (first.get("text") if isinstance(first, dict) else None)
                if isinstance(text, str):
                    return text
            text = getattr(message, "text", None) or getattr(message, "completion", None)
            if isinstance(text, str):
                return text
    except Exception:
        pass

    raise ValueError("Could not extract assistant text from response object; unexpected response shape.")


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    # triple backticks
    if s.startswith("```") and "```" in s[3:]:
        parts = s.split("```")
        inner = parts[1]
        if "\n" in inner:
            first_line, rest = inner.split("\n", 1)
            if first_line.isalpha() or first_line.lower() in ("json", "json+yaml"):
                return rest.strip()
        return inner.strip()
    # single backtick
    if s.startswith("`") and "`" in s[1:]:
        parts = s.split("`")
        return parts[1].strip()
    return s


def analyze_resume(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Send resume + job description to Claude and return a structured analysis.
    """
    if _AN_CLIENT is None:
        raise RuntimeError(f"Anthropic client not initialized: {_AN_CLIENT_INIT_ERROR}")

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

    # Try several call shapes used across Anthropic SDK versions.
    last_exc = None
    for call_shape in ("messages.create", "completions.create", "complete", "create_completion"):
        try:
            obj = _AN_CLIENT
            for part in call_shape.split("."):
                obj = getattr(obj, part)
            resp = obj(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = _extract_text_from_anthropic_response(resp)
            raw = _strip_code_fences(raw)
            return json.loads(raw.strip())
        except Exception as e:
            last_exc = e
            continue

    raise RuntimeError(f"Failed to call Anthropic API using tested client methods. Last error: {last_exc}")
