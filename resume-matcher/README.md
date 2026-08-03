# ResumeMatch AI

An AI-powered resume analyzer that scores your resume against a job description,
identifies gaps, rewrites your summary, and surfaces ATS keywords.

**Stack:** Python · FastAPI · Claude API · Stripe · pdfplumber

---

## Setup (Local)

### 1. Clone and install

```bash
git clone <your-repo>
cd resume-matcher
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```
ANTHROPIC_API_KEY=your_key     # https://console.anthropic.com
STRIPE_SECRET_KEY=sk_test_...  # https://dashboard.stripe.com/apikeys
STRIPE_WEBHOOK_SECRET=whsec_... # from Stripe webhook setup (optional for MVP)
APP_URL=http://localhost:8000
```

### 3. Run

```bash
uvicorn main:app --reload
```

Open http://localhost:8000

### 4. Test without paying (local only)

Use the `/demo` endpoint — it skips Stripe entirely:

1. Go to http://localhost:8000
2. Change `action="/submit"` to `action="/demo"` in `templates/index.html` temporarily
3. Upload a PDF and paste a job description
4. See results instantly

---

## Stripe Setup

### Get your keys

1. Create a Stripe account at https://stripe.com
2. Go to Developers → API keys
3. Copy your **Secret key** (starts with `sk_test_` for test mode)
4. Paste into `.env` as `STRIPE_SECRET_KEY`

### Test payments

Use Stripe test card: `4242 4242 4242 4242` · Any future date · Any CVC

---

## Deploy to Railway (Recommended — free to start)

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/resume-matcher.git
git push -u origin main
```

### Step 2 — Deploy on Railway

1. Go to https://railway.app and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repo
4. Railway auto-detects the Procfile and deploys

### Step 3 — Set environment variables on Railway

In your Railway project → Variables tab, add:

```
ANTHROPIC_API_KEY=your_key
STRIPE_SECRET_KEY=sk_live_...   ← switch to live key when ready
APP_URL=https://your-app.up.railway.app
```

### Step 4 — Update Stripe success URL

In `services/stripe_service.py`, the `APP_URL` env var controls the redirect URL.
Make sure `APP_URL` matches your Railway domain.

### Step 5 — Switch to live Stripe keys

1. Go to Stripe Dashboard → toggle off "Test mode"
2. Copy your live secret key (`sk_live_...`)
3. Update `STRIPE_SECRET_KEY` on Railway

---

## Deploy to Render (Alternative)

1. Create account at https://render.com
2. New → Web Service → Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in the Render dashboard

---

## Project Structure

```
resume-matcher/
├── main.py                  # FastAPI routes
├── services/
│   ├── parser.py            # PDF text extraction
│   ├── ai.py                # Claude API integration
│   └── stripe_service.py    # Stripe Checkout
├── templates/
│   ├── index.html           # Landing + upload form
│   ├── result.html          # Analysis results page
│   └── error.html           # Error page
├── static/                  # (empty, for future CSS/JS files)
├── requirements.txt
├── Procfile                 # For Railway/Render deployment
├── .env.example
└── README.md
```

---

## Go-to-Market (Weekend 2)

Once deployed, post these:

**Reddit:**
- r/resumes — "I built a tool that scores your resume against any job posting"
- r/cscareerquestions — "How I built a resume AI in a weekend (and how to use it)"
- r/side_project — share your launch

**Twitter/X:**
- Screenshot of a result page (blur the resume text)
- "Built this in a weekend with FastAPI + Claude AI"

**Pricing idea:** Start at $9.99 per analysis. Once you have 50+ customers,
consider a $19/month subscription for unlimited analyses.

---

## Production Improvements (later)

- [ ] Store session data in Redis (instead of in-memory dict)
- [ ] Add a database (Postgres) to log analyses and revisit them
- [ ] Email the PDF report after payment
- [ ] Add subscription plan with Stripe Billing
- [ ] Rate limiting on the `/demo` endpoint
- [ ] Add Google/GitHub login for returning users
