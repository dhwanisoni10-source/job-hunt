"""
Score each job on two dimensions:
  salary_score   0-10  (how likely / clearly 6-figure)
  entry_score    0-10  (how easy to get in: fewer yrs exp, startup, growing, open to pivot)
  total_score    0-20  (sum, used for ranking)

Heuristics run first (fast, free). Claude fills in the rest if ANTHROPIC_API_KEY is set.
"""

import os
import re
import json
import anthropic
from src.models import Job

# ── Salary heuristics ────────────────────────────────────────────────────────

SIX_FIGURE_ROLES = {
    "product manager", "senior product manager", "principal product manager",
    "engineering manager", "software engineer", "data scientist", "data engineer",
    "machine learning engineer", "ml engineer", "backend engineer", "frontend engineer",
    "full stack engineer", "fullstack engineer", "devops engineer", "platform engineer",
    "solutions engineer", "solutions architect", "cloud architect",
    "technical program manager", "program manager", "product designer",
    "ux researcher", "growth manager", "analytics engineer",
}

HIGH_SALARY_KEYWORDS = [
    "competitive salary", "above market", "market rate", "equity",
    "stock options", "rsu", "series a", "series b", "series c",
    "yc", "y combinator", "top startup", "well-funded",
]


def _parse_salary_range(text: str):
    """Return (min, max) in dollars, or (None, None)."""
    # e.g. "$120k – $160k", "$120,000 - $160,000", "$100K+"
    pat = r"\$([\d,]+)\s*[kK]?\s*[-–to]+\s*\$([\d,]+)\s*([kK])?"
    m = re.search(pat, text)
    if m:
        lo = float(m.group(1).replace(",", ""))
        hi = float(m.group(2).replace(",", ""))
        if m.group(3) or lo < 1000:  # 'k' suffix or bare number like 120
            lo *= 1000
            hi *= 1000
        return lo, hi

    # Single figure: "$150k+" or "$150,000"
    pat2 = r"\$([\d,]+)\s*([kK])?\+?"
    m2 = re.search(pat2, text)
    if m2:
        val = float(m2.group(1).replace(",", ""))
        if m2.group(2) or val < 1000:
            val *= 1000
        return val, val
    return None, None


def _salary_score_heuristic(job: Job) -> int:
    combined = f"{job.title} {job.salary or ''} {job.description or ''}".lower()

    # If salary is stated
    sal_text = f"{job.salary or ''} {job.description or ''}"
    lo, hi = _parse_salary_range(sal_text)
    if lo is not None:
        avg = (lo + hi) / 2
        if avg >= 150_000:
            return 10
        if avg >= 130_000:
            return 9
        if avg >= 110_000:
            return 8
        if avg >= 100_000:
            return 7
        if avg >= 85_000:
            return 4
        return 2

    # No salary stated — infer from role + signals
    score = 5  # default neutral
    title_lower = job.title.lower()
    for role in SIX_FIGURE_ROLES:
        if role in title_lower:
            score = 7
            break
    for kw in HIGH_SALARY_KEYWORDS:
        if kw in combined:
            score += 1
    if any(w in title_lower for w in ["senior", "staff", "principal", "lead"]):
        score += 1
    return min(score, 10)


# ── Entry ease heuristics ─────────────────────────────────────────────────────

HARD_REQUIREMENTS = [
    r"\b10\+\s*years", r"\b8\+\s*years", r"\b7\+\s*years",
    r"phd required", r"medical degree", r"jd required",
    r"director", r"\bvp\b", r"vice president",
    r"clearance required", r"top secret",
]

EASY_SIGNALS = [
    "entry level", "associate", "junior", "0-2 years", "1-3 years", "2-4 years",
    "career change", "career switcher", "bootcamp", "no degree required",
    "self-taught", "non-traditional", "pivoting", "transferable",
    "seed", "early stage", "series a", "growing team", "small team",
    "collaborative", "mission-driven", "diverse backgrounds",
    "willing to train", "growth opportunity",
]

PIVOT_FRIENDLY = [
    "clinical", "healthcare", "health", "wellness", "patient",
    "exercise", "physical therapy", "nursing", "medical",
]


def _entry_score_heuristic(job: Job) -> int:
    combined = f"{job.title} {job.description or ''}".lower()

    # Hard disqualifiers
    for pat in HARD_REQUIREMENTS:
        if re.search(pat, combined):
            return 2

    score = 5

    for signal in EASY_SIGNALS:
        if signal in combined:
            score += 1

    # Bonus if the role is pivot-friendly (healthcare background fits)
    for kw in PIVOT_FRIENDLY:
        if kw in combined:
            score += 1
            break

    # Penalty for very senior titles
    title_lower = job.title.lower()
    if any(w in title_lower for w in ["senior", "staff", "principal", "staff"]):
        score -= 1

    return max(1, min(score, 10))


# ── Claude deep-score (optional) ─────────────────────────────────────────────

SCORE_SYSTEM = """You score remote job listings for a specific candidate.

Candidate: Dhwani Soni
Background: Clinical Exercise Physiologist (4 years), no prior PM title but strong transferable skills:
- Patient outcome tracking (de facto product analytics)
- Cross-functional collaboration (doctors, nurses, administration)
- Protocol design (requirements + iteration)
- Quality improvement projects (roadmap + KPIs)
- Masters in Kinesiology
Currently targeting: Product Manager, Associate PM, Operations roles
Goal: 6-figure ($100k+) remote roles that are realistic to land given her background.

You MUST respond with ONLY valid JSON (no markdown, no explanation):
{"salary_score": <1-10>, "entry_score": <1-10>, "reasoning": "<25 words max>"}

salary_score: 10=clearly $150k+, 7=likely $100-130k, 4=unclear, 1=clearly under $80k
entry_score: 10=perfect for career pivot/no experience needed, 5=neutral, 1=requires 8+ years or specific tech stack she doesn't have"""


def claude_score(job: Job) -> dict:
    """Call Claude to get salary + entry scores. Returns dict with keys salary_score, entry_score, reasoning."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return {}

    try:
        client = anthropic.Anthropic(api_key=key)
        prompt = f"""Job: {job.title} at {job.company}
Location: {job.location}
Salary listed: {job.salary or 'not stated'}
Description (first 1200 chars):
{(job.description or '')[:1200]}"""

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",  # fast + cheap for scoring
            max_tokens=120,
            system=SCORE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        return json.loads(raw)
    except Exception:
        return {}


# ── Public interface ──────────────────────────────────────────────────────────

def score_job(job: Job, use_ai: bool = True) -> dict:
    """
    Returns:
      {salary_score, entry_score, total_score, reasoning, meets_six_figures, is_easy_entry}
    """
    h_sal = _salary_score_heuristic(job)
    h_ent = _entry_score_heuristic(job)

    ai = {}
    if use_ai and os.getenv("ANTHROPIC_API_KEY"):
        ai = claude_score(job)

    salary_score = ai.get("salary_score", h_sal)
    entry_score = ai.get("entry_score", h_ent)
    reasoning = ai.get("reasoning", "")

    return {
        "salary_score": salary_score,
        "entry_score": entry_score,
        "total_score": salary_score + entry_score,
        "reasoning": reasoning,
        "meets_six_figures": salary_score >= 7,
        "is_easy_entry": entry_score >= 6,
    }


def passes_filters(job: Job, min_salary_score: int = 7, min_entry_score: int = 5) -> bool:
    """Quick heuristic gate — used before AI scoring to reduce API calls."""
    sal = _salary_score_heuristic(job)
    ent = _entry_score_heuristic(job)
    return sal >= min_salary_score and ent >= min_entry_score
