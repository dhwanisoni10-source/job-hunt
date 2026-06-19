"""
Uses Claude to tailor the master resume and draft a cover letter
for each specific job description.
"""

import os
import anthropic
from src.models import Job

MODEL = "claude-sonnet-4-6"

RESUME_SYSTEM = """You are an expert resume writer specializing in career pivots into Product Management.
The candidate is Dhwani Soni, a Clinical Exercise Physiologist transitioning to Product Manager roles,
especially in digital health and health tech.

When tailoring a resume:
- Reframe clinical experience using PM language (discovery, requirements, roadmap, iteration, KPIs, stakeholders)
- Surface the most relevant experience for the specific job description
- Keep it honest — only use what's in the master resume
- Lead with transferable skills the JD explicitly calls out
- Output the full tailored resume as plain text, ready to paste"""

COVER_SYSTEM = """You are an expert cover letter writer for Product Manager roles.
Write in a warm, professional, confident voice. Keep it under 350 words.
Structure: (1) hook that ties clinical background to the company's mission,
(2) 2-3 concrete transferable wins, (3) clear ask.
Do NOT use generic phrases like 'I am writing to apply'. Be specific."""

OUTREACH_SYSTEM = """You are writing a short cold outreach email to a recruiter or hiring manager on LinkedIn or email.
The candidate is Dhwani Soni, a Clinical Exercise Physiologist pivoting to Product Manager.
Keep it under 120 words. Be direct, specific to their company, and end with one clear ask.
No fluff. No 'I hope this finds you well'."""


def _client() -> anthropic.Anthropic:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("Set ANTHROPIC_API_KEY in your .env file")
    return anthropic.Anthropic(api_key=key)


def tailor_resume(master_resume: str, job: Job) -> str:
    client = _client()
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

Produce a tailored resume for this specific role. Keep all dates and employers accurate.
Emphasize transferable skills that match what this JD is asking for."""

    msg = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=RESUME_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def draft_cover_letter(master_resume: str, job: Job) -> str:
    client = _client()
    prompt = f"""Master resume:
<resume>
{master_resume}
</resume>

Job:
Title: {job.title}
Company: {job.company}
Description:
{job.description[:2000]}

Write a tailored cover letter for this role."""

    msg = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=COVER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def draft_outreach_email(job: Job, candidate_name: str = "Dhwani Soni") -> str:
    client = _client()
    prompt = f"""Candidate: {candidate_name} (Clinical Exercise Physiologist → Product Manager)
Target role: {job.title} at {job.company}
Company context from JD: {job.description[:500]}

Write a short cold outreach email to a recruiter or hiring manager at {job.company}."""

    msg = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=OUTREACH_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
