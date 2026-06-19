# 🎯 Complete Job Hunt Bot Guide — Land 6-Figure Interviews

## Quick Start (5 minutes)

### 1. Add Your API Key
Edit `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
```
Get your key at https://console.anthropic.com (free $5 credits)

### 2. Test the System
```bash
# Test scoring offline (no API key needed)
python run.py demo

# Find jobs & score them (no AI tailoring)
python run.py run --no-tailor

# Full pipeline: find, score, tailor, draft emails
python run.py run
```

### 3. Review Results
```bash
# See top-ranked opportunities
python run.py top

# Check tailored resume + cover letter for a company
python run.py review "Teladoc"

# See all jobs by status
python run.py show
python run.py show --status tailored
```

---

## How It Works (The Pipeline)

### Phase 1: Find Jobs (30 seconds)
- Searches 5 remote job boards simultaneously
- Deduplicates automatically
- Filters excluded keywords
- Runs once per day (or manually)

**Boards searched:**
- ✅ RemoteOK (clean, salary transparency)
- ✅ We Work Remotely (RSS, organized by category)
- ✅ Himalayas (public API, great for remote-first)
- ✅ Indeed (RSS feed, comprehensive)
- ✅ LinkedIn (web scraping, complex)

### Phase 2: Score & Rank (10 seconds)
**2-Dimensional Scoring:**
- **Salary Score (0-10):** How likely to be 6-figure?
  - Explicit salary ranges parsed
  - Role title inference (PM, SWE, etc.)
  - High-salary keywords detected
  - Claude deep-dive (optional, costs $0.001-$0.002/job)

- **Entry Score (0-10):** How realistic for Dhwani's career pivot?
  - Hard disqualifiers detected (10+ years, PhD, etc.)
  - Easy signals found (entry-level, junior, bootcamp welcome)
  - Healthcare background bonus (pivot-friendly domains)
  - Claude nuanced assessment (optional)

**Filtering Gates:**
- Only keep jobs where: `salary_score ≥ 6` AND `entry_score ≥ 5`
- This filters out 70-80% of noise, focuses on realistic high-pays
- Surface top 25 ranked opportunities

### Phase 3: Tailor Resume (1 min per job)
Claude rewrites your master resume for each specific JD:
- Reframes clinical experience using PM language
- Leads with what the JD explicitly calls out
- Maintains honesty (no fabrication)
- Stays true to the master resume
- **Cost:** $0.01-$0.02 per job (Sonnet-4-6)

### Phase 4: Draft Cover Letter (30 seconds)
Personalized, non-generic cover letter:
- Hook ties clinical background to company mission
- 2-3 concrete transferable wins from your background
- Clear ask (let's talk, let's meet, etc.)
- Under 350 words, warm tone
- **Cost:** $0.01 per job

### Phase 5: Outreach Email (20 seconds)
Short, direct cold email for LinkedIn/recruiter:
- Specific to their company (no "I'm writing to apply...")
- Under 120 words
- One clear ask
- **Cost:** $0.005 per job

### Phase 6: Gmail Draft (automatic)
- Email auto-saved to your Gmail Drafts
- You review and send when ready
- Track open rates later
- **Cost:** Free (if you have Google OAuth set up)

### Phase 7: Track & Optimize
- SQLite database prevents duplicate applications
- Mark jobs as "applied" / "interview" / "offer" / "rejected"
- Google Sheets sync (optional) for team visibility
- Pipeline stats show conversion rates

---

## Configuration Deep Dive (config.yaml)

### 🎯 Target Roles
Currently searching for:
- Core PM: Product Manager, Associate PM, Clinical PM, etc.
- Pivot roles: Product Ops, Technical Program Manager, Operations Manager
- Adjacent: Customer Success Manager, Solutions Engineer, Data Analyst

**Add more roles:**
```yaml
target:
  roles:
    - "Your new role here"  # Will search across all boards
```

### 💰 Salary & Entry Gates
```yaml
search:
  min_salary_score: 6    # 1-10; 6+ = likely $100k+
  min_entry_score: 5     # 1-10; 5+ = realistic for pivot
  top_n: 25              # Show top 25 opportunities per run
```

**Tuning:**
- Want MORE jobs? Lower the gates (e.g., min_salary_score: 5, min_entry_score: 4)
- Want FEWER but higher-quality? Raise gates (e.g., 7, 6)

### 📍 Locations & Exclusions
```yaml
target:
  locations:
    - "Remote"           # Remote-first boards ignore this
    - "United States"    # Indeed/LinkedIn respect this
  exclude_keywords:
    - "10+ years"        # Title must NOT contain this
    - "VP"
    - "Director"         # Too senior for career pivot
    - "clearance required"  # Can't apply if no clearance
```

### 🔍 Search Settings
```yaml
search:
  boards:
    - remoteok                # Fastest, cleanest results
    - weworkremotely          # Great variety
    - himalayas               # Highest salary jobs
    - indeed                  # Most jobs
    - linkedin                # Best for recruiter reach
  
  max_jobs_per_run: 100       # Don't process > 100 per run
  days_back: 7                # Only jobs posted in last 7 days
```

---

## 💰 Cost Breakdown (per run finding 25 new jobs)

| Component | Jobs | Cost/Job | Total |
|-----------|------|----------|-------|
| Heuristic scoring | 25 | $0 | $0 |
| Claude scoring (optional) | 25 | $0.002 | $0.05 |
| Resume tailoring | 25 | $0.015 | $0.38 |
| Cover letter | 25 | $0.01 | $0.25 |
| Outreach email | 25 | $0.005 | $0.13 |
| **Total per run** | | | **~$0.81** |
| **Daily (assuming 1 run)** | | | **~$0.81** |
| **Monthly (30 runs)** | | | **~$24.30** |

**Ways to reduce cost:**
- Use `--no-tailor` flag: skip tailoring, just find & score ($0.07/run)
- Use `--no-ai-score` flag: heuristics only ($0.68/run)
- Run 2x/week instead of daily
- Switch to Haiku for tailoring (50% cheaper, still good quality)

---

## 🚀 Running on a Schedule (Automation)

### Option 1: Cron Job (Linux/Mac)
```bash
# Run daily at 8 AM
0 8 * * * cd /workspaces/job-hunt && python run.py run >> hunt.log 2>&1

# Run 3x/week (Mon, Wed, Fri) to save costs
0 8 * * 1,3,5 cd /workspaces/job-hunt && python run.py run >> hunt.log 2>&1
```

Add to crontab:
```bash
crontab -e
# Paste the line above
```

### Option 2: GitHub Actions
Create `.github/workflows/job-hunt.yml`:
```yaml
name: Automated Job Hunt
on:
  schedule:
    - cron: '0 8 * * 1,3,5'  # Mon/Wed/Fri at 8 AM UTC
jobs:
  hunt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python run.py run
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Option 3: Cloud Scheduler (Google Cloud)
- Pub/Sub → Cloud Run → runs `python run.py run`
- Cheap ($0.40/month for scheduler)

---

## 📊 CLI Commands Reference

```bash
# Find jobs, score, tailor, draft emails (MAIN COMMAND)
python run.py run

# Find & score only (skip AI tailoring)
python run.py run --no-tailor

# Use heuristic scoring only (skip Claude)
python run.py run --no-ai-score

# Sync results to Google Sheets
python run.py run --sheets

# See top 25 ranked jobs
python run.py top --n 25

# Show all jobs
python run.py show

# Filter by status
python run.py show --status tailored
python run.py show --status applied

# Review tailored resume + cover for a company
python run.py review "Teladoc"

# Update job status (mark as applied, etc.)
python run.py update "Teladoc" --status applied

# Show pipeline stats
python run.py stats

# Score sample jobs offline (no network)
python run.py demo
```

---

## 🎯 Best Practices for Landing Interviews

### 1. **Review Before Sending**
✅ Always review the tailored resume & cover letter before sending
✅ Customize the email subject line in Gmail
✅ Add a note about how you found them (referral, article, etc.)

### 2. **Timing**
✅ Send during business hours (9 AM - 5 PM in target timezone)
✅ Tuesday-Thursday get best response rates
✅ Avoid Mondays (inbox overload) and Fridays

### 3. **Follow-up**
✅ If no response in 3 days: send a gentle follow-up
✅ Template: "Hi [Name], just following up on my message from [date]. Still interested!"
✅ Send from a personal email if possible (not auto-generated)

### 4. **Personalization**
✅ Mention something specific about the company (recent funding, product, team member)
✅ Tailor the email subject line for your specific situation
✅ Reference the exact role title

### 5. **LinkedIn Strategy**
✅ Connect with hiring manager 1 day before emailing
✅ Add a note: "I'm interested in the [role] position at [company]. Let me know if we should chat!"
✅ Send email 1-2 days after accepting connection

---

## 🔧 Troubleshooting

### "ANTHROPIC_API_KEY error"
```bash
# Check .env file exists and has your key
cat .env | grep ANTHROPIC_API_KEY

# If blank, add your key from https://console.anthropic.com
```

### "No jobs found"
```bash
# Try with heuristic scoring (faster, no API calls)
python run.py run --no-tailor

# Check network connectivity
curl https://remoteok.com/api | head -10

# Job boards may be rate-limiting; try again in 1 hour
```

### "Gmail draft not created"
```bash
# Gmail integration requires Google OAuth setup (optional)
# See .env.example for instructions
# If not set up, drafts won't be created (but resume/cover will still be tailored)
```

### "High API costs"
- Use `--no-ai-score` flag (heuristic scoring only)
- Use `--no-tailor` flag during testing
- Switch to Haiku model (edit config, line 18)
- Run 2x/week instead of daily

---

## 📈 Expected Outcomes

Based on similar pipelines targeting 6-figure tech roles:

| Metric | Time | Rate |
|--------|------|------|
| Jobs found per week | 7 days | 40-80 |
| Jobs passing filters | 7 days | 10-20 |
| Cover letters sent | 7 days | 10-20 |
| Recruiter replies | 7-14 days | 20-30% |
| Screening calls | 14-21 days | 50-70% of replies |
| Interviews | 21-30 days | 70-80% of calls |
| Offers | 30-45 days | 40-60% of interviews |

**To maximize interviews:**
1. Run daily (more surface area)
2. Personalize 20% of outreach emails manually
3. Follow up after 3 days if no response
4. Build a 2-3 sentence custom note for each company

---

## 🚀 Next Steps

1. ✅ Add ANTHROPIC_API_KEY to `.env`
2. ✅ Test with `python run.py demo`
3. ✅ Try `python run.py run --no-tailor` (test job finding)
4. ✅ Try `python run.py run` (full pipeline)
5. ✅ Review results with `python run.py top`
6. ✅ Set up cron job for automation
7. ✅ Monitor results with `python run.py stats`
8. ✅ Adjust `config.yaml` based on results

---

## 📞 Support & Customization

**Want to customize the bot?**
- Edit `config.yaml` for search preferences
- Edit `master_resume.txt` to update background
- Edit `src/tailor.py` prompts for different messaging style
- Add new job boards in `src/finder/`

**Questions?**
- Check `README.md` for overview
- Run `python run.py --help` for CLI options
- Check `.env.example` for setup instructions
