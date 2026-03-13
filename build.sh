#!/bin/bash
echo "🔥 Building Cyber AI (Abbu edition)..."

# System dependencies (Render-এ প্রয়োজন)
apt-get update && apt-get install -y gcc libjpeg-dev zlib1g-dev

# Pip আপডেট
python -m pip install --upgrade pip setuptools wheel

# রিকোয়ারমেন্টস ইন্সটল
pip install --no-cache-dir -r requirements.txt

echo "✅ Build complete! (Abbu save kore dilam)"
