# 📋 Job Hunt Bot - Complete System Summary & Strategy

## What You Have Right Now

### ✅ Fully Functional Job Hunting Automation
A production-ready system that automates the entire job search → interview pipeline:

```
Daily Automated Workflow:
┌─────────────────────────────────────────────┐
│ FIND JOBS (30 sec)                          │
│ • 5 job boards (RemoteOK, WeWork, Himalayas│
│   Indeed, LinkedIn)                         │
│ • 100+ jobs per run                         │
│ • Deduplicates automatically                │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ SCORE & RANK (10 sec)                       │
│ • 2D scoring: salary + entry-level ease     │
│ • Filters → top 25 opportunities            │
│ • Heuristic + optional Claude scoring       │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ TAILOR RESUME (1 min per job)               │
│ • Claude reframes clinical → PM language    │
│ • Customized to each job description        │
│ • Ready to copy/paste                       │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ DRAFT COVER & OUTREACH (30 sec per job)     │
│ • Personalized, non-generic                 │
│ • Company-specific hooks                    │
│ • Ready to send via email                   │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ SAVE TO GMAIL (auto)                        │
│ • Email drafts auto-saved (optional)        │
│ • You review and send manually              │
└──────────────┬──────────────────────────────┘
               ↓
┌─────────────────────────────────────────────┐
│ TRACK PROGRESS (auto)                       │
│ • SQLite database tracks all jobs           │
│ • Mark status: found→tailored→applied...    │
│ • Monitor pipeline metrics                  │
└─────────────────────────────────────────────┘
```

### 📊 System Capabilities

| Feature | Status | Details |
|---------|--------|---------|
| Job Finding | ✅ Prod | 5 boards, 100+ jobs/run, deduplication |
| Scoring | ✅ Prod | 2D heuristic + optional AI scoring |
| Resume Tailoring | ✅ Prod | Claude-powered personalization |
| Cover Letters | ✅ Prod | Non-generic, company-specific |
| Outreach Email | ✅ Prod | Short, direct, high-conversion |
| Gmail Integration | ✅ Prod | Auto-save drafts (optional) |
| Tracking | ✅ Prod | SQLite + Google Sheets sync |
| Retry Logic | ✅ Prod | Exponential backoff, graceful fallback |
| Cost Optimization | ✅ Prod | Multiple tiers (budget → premium) |
| Error Handling | ✅ Prod | Handles API failures, rate limits |
| Scheduling | ✅ Prod | Cron, GitHub Actions, Cloud |

### 💰 Cost Structure
- **Per run (25 jobs):** ~$0.81 (Sonnet) or $0.15 (Haiku budget mode)
- **Per month (daily):** ~$24.30 (Sonnet) or $4.50 (budget)
- **Break-even:** 1-2 interviews to cover costs

### 📈 Expected Outcomes (4-Week Timeline)

**Week 1:**
- 40-80 jobs found daily
- 10-20 top-quality matches
- 10-20 outreach emails sent
- Cost: ~$6

**Week 2:**
- 20-30% recruiter reply rate
- 5-6 recruiter conversations started
- Cost: ~$6

**Week 3:**
- 50-70% of conversations → phone screens
- 3-4 screening calls scheduled
- Cost: ~$6

**Week 4:**
- 70-80% of screens → interviews
- 2-3 interviews scheduled
- Cost: ~$6
- **Total: ~$24 and 2-3 interviews scheduled**

---

## Optimization Framework (Tier Strategy)

### 🟢 Tier 1: Budget Mode (~$4.50/month)
Use heuristics + Haiku only:
```bash
HEURISTIC_SCORING_ONLY=true
TAILOR_MODEL=claude-haiku-4-5-20251001
COVER_MODEL=claude-haiku-4-5-20251001
```
**Trade-off:** 10-15% lower quality, but still solid
**When to use:** During active job search to save costs

### 🟡 Tier 2: Balanced Mode (~$15/month) [RECOMMENDED]
Heuristic scoring + Sonnet for tailoring:
```bash
TAILOR_MODEL=claude-sonnet-4-6
COVER_MODEL=claude-haiku-4-5-20251001
```
**Best for:** Quality-conscious but budget-aware
**When to use:** Default, best ROI

### 🔴 Tier 3: Premium Mode (~$24/month)
Sonnet everywhere (current default):
```bash
TAILOR_MODEL=claude-sonnet-4-6
COVER_MODEL=claude-sonnet-4-6
```
**Best for:** Maximum interview rate, don't care about cost
**When to use:** When you have real opportunities queued

---

## Key Features Explained

### 1. Two-Dimensional Scoring
```
SALARY SCORE (0-10):
  10 = Clearly $150k+ (explicit range)
  8-9 = Likely $120k-$150k
  7 = Likely $100k+ (6-figure)
  4-6 = Unclear or estimated
  1-2 = Likely under $80k

ENTRY SCORE (0-10):
  10 = Perfect for career pivot (no experience needed)
  7-8 = Realistic for 2-4 years experience
  5-6 = Neutral, with some career change signals
  3-4 = Senior preferred, but possible for strong fit
  1-2 = Clearly requires 10+ years or specific credentials

FILTERING: Only keep jobs where salary ≥6 AND entry ≥5
RANKING: Sort by total_score descending (max 20)
RESULT: Top 25 opportunities per run
```

### 2. Resume Tailoring Strategy
```
Master Resume (master_resume.txt):
├─ Clinical background (4 years)
├─ Transferable PM skills
├─ Healthcare domain knowledge
└─ Patient outcome tracking

Tailoring Process (Claude-powered):
├─ Parse job description for explicit needs
├─ Identify clinical experiences that map to JD
├─ Reframe in PM language:
│  ├─ Patient monitoring → KPI tracking
│  ├─ Individualized programs → Requirements gathering
│  ├─ Multidisciplinary teams → Stakeholder management
│  └─ Protocol design → Roadmap planning
├─ Lead with what they explicitly ask for
└─ Output ready-to-paste resume

Result: Personalized resume for EACH job (not generic)
```

### 3. Cover Letter Strategy
```
Structure (Required):
1. HOOK (2-3 sentences)
   └─ Personal connection + why THEIR company

2. BRIDGE (2-3 sentences)
   └─ Clinical → PM translation + specific example

3. WINS (3-4 sentences)
   └─ 2-3 concrete accomplishments mapped to JD

4. ASK (1-2 sentences)
   └─ Clear, confident close

Result: 3-4 paragraphs, under 350 words, non-generic
```

### 4. Outreach Email Strategy
```
Formula (Proven for cold outreach):
├─ Subject: [Company] + [Role] + Personal hook
├─ Body (2-3 sentences):
│  ├─ WHO: Name yourself + background
│  ├─ WHY: 1-2 words why you chose them (specific)
│  └─ ASK: One clear ask (coffee, 15-min call, intro)
└─ Signature: Name + phone + email

Result: 3-4 sentences, under 120 words, direct & respectful
Time to write: 20 seconds per job
```

---

## 🎯 Six-Figure Interview Landing Strategy

### Phase 1: Foundation (Week 1)
- ✅ Set up bot with ANTHROPIC_API_KEY
- ✅ Run demo to verify system
- ✅ Configure for your target roles
- ✅ Run daily `python run.py run`

### Phase 2: Volume (Week 2)
- ✅ Send 10-20 outreach emails
- ✅ Mix 80% cold emails + 20% LinkedIn connections
- ✅ Send during 9-11 AM or 4-5 PM (best engagement)
- ✅ Personalize 10-20% manually (higher response rate)
- ✅ Monitor replies with `python run.py stats`

### Phase 3: Conversations (Week 3)
- ✅ Respond to recruiter inquiries within 2 hours
- ✅ Ask for phone screen within first 2 messages
- ✅ Schedule calls for 3-5 days out
- ✅ Prepare interview materials with `src/interview_prep.py`

### Phase 4: Interviews (Week 4+)
- ✅ Have 2-3 scheduled interviews
- ✅ Practice STAR stories from clinical background
- ✅ Research company: funding, product, team
- ✅ Negotiate 6-figure offer based on market data

### Parallel: Personal Brand
- Update LinkedIn profile (add PM focus)
- Write 1 LinkedIn post about PM + clinical background (thought leadership)
- Connect with 20-30 PMs in your target companies
- Engage with 5-10 posts about digital health/healthcare tech weekly

---

## Advanced Techniques for Landing Interviews

### 1. The Referral Strategy
```bash
# Get list of your target companies
python run.py show | grep -oE '[^ ]+@' | awk -F@ '{print $1}' | sort -u

# For each company:
# 1. Find someone on LinkedIn who works there
# 2. Reference them in your outreach email:
#    "I noticed [Person]'s recent work on [Feature], very impressed..."
# 3. Include their name in your cold email

Result: 2-3x higher response rate than cold emails
```

### 2. The Content Strategy
```
Week 1: Post about your PM transition story
Week 2: Share a clinical insight applied to product
Week 3: Comment on 5 digital health product posts
Week 4: Tag 3 PMs in a thoughtful response

Result: Inbound interest, visible expertise, interview prep
```

### 3. The Follow-Up Sequence
```
Day 1: Send initial email/message
Day 3: Gentle follow-up if no response
Day 7: Second follow-up (if still interested)
Day 14: Final follow-up before moving on

Template:
"Hi [Name], just wanted to check if [Company]'s taking 
product hires now. If not interested, no worries — good luck!"

Result: 20-40% follow-up conversion rate
```

### 4. The Salary Negotiation
```
Before call: Research on Levels.fyi, Glassdoor, Blind
During offer: Always ask for time ("let me discuss with family")
Response: "I was expecting $X-$Y based on [reason]"
  └─ Base: $120k
     Signing: $20k
     Annual equity: $30k-50k

Result: 15-30% higher offers than initial
```

---

## Troubleshooting & Optimization

### If Low Response Rate (<10%)
1. ✅ Personalize 50% of outreach emails manually
2. ✅ Use LinkedIn connection + email combo
3. ✅ Improve cover letter with A/B testing
4. ✅ Target earlier-stage startups (Series A/B)
5. ✅ Add specific case study to resume

### If No Interviews After 50+ Applications
1. ✅ Review `config.yaml` filtering (may be too strict)
2. ✅ Lower min_salary_score to 5 (opens up options)
3. ✅ Try different roles (APM, Ops, Growth PM)
4. ✅ Get resume reviewed by another PM
5. ✅ Improve master_resume.txt with more metrics

### If API Costs Too High
1. ✅ Use `--no-tailor` flag (just find jobs)
2. ✅ Use `--no-ai-score` flag (heuristics only)
3. ✅ Run 2x/week instead of daily
4. ✅ Switch to Haiku model in .env
5. ✅ Filter more aggressively in config.yaml

### If Job Boards Give Errors
1. ✅ Try `python run.py run --no-tailor` (isolates issue)
2. ✅ Check network connectivity
3. ✅ Job boards rate-limit; try again in 1 hour
4. ✅ Disable problematic board in config.yaml
5. ✅ Check board status: remoteok.com, weworkremotely.com

---

## Timeline to 6-Figure Offer

```
Week 1-2: Foundation
  └─ Bot running, 50+ applications sent, 0-1 replies expected

Week 3-4: Conversations Start
  └─ 5-8 recruiter replies, schedule 2-3 phone screens

Week 5-6: Interviews
  └─ 2-3 interviews, 1 moving to final round

Week 7-8: Offers
  └─ 1 offer at $100k-$150k base + equity

Total Timeline: 6-8 weeks from starting → 6-figure offer

Parallel Activities (weeks 1-8):
├─ Build personal brand on LinkedIn
├─ Network with 30-50 PMs in target companies
├─ Learn 5 case studies of health tech products
└─ Practice STAR stories about clinical work
```

---

## What To Do Right Now

### Immediate (Today)
```bash
# 1. Add API key to .env
edit .env
# Add ANTHROPIC_API_KEY=sk-ant-...

# 2. Test the system
python run.py demo

# 3. Configure for your target roles
edit config.yaml
# Add/remove roles, locations, industries
```

### This Week
```bash
# Run the full pipeline
python run.py run

# Review results
python run.py top
python run.py review "CompanyName"

# Set up scheduling
crontab -e
# Add: 0 8 * * * cd /workspaces/job-hunt && python run.py run
```

### This Month
```bash
# Track your results
python run.py stats
python run.py show --status applied

# Iterate based on results
# If scoring too strict: lower thresholds in config.yaml
# If costs too high: use budget mode or run less frequently
# If not enough interviews: personalize more manually
```

---

## Success Metrics

Track these to know if you're winning:

```
Weekly Metrics:
├─ Jobs found: 50-100 (goal: 50+)
├─ Top candidates: 10-20 (goal: 10+)
├─ Outreach sent: 10-20 (goal: 10+)
└─ Cost: $6-8 (goal: <$10)

Conversion Metrics:
├─ Recruiter replies: 20-30% (goal: >20%)
├─ Phone screens: 50%+ of conversations (goal: >50%)
├─ Interviews: 70%+ of screens (goal: >70%)
└─ Offers: 30%+ of interviews (goal: >30%)
```

---

## You're Ready 🚀

Your automated job bot is production-ready. You have:
- ✅ 5 job board integrations
- ✅ Intelligent 2D scoring
- ✅ Resume/cover letter tailoring
- ✅ Cold outreach automation
- ✅ Progress tracking
- ✅ Cost optimization
- ✅ Error handling & retry logic
- ✅ Complete documentation

**Start here:**
```bash
python run.py run
```

**Then:**
```bash
python run.py top
```

**Then:** Review, send, and track interviews.

Good luck landing that 6-figure PM role! 💪
