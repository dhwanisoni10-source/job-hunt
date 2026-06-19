"""
Claude answers screening questions automatically.
Maps common application questions to Dhwani's profile.
"""

import os
import anthropic

CANDIDATE = {
    "name": "Dhwani Soni",
    "email": "sonidhwaniwork@gmail.com",
    "phone": "734-309-2161",
    "location": "Westland, MI 48185",
    "city": "Westland",
    "state": "MI",
    "zip": "48185",
    "linkedin": "",
    "years_experience": "4",
    "authorized_to_work": "Yes",
    "require_sponsorship": "No",
    "gender": "Female",
    "ethnicity": "Asian",
    "veteran": "No",
    "disability": "No",
    "salary_expectation": "90000",
    "start_date": "2 weeks",
    "remote_preference": "Remote or Hybrid",
}

# Hardcoded answers to common screening questions (fast path, no LLM needed)
QUICK_ANSWERS = {
    # authorization
    "authorized to work": "Yes",
    "require visa sponsorship": "No",
    "require sponsorship": "No",
    "legally authorized": "Yes",
    # experience
    "years of experience": "4",
    "years of product management": "0",   # honest — pivoting
    "years of clinical experience": "4",
    # remote
    "remote": "Yes",
    "hybrid": "Yes",
    "willing to relocate": "No",
    # salary
    "salary expectation": "90000",
    "desired salary": "90000",
    "compensation": "90000",
    # basics
    "first name": "Dhwani",
    "last name": "Soni",
    "full name": "Dhwani Soni",
    "email": "sonidhwaniwork@gmail.com",
    "phone": "734-309-2161",
    "city": "Westland",
    "state": "Michigan",
    "zip": "48185",
    "country": "United States",
    "linkedin": "",
    "website": "",
    "portfolio": "",
    "cover letter": "",  # will be filled from tailored cover letter
}


def quick_answer(question: str) -> str | None:
    """Return a fast hardcoded answer if we recognize the question."""
    q = question.lower().strip()
    for key, val in QUICK_ANSWERS.items():
        if key in q:
            return val
    return None


def ai_answer(question: str, job_context: str, resume: str) -> str:
    """Use Claude to answer an unknown screening question."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return ""
    client = anthropic.Anthropic(api_key=key)

    prompt = f"""You are filling out a job application for Dhwani Soni.

Candidate profile:
- Name: Dhwani Soni
- Background: Clinical Exercise Physiologist (4+ years, cardiac rehab at Trinity Health & Corewell Health)
- Pivoting to: Product Manager in digital health
- Location: Westland, MI (open to remote)
- Education: BS Kinesiology, Wayne State University 2021
- Authorized to work in US: Yes, no sponsorship needed

Resume summary:
{resume[:1000]}

Job context: {job_context}

Application question: "{question}"

Answer this question briefly and honestly. For yes/no questions, answer with just Yes or No.
For text fields, keep answers under 3 sentences. Do not make up credentials she doesn't have."""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def get_answer(question: str, job_context: str = "", resume: str = "") -> str:
    fast = quick_answer(question)
    if fast is not None:
        return fast
    return ai_answer(question, job_context, resume)
