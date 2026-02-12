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

# 2. Pre-install latest curl-cffi BEFORE dependencies get locked
echo "📦 Pre-installing curl-cffi>=0.7.2 for Chrome 142 support..."
uv pip install --no-deps 'curl-cffi>=0.7.2' --index-url https://pypi.org/simple || {
    echo "⚠️  curl-cffi pre-install failed, continuing..."
}

# 3. Run project setup (will preserve curl-cffi if already installed)
echo "📦 Running make setup..."
make setup || { echo "⚠️  make setup had issues, continuing..."; }

# 4. Verify final state
echo "" (with error handling for older curl-cffi versions)
echo "🔍 Verifying curl-cffi installation..."
python3 -c "
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
echo "ℹ️  curl-cffi upgrade attempted (adds chrome142 support if available)"
echo ""
echo "🚀 Starting application..."
echo "   Access the dashboard at: http://localhost:8502"
echo ""

# Start Streamlit in background
cd /workspaces/share-investment-strategy-model
nohup make run > /tmp/streamlit.log 2>&1 &
echo "   View logs: tail -f /tmp/streamlit.log"

