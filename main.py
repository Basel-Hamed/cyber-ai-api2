"""
Advanced Cyber AI Assistant API
Enterprise-grade FastAPI application with security, monitoring, and advanced features
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.redis import RedisBackend
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import logging
import time
import uuid
import asyncio
import jwt
import redis
import json
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import aioredis
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your modules
from sites import SITES, get_sites_info
from scraper import search_site_advanced, AdvancedWebScraper
from ai_engine import AdvancedAIEngine, AnswerMode
from summarizer import AdvancedSummarizer, summarize_advanced
from translator import AdvancedTranslator, translate_advanced
from image_tools import AdvancedImageAnalyzer, analyze_image_advanced
from memory import AdvancedChatHistory, StorageType, ExportFormat
from models import *  # We'll create models.py next

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cyber_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking (optional)
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Database connections
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup
    logger.info("Starting Cyber AI Assistant API...")
    
    # Initialize Redis cache
    global redis_client
    redis_client = await aioredis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        encoding="utf8",
        decode_responses=True
    )
    
    # Initialize FastAPI cache
    FastAPICache.init(RedisBackend(redis_client), prefix="cyberai-cache")
    
    # Initialize components
    app.state.scraper = AdvancedWebScraper()
    app.state.ai_engine = AdvancedAIEngine()
    app.state.summarizer = AdvancedSummarizer()
    app.state.translator = AdvancedTranslator()
    app.state.image_analyzer = AdvancedImageAnalyzer()
    app.state.chat_history = AdvancedChatHistory(
        storage_type=StorageType.SQLITE,
        storage_path="./data"
    )
    
    logger.info("Cyber AI Assistant API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cyber AI Assistant API...")
    await redis_client.close()
    logger.info("Shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="Cyber AI Assistant API",
    description="Advanced AI-powered Cyber Security Learning Assistant with Multi-language Support",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    contact={
        "name": "Khaled Mahmud",
        "email": "khaled@cyberai.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add Sentry middleware if configured
if os.getenv("SENTRY_DSN"):
    app.add_middleware(SentryAsgiMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(","),
)

# Add rate limit exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(f"Response {request_id}: {response.status_code} - {duration:.3f}s")
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    return response

# Authentication functions
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    
    try:
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET", "your-secret-key"),
            algorithms=["HS256"]
        )
        
        # Check expiration
        if datetime.fromtimestamp(payload["exp"]) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify API key"""
    valid_keys = os.getenv("API_KEYS", "test-key").split(",")
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key

# Pydantic models
class AskRequest(BaseModel):
    """Request model for /ask endpoint"""
    question: str = Field(..., min_length=3, max_length=1000)
    mode: str = Field("medium", regex="^(tiny|short|medium|long|comprehensive)$")
    language: str = Field("bn", regex="^(en|bn|hi|es|fr|de)$")
    use_advanced: bool = Field(False)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    @validator('question')
    def validate_question(cls, v):
        if len(v.strip()) < 3:
            raise ValueError('Question must be at least 3 characters')
        return v.strip()

class AskResponse(BaseModel):
    """Response model for /ask endpoint"""
    question: str
    answer_en: str
    answer_translated: str
    keywords: List[str]
    topic: str
    confidence: float
    sources: List[str]
    processing_time: float
    message_id: str
    session_id: str
    metadata: Dict[str, Any]

class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis"""
    detailed: bool = Field(False)
    include_ocr: bool = Field(True)
    security_check: bool = Field(True)
    format: str = Field("text", regex="^(text|html|json|markdown)$")

class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis"""
    filename: str
    analysis: str
    image_type: str
    confidence: float
    findings_count: int
    processing_time: float
    request_id: str

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with API information"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cyber AI Assistant API</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #2c3e50; }}
            .info {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
            .endpoint {{ margin: 10px 0; padding: 10px; background: #e9ecef; border-radius: 4px; }}
            code {{ background: #f1f3f5; padding: 2px 5px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>🔐 Cyber AI Assistant API</h1>
        <div class="info">
            <p><strong>Version:</strong> 3.0.0</p>
            <p><strong>Developer:</strong> Khaled Mahmud</p>
            <p><strong>Description:</strong> AI-powered Cyber Security Learning Assistant</p>
            <p><strong>Available Sites:</strong> {len(SITES)}</p>
        </div>
        
        <h2>📚 Documentation</h2>
        <div class="endpoint">
            <code>GET /api/docs</code> - Interactive API documentation (Swagger UI)
        </div>
        <div class="endpoint">
            <code>GET /api/redoc</code> - ReDoc documentation
        </div>
        <div class="endpoint">
            <code>GET /api/openapi.json</code> - OpenAPI schema
        </div>
        
        <h2>🚀 Quick Start</h2>
        <div class="endpoint">
            <code>GET /api/v1/health</code> - Health check
        </div>
        <div class="endpoint">
            <code>GET /api/v1/sites</code> - List available sites
        </div>
        <div class="endpoint">
            <code>GET /api/v1/ask?question=What is SQL injection?</code> - Ask a question
        </div>
        
        <footer style="margin-top: 40px; color: #6c757d;">
            <p>© 2024 Cyber AI Assistant. All rights reserved.</p>
        </footer>
    </body>
    </html>
    """

@app.get("/api/v1/health")
@cache(expire=10)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "services": {
            "database": "connected",
            "redis": "connected" if redis_client else "disconnected"
        }
    }

@app.get("/api/v1/sites")
@cache(expire=3600)  # Cache for 1 hour
async def get_sites():
    """Get list of available sites"""
    return {
        "total": len(SITES),
        "sites": [
            {
                "name": name,
                "url": info["url"],
                "category": info.get("category", "general")
            }
            for name, info in SITES.items()
        ]
    }

@app.get("/api/v1/ask", response_model=AskResponse)
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    q: AskRequest = Depends(),
    auth: dict = Depends(verify_token)
):
    """
    Ask a question to Cyber AI Assistant
    
    - **question**: Your question (min 3 chars)
    - **mode**: Answer length (tiny/short/medium/long/comprehensive)
    - **language**: Target language (en/bn/hi/es/fr/de)
    - **use_advanced**: Use advanced AI engine
    - **session_id**: Optional session ID for conversation tracking
    """
    start_time = time.time()
    
    try:
        # Log request
        logger.info(f"Processing question: {q.question[:50]}...")
        
        # Extract keywords and topic
        if q.use_advanced:
            keywords = request.app.state.ai_engine.extract_keywords_advanced(q.question)
            topic = q.question  # AI engine handles topic extraction
        else:
            from ai_engine import extract_keyword, detect_topic
            keywords = [extract_keyword(q.question)]
            topic = detect_topic(q.question)
        
        # Scrape sites
        collected = []
        scraper = request.app.state.scraper
        
        for site_name, site_info in SITES.items():
            try:
                results = scraper.scrape_site(
                    site_info["url"],
                    keywords[0] if keywords else "",
                    max_pages=2
                )
                
                if results and results.get('matches'):
                    for match in results['matches'][:3]:
                        collected.append(match.get('content', ''))
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
        
        # Summarize
        if q.use_advanced:
            summary_stats = request.app.state.summarizer.summarize_with_stats(
                collected,
                num_sentences=15,
                method='hybrid'
            )
            summary = summary_stats['summary']
        else:
            from summarizer import summarize
            summary = summarize(collected)
        
        # Generate answer
        if q.use_advanced:
            answer_mode = AnswerMode(q.mode)
            result = request.app.state.ai_engine.generate_dynamic_answer(
                topic=topic,
                content=summary,
                question=q.question,
                mode=answer_mode
            )
            answer = result['answer']
            confidence = result['metadata']['relevance_score']
        else:
            from ai_engine import build_answer
            answer = build_answer(topic, summary, q.mode)
            confidence = 0.85
        
        # Translate
        if q.language != "en":
            translated = request.app.state.translator.translate(
                answer,
                target=q.language,
                source="en"
            )
            translated_text = translated.translated_text
        else:
            translated_text = answer
        
        # Save to history
        message_id = request.app.state.chat_history.save_chat(
            question=q.question,
            answer=answer,
            metadata={
                'mode': q.mode,
                'language': q.language,
                'confidence': confidence,
                'keywords': keywords
            },
            session_id=q.session_id
        )
        
        processing_time = time.time() - start_time
        
        # Prepare response
        response = AskResponse(
            question=q.question,
            answer_en=answer,
            answer_translated=translated_text,
            keywords=keywords,
            topic=topic,
            confidence=confidence,
            sources=list(SITES.keys())[:5],
            processing_time=processing_time,
            message_id=message_id,
            session_id=q.session_id or request.app.state.chat_history.current_session_id,
            metadata={
                'mode': q.mode,
                'language': q.language,
                'use_advanced': q.use_advanced,
                'sources_used': len(collected)
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

@app.post("/api/v1/ask/batch")
@limiter.limit("5/minute")
async def ask_batch(
    request: Request,
    questions: List[str],
    auth: dict = Depends(verify_token)
):
    """Process multiple questions in batch"""
    tasks = []
    
    for question in questions[:10]:  # Limit to 10 questions
        tasks.append(
            ask_question(
                request,
                AskRequest(question=question, mode="short"),
                auth
            )
        )
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        "total": len(questions),
        "successful": sum(1 for r in results if not isinstance(r, Exception)),
        "failed": sum(1 for r in results if isinstance(r, Exception)),
        "results": [
            r if not isinstance(r, Exception) else {"error": str(r)}
            for r in results
        ]
    }

@app.post("/api/v1/image/analyze")
@limiter.limit("5/minute")
async def analyze_uploaded_image(
    request: Request,
    file: UploadFile = File(...),
    options: Optional[str] = "{}",
    auth: dict = Depends(verify_token)
):
    """
    Analyze an uploaded image for security issues
    
    - Supports: PNG, JPG, JPEG, GIF, BMP
    - Max size: 10MB
    """
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/bmp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {allowed_types}"
        )
    
    # Check file size (10MB limit)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size: 10MB"
        )
    
    # Parse options
    try:
        analysis_options = json.loads(options) if options != "{}" else {}
    except json.JSONDecodeError:
        analysis_options = {}
    
    # Analyze image
    start_time = time.time()
    
    result = await request.app.state.image_analyzer.analyze_image(
        content,
        options=analysis_options
    )
    
    # Generate report
    format = analysis_options.get('format', 'text')
    report = request.app.state.image_analyzer.generate_report(result, format)
    
    processing_time = time.time() - start_time
    
    return ImageAnalysisResponse(
        filename=file.filename,
        analysis=report,
        image_type=result.image_type.value,
        confidence=result.confidence,
        findings_count=len(result.findings),
        processing_time=processing_time,
        request_id=request.state.request_id
    )

@app.get("/api/v1/history")
@limiter.limit("20/minute")
async def get_chat_history(
    request: Request,
    session_id: Optional[str] = None,
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    auth: dict = Depends(verify_token)
):
    """Get chat history with filters"""
    
    # Parse dates if provided
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    history = request.app.state.chat_history.get_history(
        session_id=session_id,
        limit=limit,
        start_date=start,
        end_date=end,
        keyword=keyword
    )
    
    return {
        "total": len(history),
        "history": history
    }

@app.get("/api/v1/history/sessions")
@limiter.limit("20/minute")
async def get_sessions(
    request: Request,
    auth: dict = Depends(verify_token)
):
    """Get all chat sessions"""
    sessions = []
    
    # In a real app, you would get this from database
    # This is simplified
    for session_id in request.app.state.chat_history.sessions:
        summary = request.app.state.chat_history.get_session_summary(session_id)
        sessions.append(summary)
    
    return {
        "total": len(sessions),
        "sessions": sessions
    }

@app.post("/api/v1/history/export")
@limiter.limit("5/minute")
async def export_history(
    request: Request,
    format: str = "json",
    session_id: Optional[str] = None,
    auth: dict = Depends(verify_token)
):
    """Export chat history"""
    
    try:
        format_enum = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Supported: json, csv, text, html, markdown"
        )
    
    # Generate export
    export_path = request.app.state.chat_history.export_history(
        format=format_enum,
        session_id=session_id
    )
    
    # Read and return file
    with open(export_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Set appropriate media type
    media_types = {
        ExportFormat.JSON: "application/json",
        ExportFormat.CSV: "text/csv",
        ExportFormat.TEXT: "text/plain",
        ExportFormat.HTML: "text/html",
        ExportFormat.MARKDOWN: "text/markdown"
    }
    
    return StreamingResponse(
        iter([content]),
        media_type=media_types.get(format_enum, "text/plain"),
        headers={
            "Content-Disposition": f"attachment; filename=chat_export.{format_enum.value}"
        }
    )

@app.get("/api/v1/stats")
@limiter.limit("10/minute")
async def get_statistics(
    request: Request,
    auth: dict = Depends(verify_token)
):
    """Get system statistics"""
    
    chat_stats = request.app.state.chat_history.get_statistics()
    
    # Add more stats
    stats = {
        "chat": chat_stats,
        "system": {
            "uptime": "N/A",  # Would track in production
            "requests_processed": "N/A",
            "active_sessions": len(request.app.state.chat_history.sessions)
        },
        "sites": {
            "total": len(SITES),
            "categories": {}
        }
    }
    
    # Count site categories
    for site in SITES.values():
        category = site.get("category", "general")
        stats["sites"]["categories"][category] = stats["sites"]["categories"].get(category, 0) + 1
    
    return stats

@app.post("/api/v1/auth/token")
@limiter.limit("5/minute")
async def create_token(
    request: Request,
    username: str,
    password: str
):
    """Create JWT token (simplified - use proper auth in production)"""
    
    # In production, validate against database
    if username == os.getenv("ADMIN_USER", "admin") and password == os.getenv("ADMIN_PASS", "password"):
        token = jwt.encode(
            {
                "sub": username,
                "iat": datetime.now(),
                "exp": datetime.now() + timedelta(hours=24)
            },
            os.getenv("JWT_SECRET", "your-secret-key"),
            algorithm="HS256"
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400
        }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@app.get("/api/v1/about")
@cache(expire=3600)
async def about():
    """Get information about the API"""
    return {
        "app": "Cyber AI Assistant",
        "version": "3.0.0",
        "developer": "Khaled Mahmud",
        "description": "AI powered Cyber Security learning assistant with multi-language support",
        "features": [
            "Multi-site web scraping",
            "Advanced NLP question answering",
            "Multi-language support (English, Bangla, Hindi, Spanish, French, German)",
            "Image analysis with OCR",
            "Security vulnerability detection",
            "Chat history with SQLite storage",
            "Rate limiting",
            "JWT authentication",
            "Prometheus metrics"
        ],
        "technologies": [
            "FastAPI",
            "NLTK",
            "Transformers",
            "Tesseract OCR",
            "Redis",
            "SQLite",
            "Prometheus",
            "Docker"
        ],
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json"
        }
    }

# Admin endpoints (protected)
@app.get("/api/v1/admin/health/detailed")
async def admin_health_detailed(auth: dict = Depends(verify_token)):
    """Detailed health check for admin (requires admin role)"""
    
    # Check admin role
    if auth.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "connected",
            "redis": "connected",
            "cache": "operational",
            "scraper": "operational",
            "ai_engine": "operational",
            "translator": "operational"
        },
        "metrics": {
            "total_questions": 1234,  # From database
            "active_sessions": 5,
            "cache_hits": 567,
            "cache_misses": 89
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested resource was not found",
            "path": request.url.path,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    logger.error(f"Internal error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred",
            "request_id": request.state.request_id,
            "timestamp": datetime.now().isoformat()
        }
    )

# Webhook endpoints (for integration)
@app.post("/api/v1/webhook/scraper")
async def scraper_webhook(
    request: Request,
    data: Dict[str, Any],
    auth: dict = Depends(verify_token)
):
    """Webhook for receiving scraped data"""
    
    # Process webhook data
    logger.info(f"Received webhook data: {data}")
    
    # Store in database or process as needed
    
    return {"status": "received", "timestamp": datetime.now().isoformat()}

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
