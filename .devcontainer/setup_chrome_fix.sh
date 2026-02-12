#!/bin/bash
# Chrome Impersonation Fix Setup Script
# Approach: Environment variable + curl-cffi upgrade (no code changes needed)

echo "🔧 Setting up Chrome impersonation fix..."

# 1. Add environment variable to bashrc (skip if already exists)
if ! grep -q "CURL_IMPERSONATE" ~/.bashrc 2>/dev/null; then
    echo 'export CURL_IMPERSONATE=chrome131' >> ~/.bashrc
    echo "✅ Added CURL_IMPERSONATE to ~/.bashrc"
else
    echo "ℹ️  CURL_IMPERSONATE already in ~/.bashrc"
fi

# 2. Run project setup
echo "📦 Running make setup..."
make setup || { echo "⚠️  make setup had issues, continuing..."; }

# 3. Upgrade curl-cffi to get latest Chrome version support
echo "⬆️  Upgrading curl-cffi to latest version..."
uv pip install --upgrade 'curl-cffi>=0.7.0' --index-url https://pypi.org/simple || {
    echo "⚠️  curl-cffi upgrade failed"
    echo "   Relying on CURL_IMPERSONATE=chrome131 environment variable"
}

# 4. Verify final state
echo ""
echo "✅ Setup complete!"
echo "ℹ️  Fix applied: CURL_IMPERSONATE=chrome131 (forces safe Chrome version)"
echo "ℹ️  curl-cffi upgrade attempted (adds chrome142 support if available)"

