#!/bin/bash
echo "🚀 Build process started..."

# Pip আপডেট
python -m pip install --upgrade pip

# Build dependencies
python -m pip install --upgrade setuptools wheel

# Install requirements
pip install -r requirements.txt

# NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

echo "✅ Build completed!"
