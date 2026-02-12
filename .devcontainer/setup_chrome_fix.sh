#!/bin/bash
set -e

echo "🔧 Setting up Chrome impersonation fix..."

# 1. Add environment variable to bashrc
echo 'export CURL_IMPERSONATE=chrome131' >> ~/.bashrc
echo "✅ Added CURL_IMPERSONATE to ~/.bashrc"

# 2. Run project setup
echo "📦 Running make setup..."
make setup

# 3. Upgrade curl-cffi
echo "⬆️  Upgrading curl-cffi..."
uv pip install --upgrade 'curl-cffi>=0.7.0' --index-url https://pypi.org/simple

# 4. Verify installation (safe version)
echo "🔍 Checking curl-cffi..."
python3 -c "
try:
    import curl_cffi
    print('✅ curl-cffi version:', curl_cffi.__version__)
    
    try:
        from curl_cffi.const import CHROME_VERSIONS
        print('✅ Supported Chrome versions:', list(CHROME_VERSIONS.keys()))
    except (ImportError, AttributeError):
        print('⚠️  CHROME_VERSIONS not available (using fallback chrome131)')
except ImportError:
    print('⚠️  curl-cffi not installed (skipping check)')
"

echo "✅ Setup complete!"
