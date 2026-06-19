# 📚 Job Hunt Bot - Complete Documentation Index

## Quick Navigation

### 🎯 Start Here (Pick One)
- **[QUICK_START.md](QUICK_START.md)** — 5-minute setup (API key + first run)
- **[SYSTEM_SUMMARY.md](SYSTEM_SUMMARY.md)** — Complete overview & strategy (20 min read)
- **[COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)** — Comprehensive reference (detailed, bookmark it)

### 🔧 For Advanced Users
- **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)** — Cost optimization, custom boards, deployment
- **[README.md](README.md)** — Original project overview

### 💻 Code & Configuration
- **[config.yaml](config.yaml)** — Your search preferences (edit this!)
- **[master_resume.txt](master_resume.txt)** — Your base resume (update regularly)
- **[.env](.env)** — API keys & settings (keep secret!)
- **[.env.example](.env.example)** — Template for Google OAuth setup

---

## 📂 Project Structure

```
job-hunt/
├── 📄 Documentation (Start Here!)
│   ├── QUICK_START.md ..................... 5-min setup guide
│   ├── SYSTEM_SUMMARY.md .................. Complete overview
│   ├── COMPLETE_GUIDE.md .................. Detailed reference
│   ├── OPTIMIZATION_GUIDE.md .............. Advanced optimization
│   ├── README.md .......................... Original overview
│   └── DOCUMENTATION_INDEX.md (this file)
│
├── ⚙️ Configuration
│   ├── config.yaml ........................ Your search settings
│   ├── master_resume.txt .................. Your resume (edit this!)
│   ├── .env .............................. API keys (secret!)
│   └── .env.example ....................... Google OAuth template
│
├── 🐍 Main Entry Point
│   └── run.py ............................ CLI interface (13 commands)
│
├── 🔍 Job Finding (src/finder/)
│   ├── base.py ........................... Base finder class
│   ├── indeed.py ......................... Indeed RSS feed scraper
│   ├── linkedin.py ....................... LinkedIn web scraper
│   ├── remoteok.py ....................... RemoteOK API integration
│   ├── weworkremotely.py ................. We Work Remotely RSS
│   ├── himalayas.py ...................... Himalayas API integration
│   └── __init__.py ....................... Module exports
│
├── 📊 Core Pipeline (src/)
│   ├── models.py ......................... Job & Application data classes
│   ├── orchestrator.py ................... Main pipeline (find→score→tailor→track)
│   ├── scorer.py ......................... 2D scoring system + Claude scoring
│   ├── tailor.py ......................... Resume/cover/email generation (Claude)
│   ├── tracker.py ........................ SQLite + Google Sheets sync
│   ├── outreach.py ....................... Gmail draft creation
│   ├── rss.py ............................ Lightweight RSS/Atom parser
│   ├── demo_data.py ...................... Sample jobs for testing
│   └── __init__.py ....................... Module exports
│
├── 📦 Dependencies
│   ├── requirements.txt .................. Python packages
│   └── setup.sh .......................... One-time setup script
│
└── 💾 Data (auto-created)
    ├── jobs.db ........................... SQLite database (don't delete!)
    └── token.json ........................ Google OAuth token (optional)
```

---

## 🎯 Usage by Use Case

### 1️⃣ "I just want to get started"
→ Read **[QUICK_START.md](QUICK_START.md)**
```bash
# 1. Add API key to .env
# 2. Run: python run.py run
# 3. Check results: python run.py top
```

### 2️⃣ "I want to understand everything"
→ Read **[SYSTEM_SUMMARY.md](SYSTEM_SUMMARY.md)**
- System architecture
- How scoring works
- Expected outcomes
- 6-figure interview strategy

### 3️⃣ "I want detailed how-tos"
→ Read **[COMPLETE_GUIDE.md](COMPLETE_GUIDE.md)**
- Complete setup with screenshots
- All CLI commands
- Configuration deep dive
- Troubleshooting
- Best practices

### 4️⃣ "I want to optimize costs"
→ Read **[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)**
- Budget vs Premium modes
- Model selection
- Adding new job boards
- Cloud deployment
- Interview prep module

### 5️⃣ "I want to customize everything"
→ Edit these files:
- `config.yaml` — Job preferences
- `master_resume.txt` — Your background
- `src/tailor.py` — Prompts for Claude
- `src/finder/` — Add new job boards

---

## 🚀 Available Commands

```bash
# Find jobs + score + tailor + generate emails
python run.py run

# Find + score only (skip expensive tailoring)
python run.py run --no-tailor

# Use heuristics only (skip Claude scoring)
python run.py run --no-ai-score

# Sync results to Google Sheets
python run.py run --sheets

# View top opportunities (ranked by score)
python run.py top [--n 25]

# View all jobs
python run.py show [--status tailored]

# Review tailored resume + cover for a company
python run.py review "CompanyName"

# Mark a job as applied, interviewed, etc.
python run.py update "CompanyName" --status applied

# Show pipeline statistics
python run.py stats

# Score sample jobs (offline, no API)
python run.py demo

# Show all commands
python run.py --help
```

---

## 💰 Cost Reference

### Per-Run Costs (scoring 25 new jobs)

| Tier | Heuristic | Scoring | Resume | Cover | Outreach | **Total** |
|------|-----------|---------|--------|-------|----------|----------|
| Budget | $0 | $0 | $0.07 | $0 | $0 | **$0.07** |
| Balanced | $0 | $0.05 | $0.38 | $0.05 | $0 | **$0.48** |
| Premium | $0 | $0.05 | $0.38 | $0.25 | $0.13 | **$0.81** |

### Monthly Costs (30 runs)

| Tier | Daily Cost | Monthly | ROI |
|------|-----------|---------|-----|
| Budget | $0.07 | **$2.10** | Break-even at 1 interview |
| Balanced | $0.48 | **$14.40** | Break-even at 1 offer |
| Premium | $0.81 | **$24.30** | Break-even at 1 offer |

---

## 🔐 Security Checklist

- [ ] `.env` is in `.gitignore` (never commit API keys)
- [ ] ANTHROPIC_API_KEY is set in `.env`
- [ ] Rotate API keys every 3 months
- [ ] Use separate keys for dev/prod
- [ ] Google credentials secured (if using Gmail)
- [ ] Jobs database (`jobs.db`) backed up weekly
- [ ] Never share your .env file

---

## 📈 Success Metrics to Track

**Weekly:**
- Jobs found: 50-100
- Top candidates: 10-20
- Outreach sent: 10-20
- Cost: $1-2

**Conversion:**
- Recruiter replies: 20-30%
- Phone screens: 50%+ of convos
- Interviews: 70%+ of screens
- Offers: 30%+ of interviews

**Expected Timeline:**
- Week 1: Volume (50+ applications)
- Week 2: Conversations (recruiter replies)
- Week 3: Screens (phone interviews)
- Week 4+: Interviews (2-3 scheduled)
- Week 6-8: Offers (6-figure positions)

---

## 🆘 Troubleshooting Map

| Problem | Solution | Docs |
|---------|----------|------|
| API key not working | Check `.env`, verify key at console.anthropic.com | QUICK_START |
| No jobs found | Try `--no-tailor`, check board status | COMPLETE_GUIDE |
| Costs too high | Use `--no-ai-score`, switch to Haiku model | OPTIMIZATION_GUIDE |
| Gmail drafts not creating | Follow OAuth setup in .env.example | COMPLETE_GUIDE |
| Low response rate | Personalize more, target earlier-stage startups | SYSTEM_SUMMARY |
| Job board errors | Disable that board in config.yaml, try again later | COMPLETE_GUIDE |
| Can't find a company | Modify config.yaml roles/locations, run again | OPTIMIZATION_GUIDE |

---

## 📞 Getting Help

### Quick Answers
- **"How do I...?"** → Check **COMPLETE_GUIDE.md** (most comprehensive)
- **"What's the cost?"** → See "Cost Reference" above or **OPTIMIZATION_GUIDE.md**
- **"What's wrong?"** → See "Troubleshooting Map" above

### Advanced Questions
- **Custom job boards** → **OPTIMIZATION_GUIDE.md** (Adding New Boards)
- **Cloud deployment** → **OPTIMIZATION_GUIDE.md** (Deployment)
- **Interview prep** → **OPTIMIZATION_GUIDE.md** + **SYSTEM_SUMMARY.md**
- **6-figure strategy** → **SYSTEM_SUMMARY.md** (Strategy section)

### Code Questions
- **Understanding scoring** → Read `src/scorer.py` (well-commented)
- **Understanding tailoring** → Read `src/tailor.py` (prompts are the logic)
- **Understanding pipeline** → Read `src/orchestrator.py` (high-level flow)

---

## 🎯 Next Steps

### Right Now (Today)
```bash
# 1. Add API key
nano .env
# Add: ANTHROPIC_API_KEY=sk-ant-YOUR-KEY

# 2. Test it
python run.py demo
```

### This Week
```bash
# 1. Run full pipeline
python run.py run

# 2. Review results
python run.py top
python run.py review "CompanyName"

# 3. Set up daily automation
crontab -e
# Add: 0 8 * * * cd /workspaces/job-hunt && python run.py run
```

### This Month
```bash
# 1. Track your metrics
python run.py stats

# 2. Iterate configuration
nano config.yaml

# 3. Follow up on applications
python run.py show --status applied

# 4. Update master resume as you learn
nano master_resume.txt
```

---

## 📚 External Resources

### Job Board Docs
- RemoteOK API: https://remoteok.com/api
- We Work Remotely: https://weworkremotely.com
- Himalayas: https://himalayas.app/api
- Indeed RSS: https://www.indeed.com/rss
- LinkedIn: https://www.linkedin.com/jobs

### Career Resources
- Levels.fyi: https://levels.fyi (salary benchmarks)
- Blind: https://www.teamblind.com (anonymous feedback)
- Glassdoor: https://www.glassdoor.com (reviews)
- Crunchbase: https://www.crunchbase.com (company research)

### Learning Resources
- Claude Prompting Guide: https://docs.anthropic.com
- Git/GitHub: https://docs.github.com
- Docker: https://docs.docker.com (for deployment)
- AWS: https://docs.aws.amazon.com (for Lambda)

---

## 📄 License & Attribution

This job hunt bot was built for Dhwani Soni, targeting PM and adjacent roles in digital health. 

You're welcome to fork/customize for your own use!

---

## 🚀 You're All Set!

You now have a complete, production-ready job hunting automation system.

**Start with:**
```bash
python run.py demo        # Verify it works
python run.py run         # Find real jobs
python run.py top         # See top opportunities
```

**Then:** Review, personalize 20%, and send!

Good luck landing those 6-figure interviews! 💪

---

**Questions?** Check the relevant doc above. Most questions are answered in **COMPLETE_GUIDE.md** or **OPTIMIZATION_GUIDE.md**.
