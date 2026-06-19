"""
Uses Claude to tailor the master resume and draft a cover letter
for each specific job description.

Models: Uses Sonnet-4-6 for tailoring (best quality), can switch to Haiku for cost savings.
"""

import os
import time
import anthropic
from src.models import Job

# MODEL SELECTION (for cost optimization)
# claude-sonnet-4-6: Best quality, ~$0.015 per resume tailoring
# claude-haiku-4-5-20251001: 50% cheaper, good for first pass but slightly lower quality
MODEL = os.getenv("TAILOR_MODEL", "claude-sonnet-4-6")
RESUME_MODEL = os.getenv("RESUME_MODEL", MODEL)
COVER_MODEL = os.getenv("COVER_MODEL", MODEL)
OUTREACH_MODEL = os.getenv("OUTREACH_MODEL", "claude-haiku-4-5-20251001")  # Cheap for emails

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds, exponential backoff

RESUME_SYSTEM = """You are an expert resume writer specializing in career pivots into Product Management.
The candidate is Dhwani Soni: Clinical Exercise Physiologist → Product Manager.
Background: 4+ years driving patient outcomes in cardiac rehabilitation, strong cross-functional collaboration.

CRITICAL: Your goal is to get her an interview for a 6-figure PM role.

When tailoring a resume:
1. REFRAME in PM language: patient monitoring → KPI tracking, individualized programs → requirements gathering, 
   multidisciplinary collaboration → stakeholder management, protocol design → roadmap planning
2. LEAD with what the JD explicitly asks for (if they say "healthcare background required", front-load her clinical work)
3. QUANTIFY impact: "Managed X patients", "Improved Y metric by Z%", "Led team of N"
4. EMPHASIZE transferable skills: data-driven decisions, user advocacy, cross-functional leadership, process improvement
5. KEEP HONEST: Only reframe, don't fabricate. All info must be in master resume.
6. BE CONCISE: One-page format, ATS-friendly, 11-12pt font equivalent

OUTPUT: Full tailored resume as plain text, ready to copy/paste into application. Include header, objective (optional), 
experience, education, skills, certifications."""

COVER_SYSTEM = """You are an expert cover letter writer for Product Manager roles targeting 6-figure positions.
Candidate: Dhwani Soni (Clinical Exercise Physiologist pivoting to PM roles in digital health).

CRITICAL: Your goal is to stand out and get a phone screen within 48 hours.

Structure (must be strict):
1. HOOK (2-3 sentences): Personal connection + mission alignment. Why you care about THIS company.
   Example: "Your work on patient engagement through data resonates deeply with my 4 years..."
2. BRIDGE (2-3 sentences): Translate clinical background to PM credibility. Specific example.
   Example: "I've designed 50+ individualized care programs—that's product discovery and requirements gathering..."
3. WINS (3-4 sentences): 2-3 concrete accomplishments mapped to their JD needs.
   Example: "Collaborated with cardiologists (stakeholders) to iterate treatment protocols (roadmap)..."
4. ASK (1-2 sentences): Clear, confident close. No desperation.
   Example: "I'd love to discuss how my background applies. Available for a call this week."

TONE: Warm, confident, specific. Show you did research. NO GENERIC PHRASES like "I am writing", "Please consider", "I look forward to".
LENGTH: Exactly 3-4 paragraphs, under 350 words.
OUTPUT: Body only (no date, address, salutation—user adds these). Ready to paste in email."""

OUTREACH_SYSTEM = """You are writing a SHORT cold outreach email to a recruiter or hiring manager.
Candidate: Dhwani Soni (4-year clinical background, pivoting to PM roles).

CRITICAL: Get them to reply to a coffee chat offer within 5 days.

Structure:
1. SUBJECT LINE (if generating): [Company] + [Role] + Personal touch → "Your approach to patient engagement @ [Company]"
2. BODY (2-3 sentences): 
   - WHO: Name yourself + what you're pivoting from (clinical → PM)
   - WHY: 1-2 words why you're interested in THEIR company (not generic)
   - ASK: One ask only → "Coffee chat?", "15-min call?", "Intro?"
3. SIGNATURE: Name + phone + email

TONE: Direct, confident, respectful of their time. No fluff.
LENGTH: 3-4 sentences max, under 120 words.
RULES: 
- NO "I hope this finds you well"
- NO long paragraphs
- NO asking for feedback on resume
- DO be specific about why you chose them
- DO show you researched the company

OUTPUT: Full email, ready to send. Include subject line."""


def _client() -> anthropic.Anthropic:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Set ANTHROPIC_API_KEY in your .env file")
    return anthropic.Anthropic(api_key=key)


def _call_claude(system: str, prompt: str, model: str, max_tokens: int = 1500) -> str:
    """Call Claude with retry logic and exponential backoff."""
    client = _client()
    
    for attempt in range(MAX_RETRIES):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except anthropic.RateLimitError:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (2 ** attempt)  # exponential backoff
                print(f"  ⏱️  Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                raise
        except anthropic.APIError as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  ⚠️  API error: {e}. Retrying...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                raise


def tailor_resume(master_resume: str, job: Job) -> str:
    prompt = f"""Master resume:
<resume>
{master_resume}
</resume>

Job description:
<job>
Title: {job.title}
Company: {job.company}
Location: {job.location}
Description:
{job.description[:3000]}
</job>

Produce a tailored resume for this specific role. 
- Keep all dates and employers exactly as in master resume (don't fabricate)
- Reframe clinical roles using PM language
- Lead with skills the JD explicitly asks for
- Make it compelling for a recruiter scanning 10 seconds"""

    return _call_claude(RESUME_SYSTEM, prompt, RESUME_MODEL, max_tokens=1500)


def draft_cover_letter(master_resume: str, job: Job) -> str:
    prompt = f"""Master resume:
<resume>
{master_resume}
</resume>

Target role: {job.title} at {job.company}
Job description (first 1500 chars):
{job.description[:1500]}

WRITE THE BODY of a cover letter (no date/address/salutation). 
The reader will receive this as an email, so write it as email body text.
Be specific to this company and role. Make them WANT to call you."""

    return _call_claude(COVER_SYSTEM, prompt, COVER_MODEL, max_tokens=800)


def draft_outreach_email(job: Job, candidate_name: str = "Dhwani Soni") -> str:
    prompt = f"""Target: {job.title} at {job.company}
Job description excerpt: {(job.description or '')[:500]}

WRITE A COMPLETE EMAIL (with subject line) that I would send to a recruiter or hiring manager.
Make it specific, direct, and compelling. Include a clear ask (coffee chat, intro, 15-min call).
Show you researched the company."""

    return _call_claude(OUTREACH_SYSTEM, prompt, OUTREACH_MODEL, max_tokens=300)
