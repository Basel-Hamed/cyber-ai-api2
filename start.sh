#!/bin/bash
# Render start script for Cyber AI API

echo "🚀 Starting Cyber AI API..."

# Set environment variables
export PYTHONUNBUFFERED=1

# Print environment info
echo "📌 Environment: $ENVIRONMENT"
echo "📌 Port: $PORT"

# Run database migrations if needed
echo "🔄 Initializing database..."

# Start the application with uvicorn
echo "🚀 Starting server..."
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-10000} \
    --workers 1 \
    --log-level info \
    --proxy-headers \
    --forwarded-allow-ips '*'
