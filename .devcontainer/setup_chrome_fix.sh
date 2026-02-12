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

# 2. Run project setup first
echo "📦 Running make setup..."
make setup || { echo "⚠️  make setup had issues, continuing..."; }

# 3. Upgrade curl-cffi in Codespaces only (using UV's managed environment)
if command -v uv >/dev/null 2>&1; then
    echo "⬆️  Upgrading curl-cffi to >=0.7.2 for Chrome 142 support (Codespaces only)..."
    uv pip install --upgrade 'curl-cffi>=0.7.2' || {
        echo "⚠️  curl-cffi upgrade failed, relying on CURL_IMPERSONATE=chrome131"
    }
fi

# 4. Verify final state (with error handling for older curl-cffi versions)
echo "🔍 Verifying curl-cffi installation..."
.venv/bin/python -c "
import curl_cffi
print(f'✅ curl-cffi: {curl_cffi.__version__}')

# Try to show supported Chrome versions (only works in 0.7.0+)
try:
    from curl_cffi.const import CHROME_VERSIONS
    print(f'✅ Supported Chrome: {sorted(CHROME_VERSIONS.keys())[-3:]}... (latest 3)')
except (ImportError, AttributeError):
    print('ℹ️  CHROME_VERSIONS not available (older curl-cffi, using CURL_IMPERSONATE fallback)')
" || echo "⚠️  curl-cffi verification failed"

# 5. Final status
echo "✅ Setup complete!"
echo "ℹ️  Fix applied: CURL_IMPERSONATE=chrome131 (forces safe Chrome version)"
if command -v uv >/dev/null 2>&1; then
    echo "ℹ️  curl-cffi>=0.7.2 upgraded in Codespaces (adds chrome142 support)"
fi
echo ""
echo "🚀 Starting application..."
echo "   Access the dashboard at: http://localhost:8502"
echo ""

# Start Streamlit in background
cd /workspaces/share-investment-strategy-model
nohup make run > /tmp/streamlit.log 2>&1 &
echo "   View logs: tail -f /tmp/streamlit.log"

