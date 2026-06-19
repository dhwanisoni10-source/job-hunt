#!/usr/bin/env bash
# One-time setup — run this first
set -e

echo "==> Setting up job hunt system..."

# Check Python
python3 --version

# Install dependencies
pip install -r requirements.txt

# Copy env template if .env doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "✏️  Edit .env and add your ANTHROPIC_API_KEY"
    echo "   Get one at: https://console.anthropic.com"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Add ANTHROPIC_API_KEY to .env"
echo "  2. (Optional) Add Google credentials for Gmail/Sheets — see .env.example"
echo "  3. Edit config.yaml to adjust your target roles and locations"
echo "  4. Run: python run.py run --no-tailor   (to test job finding first)"
echo "  5. Run: python run.py run               (full pipeline with AI tailoring)"
