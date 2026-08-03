import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")


def create_checkout_session(resume_filename: str, job_desc_snippet: str) -> str:
    """
    Create a Stripe Checkout session for a one-time $9.99 payment.
    Returns the Stripe-hosted checkout URL.
    """
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "AI Resume Match Analysis",
                        "description": "Instant AI-powered resume scoring, gap analysis, and rewrite suggestions.",
                    },
                    "unit_amount": 999,  # $9.99 in cents
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{APP_URL}/",
        metadata={
            "resume_filename": resume_filename,
            "job_snippet": job_desc_snippet[:200],
        },
    )
    return session.url


def verify_payment(session_id: str) -> bool:
    """Check if a Stripe Checkout session was paid."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == "paid"
    except Exception:
        return False
