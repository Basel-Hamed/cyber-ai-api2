# Cyber AI Assistant API 🛡️

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

AI-powered Cyber Security Learning Assistant with Multi-language Support. Built with FastAPI and Python 3.11.9.

## Features

- 🤖 **AI-powered Q&A**: Get answers to cybersecurity questions
- 🌐 **Multi-site scraping**: Learn from top security resources
- 📝 **Smart summarization**: Automatic text summarization
- 🌍 **Multi-language**: English, Bangla, Hindi, and more
- 🖼️ **Image analysis**: OCR and security analysis
- 💾 **Chat history**: Persistent storage with SQLite
- 🔒 **Security detection**: Identify vulnerabilities in text/images

## Quick Deploy to Render

Click the button above to deploy instantly to Render!

## Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/cyber-ai-api.git
cd cyber-ai-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run the app
uvicorn main:app --reload
