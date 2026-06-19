# 🚀 Job Hunt Bot - Optimization & Advanced Configuration

## 🎯 Cost Optimization (Critical)

### Scenario 1: Maximum Savings (Budget Mode)
Use heuristic scoring + Haiku model for everything:
```bash
# In .env:
HEURISTIC_SCORING_ONLY=true
TAILOR_MODEL=claude-haiku-4-5-20251001
COVER_MODEL=claude-haiku-4-5-20251001
OUTREACH_MODEL=claude-haiku-4-5-20251001

# Cost per run (25 jobs): ~$0.15 (vs $0.81 normal)
# Monthly (30 runs): ~$4.50 (vs $24 normal)
```

**Trade-off:** Resume tailoring quality drops ~10-15%, but still solid for initial screening.

### Scenario 2: Balanced (Recommended)
Use AI scoring (Haiku) + Sonnet for resumes only:
```bash
# In .env:
TAILOR_MODEL=claude-sonnet-4-6
COVER_MODEL=claude-haiku-4-5-20251001
OUTREACH_MODEL=claude-haiku-4-5-20251001

# Cost per run (25 jobs): ~$0.50
# Monthly: ~$15
```

**Best for:** Budget-conscious but quality-focused.

### Scenario 3: Premium (Best Results)
Use Sonnet everywhere (current default):
```bash
# In .env:
TAILOR_MODEL=claude-sonnet-4-6
COVER_MODEL=claude-sonnet-4-6
OUTREACH_MODEL=claude-haiku-4-5-20251001

# Cost per run (25 jobs): ~$0.81
# Monthly: ~$24
```

**Best for:** When quality/interview rate matters most.

---

## 🛡️ Error Handling & Reliability

### Automatic Retry Logic
Both `src/scorer.py` and `src/tailor.py` now include:
- **Exponential backoff** for rate limits (1s, 2s, 4s...)
- **Graceful degradation**: Falls back to heuristics if API fails
- **Max 3 retries** before giving up

Example flow:
```
Rate limited → Wait 1s → Retry
↓ Still failed → Wait 2s → Retry
↓ Still failed → Wait 4s → Retry
↓ Still failed → Use heuristic scoring
```

### Monitoring API Usage
Track spending with:
```bash
# Add to cron job to log costs
python run.py run 2>&1 | grep -E "Cost|API|Error" >> hunt-costs.log

# See total monthly spend
cat hunt-costs.log | grep Cost | awk '{sum+=$NF} END {print "Total: $" sum}'
```

---

## 📊 Performance Tuning

### Speed Optimization
If searches are too slow:
```yaml
# config.yaml - search section
search:
  boards:
    - remoteok              # Fast (< 5s)
    - weworkremotely        # Medium (5-10s)
    # - himalayas           # Comment out if slow
    # - indeed              # Comment out if slow
    # - linkedin            # Very slow, optional
```

### Memory Optimization
For running on limited systems:
```bash
# Process jobs in smaller batches
python run.py run --max-jobs-per-run 50

# Score only (skip tailoring)
python run.py run --no-tailor
```

---

## 🔗 Adding New Job Boards

### Template: Create a New Finder
Location: `src/finder/your_board.py`

```python
"""
Your Board Name — description of API/scraping method
"""
import requests
from typing import List
from src.models import Job
from src.finder.base import BaseFinder

class YourBoardFinder(BaseFinder):
    """Scrapes jobs from Your Board."""
    
    def search(self, query: str, location: str = "Remote", days_back: int = 7) -> List[Job]:
        """
        Args:
            query: Job title to search (e.g., "Product Manager")
            location: Job location (e.g., "Remote", "San Francisco")
            days_back: Only return jobs posted in last N days
        
        Returns:
            List of Job objects
        """
        try:
            # 1. Make API request or scrape
            jobs_raw = []  # Your scraping logic here
            
            # 2. Parse and convert to Job objects
            jobs = []
            for item in jobs_raw:
                job = Job(
                    title=item.get('title', ''),
                    company=item.get('company', ''),
                    location=item.get('location', 'Remote'),
                    url=item.get('url', ''),
                    source='your_board',
                    salary=item.get('salary', ''),
                    description=item.get('description', ''),
                    posted_date=item.get('posted_date', ''),
                )
                jobs.append(job)
            
            return jobs
        except Exception as exc:
            print(f"  [your_board] error: {exc}")
            return []
```

### Integration Steps
1. Create file at `src/finder/your_board.py`
2. Import in `src/orchestrator.py`:
   ```python
   from src.finder.your_board import YourBoardFinder
   ```
3. Add to `FINDER_MAP`:
   ```python
   FINDER_MAP = {
       # ... existing boards
       "your_board": YourBoardFinder,
   }
   ```
4. Add to `config.yaml`:
   ```yaml
   search:
     boards:
       - your_board
       - remoteok
       # ... rest
   ```

### Boards to Consider Adding
- **AngelList**: `https://angel.co/api/v1/jobs` (startup jobs, high salary)
- **Levels.fyi**: Role-based salaries, good for validation
- **Reworld**: Tech-specific job board
- **CrunchBoard**: Startup job board
- **We Love Startups**: Startup talent network

---

## 🎯 Interview Preparation Module (Coming Soon)

### Sample Interview Prep Script
Create `src/interview_prep.py`:

```python
"""Generate interview prep materials based on company research."""

from anthropic import Anthropic

def generate_prep_materials(company_name: str, role: str) -> dict:
    """Generate STAR stories, common questions, and talking points."""
    
    client = Anthropic()
    
    # Research the company
    company_prompt = f"""Research {company_name}'s:
    1. Recent news/funding
    2. Product strategy
    3. Typical PM interview questions for {role}
    4. 3 STAR stories Dhwani should tell (from clinical background)"""
    
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": company_prompt}]
    )
    
    return {
        "company": company_name,
        "role": role,
        "prep": msg.content[0].text
    }
```

Usage:
```bash
python -c "from src.interview_prep import generate_prep_materials; print(generate_prep_materials('Teladoc', 'Senior PM'))"
```

---

## 📱 LinkedIn Outreach Strategy

### Programmatic LinkedIn Connection
1. Connect with hiring manager 1 day before email
2. Personalized connection message (if possible)
3. Email 1-2 days after connection accepted

### Manual Workflow
```bash
# Get all contacts at target companies
python run.py show | grep "Company Name" | awk '{print $NF}' | sort -u

# For each, go to LinkedIn:
# 1. Find hiring manager
# 2. Connect + custom message
# 3. Check application inbox next day
```

---

## 📈 Tracking & Analytics

### View Your Progress
```bash
# Current stats
python run.py stats

# Jobs by company
python run.py show | sort -k 3

# Top performers (highest scoring)
python run.py top --n 50

# Jobs you've applied to
python run.py show --status applied

# Scheduled interviews
python run.py show --status interview
```

### Create a Dashboard (Google Sheets)
1. Run `python run.py run --sheets` (first time only)
2. Google Sheet auto-creates in Drive
3. Manually track: offers, rejections, interview feedback

### Email Open Tracking (Manual)
Use https://mailtrack.io or similar:
1. Reply to each opened email
2. Note response time
3. Track reply rate by company

---

## 🔐 Security Best Practices

### Credential Management
```bash
# NEVER commit .env to git
echo ".env" >> .gitignore

# Use separate keys for production vs development
export ANTHROPIC_API_KEY_DEV=sk-ant-...
export ANTHROPIC_API_KEY_PROD=sk-ant-...

# Rotate keys every 3 months
# Delete old keys from https://console.anthropic.com
```

### Safe Credential Storage
```bash
# Use environment variables, not files
# In GitHub Actions: Settings > Secrets > Add ANTHROPIC_API_KEY

# In cron: Store in /home/user/.env.secure (600 permissions)
chmod 600 /home/user/.env.secure
source /home/user/.env.secure && cd /workspaces/job-hunt && python run.py run
```

---

## 🐛 Troubleshooting Advanced Issues

### "Jobs found but no scoring"
```bash
# Check if Claude API is working
python -c "import anthropic; print(anthropic.__version__)"

# Test API manually
ANTHROPIC_API_KEY=your_key python -c "
from anthropic import Anthropic
client = Anthropic()
msg = client.messages.create(model='claude-haiku-4-5-20251001', max_tokens=10, messages=[{'role': 'user', 'content': 'hi'}])
print(msg.content[0].text)
"
```

### "Rate limited constantly"
```bash
# Use batch scoring (cheaper)
python run.py run --no-ai-score  # Skip Claude, use heuristics

# Or use cheaper model
# In .env: TAILOR_MODEL=claude-haiku-4-5-20251001

# Or reduce jobs per run
# In config.yaml: max_jobs_per_run: 10
```

### "Gmail integration not working"
```bash
# Recreate credentials
rm -f credentials.json token.json

# Run any command that uses Gmail
python run.py run  # Will prompt for Google auth

# Or disable Gmail (keep everything else)
# In config.yaml: outreach.send_cold_emails: false
```

---

## 🚀 Deployment to Cloud

### Option 1: AWS Lambda + EventBridge
```yaml
# sam.yaml (AWS Serverless Application Model)
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2010-05-06
Resources:
  JobHuntFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: python3.12
      Handler: run.py:run
      Events:
        DailySchedule:
          Type: Schedule
          Properties:
            Schedule: 'cron(0 8 * * ? *)'  # 8 AM UTC daily
      Environment:
        Variables:
          ANTHROPIC_API_KEY: !Ref AnthropicAPIKey
```

Deploy:
```bash
sam build && sam deploy --guided
```

### Option 2: Google Cloud Run + Cloud Scheduler
```bash
# 1. Containerize
docker build -t gcr.io/your-project/job-hunt .

# 2. Push
docker push gcr.io/your-project/job-hunt

# 3. Deploy to Cloud Run
gcloud run deploy job-hunt \
  --image gcr.io/your-project/job-hunt \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-...

# 4. Schedule with Cloud Scheduler
gcloud scheduler jobs create pubsub job-hunt-daily \
  --schedule="0 8 * * *" \
  --topic job-hunt-trigger
```

### Option 3: Railway (Simple)
1. Push code to GitHub
2. Connect at https://railway.app
3. Set environment variables
4. Add cron job via Railway Cron extension

---

## 📞 Getting Help

- **API Issues**: Check https://console.anthropic.com (account/usage)
- **Job Boards Down**: Try `--no-tailor` to test with heuristics
- **GitHub Issues**: File at https://github.com/dhwanisoni10-source/job-hunt
