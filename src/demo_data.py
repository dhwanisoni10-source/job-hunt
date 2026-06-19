"""
Sample jobs for offline/demo testing of the scoring pipeline.
Run: python run.py demo
"""

from src.models import Job

SAMPLE_JOBS = [
    Job(
        title="Product Manager, Digital Health",
        company="Sword Health",
        location="Remote",
        url="https://jobs.swordhealth.com/pm-digital-health",
        source="demo",
        salary="$120,000 – $150,000",
        description="""Series D health-tech startup. We're looking for a PM to own our patient
        engagement roadmap. 2-4 years PM experience preferred. Healthcare background
        a huge plus. Competitive salary, equity, remote-first. We love career pivots
        and mission-driven candidates from clinical backgrounds.""",
        job_id="sword-health-pm-001",
    ),
    Job(
        title="Associate Product Manager",
        company="Garner Health",
        location="Remote",
        url="https://jobs.garnerhealth.com/apm",
        source="demo",
        salary="$100,000 – $120,000",
        description="""Seed-stage health benefits startup backed by top VCs. Looking for an APM
        to work directly with the founding team. 0-2 years experience, eager to learn,
        collaborative personality. No engineering background required. We offer training.
        Healthcare curiosity is all we need. 100% remote, full benefits.""",
        job_id="garner-apm-001",
    ),
    Job(
        title="Technical Program Manager",
        company="Nuna Health",
        location="Remote USA",
        url="https://jobs.nuna.com/tpm",
        source="demo",
        salary="$130,000 – $160,000",
        description="""Nuna builds healthcare data infrastructure for Medicaid. TPM role requiring
        5+ years of project management experience, PMP preferred. Must have healthcare
        data experience. Senior-level cross-functional leadership. B2B enterprise SaaS.""",
        job_id="nuna-tpm-001",
    ),
    Job(
        title="Customer Success Manager",
        company="Turquoise Health",
        location="Remote",
        url="https://jobs.turquoise.health/csm",
        source="demo",
        salary="$90,000 – $115,000",
        description="""Early-stage startup (Series A) making healthcare pricing transparent.
        CSM role: onboard hospital clients, drive adoption, track outcomes. 1-3 years
        customer-facing experience. Healthcare knowledge a plus. Small team, big impact.
        Willing to train the right person.""",
        job_id="turquoise-csm-001",
    ),
    Job(
        title="Senior Software Engineer",
        company="Hims & Hers Health",
        location="Remote",
        url="https://jobs.hims.com/swe",
        source="demo",
        salary="$160,000 – $200,000",
        description="""Telehealth company looking for senior SWE with 7+ years experience,
        strong in React/Node, AWS expertise required. Staff-level engineering, owns
        systems design. PhD preferred. Immediate hire.""",
        job_id="hims-swe-001",
    ),
    Job(
        title="Implementation Manager",
        company="Cohere Health",
        location="Remote",
        url="https://jobs.coherehealth.com/impl-mgr",
        source="demo",
        salary="$105,000 – $125,000",
        description="""Cohere uses AI to streamline prior authorizations. Implementation Manager
        will onboard health plan clients. 2-4 years project management experience.
        Clinical background (exercise physiology, nursing, etc.) strongly preferred.
        Series B, mission-driven, great culture.""",
        job_id="cohere-impl-001",
    ),
    Job(
        title="Operations Manager",
        company="Brightline",
        location="Remote",
        url="https://jobs.hellobrightline.com/ops-mgr",
        source="demo",
        salary="",  # no salary listed
        description="""Children's behavioral health startup. Operations Manager to run clinical
        operations workflows. 3-5 years ops experience, healthcare a plus. Self-starter,
        comfortable in ambiguity. Diverse backgrounds welcome. We believe in
        transferable skills and career changers.""",
        job_id="brightline-ops-001",
    ),
    Job(
        title="Director of Product",
        company="Oscar Health",
        location="Remote",
        url="https://jobs.hioscar.com/dir-product",
        source="demo",
        salary="$180,000 – $230,000",
        description="""Oscar Health is a tech-driven health insurance co. Director of Product
        leading a team of 6 PMs. 10+ years product experience, 3+ years managing PMs.
        VP-track role. Insurance or regulated industry experience required.""",
        job_id="oscar-dir-prod-001",
    ),
    Job(
        title="Product Operations Manager",
        company="Spring Health",
        location="Remote",
        url="https://jobs.springhealth.com/prod-ops",
        source="demo",
        salary="$115,000 – $135,000",
        description="""Mental health benefits company (Series D). Product Ops Manager to bridge
        clinical teams and product engineers. Clinical background (exercise physiology,
        therapy, nursing) strongly valued. 2-5 years experience. Equity + benefits.""",
        job_id="spring-prod-ops-001",
    ),
    Job(
        title="Business Analyst",
        company="Accolade Health",
        location="Remote",
        url="https://jobs.accolade.com/ba",
        source="demo",
        salary="$80,000 – $95,000",
        description="""Healthcare advocacy company. Business Analyst to support health plan
        clients with data and reporting. 1-3 years experience in healthcare or analytics.
        Excel, SQL basics helpful but not required — we train. Entry-level friendly.""",
        job_id="accolade-ba-001",
    ),
]
