#!/bin/bash
# Render build script for Cyber AI API

echo "🚀 Starting build process..."

# Exit on error
set -e

# Print Python version
echo "📌 Python version:"
python --version

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Download NLTK data
echo "📥 Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /var/data
mkdir -p /var/data/logs
mkdir -p /var/data/cache

# Set permissions
chmod -R 755 /var/data

echo "✅ Build completed successfully!"
