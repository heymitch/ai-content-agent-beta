#!/bin/bash
# Replit Deployment Script
# Clears Python cache and prepares for clean restart

echo "🧹 Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Cache cleared!"
echo ""
echo "📋 Next steps for Replit:"
echo "1. Stop the current process (Ctrl+C or click Stop)"
echo "2. Click the Run button to restart with fresh code"
echo ""
echo "🔍 Verify deployment by checking logs for:"
echo "   - '📨 Sending query to Claude SDK...' (NEW)"
echo "   - '📎 Including N file(s) in message' (NEW)"
echo ""
echo "   Should NOT see:"
echo "   - '🖼️ Sending multimodal message' (OLD)"
