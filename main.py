"""
Cyber AI Assistant API
Minimal version - 100% কাজ করবে
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import sys
from datetime import datetime

# FastAPI app তৈরি
app = FastAPI(
    title="Cyber AI Assistant",
    description="AI-powered Cyber Security Learning Assistant",
    version="1.0.0"
)

@app.get("/")
async def home():
    """Home endpoint"""
    return JSONResponse({
        "app": "Cyber AI Assistant",
        "status": "active",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "python_version": sys.version,
        "timestamp": datetime.now().isoformat()
    })

@app.get("/ask")
async def ask(q: str = None):
    """Ask question endpoint"""
    if not q:
        return JSONResponse({
            "error": "No question provided",
            "example": "/ask?q=What is SQL injection?"
        }, status_code=400)
    
    # Simple response
    return JSONResponse({
        "question": q,
        "answer": f"Your question: '{q}' has been received. API is working correctly!",
        "mode": "simple",
        "timestamp": datetime.now().isoformat()
    })

@app.get("/sites")
async def sites():
    """List learning sites"""
    return JSONResponse({
        "sites": [
            {"name": "PortSwigger", "url": "https://portswigger.net"},
            {"name": "OWASP", "url": "https://owasp.org"},
            {"name": "Hacksplaining", "url": "https://www.hacksplaining.com"}
        ],
        "count": 3
    })

@app.get("/about")
async def about():
    """About endpoint"""
    return JSONResponse({
        "app": "Cyber AI Assistant",
        "developer": "Khaled Mahmud",
        "description": "AI powered Cyber Security learning assistant",
        "version": "1.0.0"
    })

# Direct run
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
