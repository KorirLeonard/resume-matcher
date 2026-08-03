import os
import uuid
import json
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

from services.parser import extract_text_from_pdf
from services.ai import analyze_resume
from services.stripe_service import create_checkout_session, verify_payment

app = FastAPI(title="AI Resume Matcher")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory session store (use Redis in production)
# Stores {session_token: {resume_text, job_description}} temporarily
pending_sessions: dict = {}


# ─── Home page ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ─── Step 1: User submits resume + job description ────────────────────────────

@app.post("/submit")
async def submit(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    # Validate file type
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await resume.read()
    if len(pdf_bytes) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    try:
        resume_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Store in temp session so we can retrieve after payment
    token = str(uuid.uuid4())
    pending_sessions[token] = {
        "resume_text": resume_text,
        "job_description": job_description,
        "filename": resume.filename,
    }

    # Create Stripe checkout and redirect
    checkout_url = create_checkout_session(
        resume_filename=resume.filename,
        job_desc_snippet=job_description,
    )

    # Attach our token to the success URL via Stripe metadata isn't reliable,
    # so we store the token and pass it through the success redirect query param.
    # We embed token in the session metadata separately.
    # For simplicity, we'll just redirect with our token in the URL.
    # In production: store token server-side tied to Stripe session_id.
    return RedirectResponse(url=checkout_url, status_code=303)


# ─── Step 2: Stripe redirects back after payment ──────────────────────────────

@app.get("/success", response_class=HTMLResponse)
async def success(request: Request, session_id: str):
    if not verify_payment(session_id):
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "Payment not confirmed. Please contact support."
        })

    # For demo: grab the most recent pending session
    # In production: tie session_id to your token in DB
    if not pending_sessions:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "Session expired. Please try again."
        })

    token = list(pending_sessions.keys())[-1]
    data = pending_sessions.pop(token)

    try:
        result = analyze_resume(data["resume_text"], data["job_description"])
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": f"Analysis failed: {str(e)}"
        })

    return templates.TemplateResponse("result.html", {
        "request": request,
        "result": result,
        "filename": data["filename"],
    })


# ─── Free demo endpoint (no payment — for testing) ────────────────────────────

@app.post("/demo", response_class=HTMLResponse)
async def demo(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    """Remove this route in production. For local testing only."""
    pdf_bytes = await resume.read()
    try:
        resume_text = extract_text_from_pdf(pdf_bytes)
        result = analyze_resume(resume_text, job_description)
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": str(e)
        })

    return templates.TemplateResponse("result.html", {
        "request": request,
        "result": result,
        "filename": resume.filename,
    })


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}
