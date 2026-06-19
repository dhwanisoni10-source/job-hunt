#!/usr/bin/env bash
# One-time setup — run this first
set -e

echo "==> Setting up job hunt system..."

# Check Python
python3 --version

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for auto-apply)
python -m playwright install chromium

# Copy env template if .env doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "✏️  Edit .env and fill in your keys (see .env.example for instructions)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add ANTHROPIC_API_KEY to .env (required for AI tailoring)"
echo "  2. Add LINKEDIN_EMAIL + LINKEDIN_PASSWORD to .env (required for auto-apply)"
echo "  3. (Optional) Add Google credentials for Gmail/Sheets sync"
echo "  4. Run: python run.py run           — find + tailor + create Gmail drafts"
echo "  5. Run: python run.py apply         — auto-apply to tailored jobs via browser"
echo "  6. Run: python run.py apply --dry-run  — test the browser flow without submitting"
