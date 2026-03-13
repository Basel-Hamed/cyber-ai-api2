"""
Cyber AI Assistant API
Advanced Version - No external AI, 100% rule-based but powerful
Developer: Khaled Mahmud
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import re
import json
import hashlib
import random
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import Counter
import urllib.parse

# Try to import optional libraries (but app works without them)
try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False
    print("⚠️ Scraping libraries not available. Using mock data.")

try:
    from deep_translator import GoogleTranslator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("⚠️ Translation libraries not available. Using English only.")

# ==================== CONFIGURATION ====================

class Config:
    APP_NAME = "Cyber AI Assistant"
    APP_VERSION = "3.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    MAX_KEYWORDS = 5
    MAX_SOURCES = 5
    CACHE_SIZE = 100
    REQUEST_TIMEOUT = 10

config = Config()

# ==================== DATA MODELS ====================

class SecurityTopic(str, Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    SSRF = "ssrf"
    AUTH_BYPASS = "authentication_bypass"
    FILE_UPLOAD = "file_upload_vulnerability"
    COMMAND_INJECTION = "command_injection"
    LDAP_INJECTION = "ldap_injection"
    XXE = "xxe"
    DESERIALIZATION = "insecure_deserialization"
    GENERAL = "general_security"

class AnswerMode(str, Enum):
    TINY = "tiny"      # 1-2 sentences
    SHORT = "short"    # short paragraph
    MEDIUM = "medium"  # detailed
    LONG = "long"      # very detailed
    COMPREHENSIVE = "comprehensive"  # complete guide

class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

# ==================== KNOWLEDGE BASE ====================

class CyberSecurityKnowledge:
    """Built-in cybersecurity knowledge base"""
    
    TOPICS = {
        "sql_injection": {
            "keywords": ["sql", "injection", "database", "query", "mysql", "postgresql", "oracle"],
            "name": "SQL Injection",
            "description": "SQL injection is a code injection technique that might destroy your database.",
            "explanation": """
SQL Injection occurs when an attacker inserts malicious SQL code into application queries.
This vulnerability allows attackers to:
• View restricted data
• Modify database contents
• Execute administrative operations
• Sometimes gain shell access

Example attack: ' OR '1'='1' --

Common vulnerable code:
username = request.POST['username']
password = request.POST['password']
query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
            """,
            "prevention": [
                "Use parameterized queries / prepared statements",
                "Use stored procedures",
                "Validate and sanitize all user inputs",
                "Escape special characters",
                "Use ORM frameworks",
                "Implement least privilege principle"
            ],
            "examples": [
                "' OR '1'='1",
                "admin' --",
                "'; DROP TABLE users; --",
                "' UNION SELECT username,password FROM users--"
            ],
            "risk": RiskLevel.CRITICAL,
            "cwe": "CWE-89",
            "owasp_rank": 1
        },
        
        "xss": {
            "keywords": ["xss", "cross site", "script", "javascript", "html injection"],
            "name": "Cross-Site Scripting (XSS)",
            "description": "XSS allows attackers to inject malicious scripts into web pages viewed by users.",
            "explanation": """
Cross-Site Scripting (XSS) enables attackers to inject client-side scripts into web pages.
Types of XSS:
• Reflected XSS: Script comes from current HTTP request
• Stored XSS: Script is stored on target server
• DOM-based XSS: Vulnerability in client-side code

Example attack:
<script>alert('XSS')</script>
<img src=x onerror=alert(1)>
<a href="javascript:alert('XSS')">Click me</a>
            """,
            "prevention": [
                "Implement Content Security Policy (CSP)",
                "Use output encoding/escaping",
                "Validate input on server side",
                "Use HTTP-only cookies",
                "Sanitize HTML input",
                "Use XSS protection headers"
            ],
            "examples": [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>"
            ],
            "risk": RiskLevel.HIGH,
            "cwe": "CWE-79",
            "owasp_rank": 2
        },
        
        "authentication": {
            "keywords": ["auth", "login", "password", "session", "jwt", "oauth", "bypass"],
            "name": "Authentication Bypass",
            "description": "Authentication bypass allows attackers to access systems without valid credentials.",
            "explanation": """
Authentication bypass vulnerabilities let attackers circumvent login mechanisms.
Common issues:
• Weak password policies
• Session fixation
• Insecure password recovery
• Missing brute-force protection
• JWT vulnerabilities (none algorithm, weak secrets)

Example vulnerable code:
if user.role == 'admin':
    grant_access()
            """,
            "prevention": [
                "Implement strong password policies",
                "Use multi-factor authentication (MFA)",
                "Secure session management",
                "Rate limiting on login attempts",
                "Proper JWT validation",
                "Secure password reset flows"
            ],
            "examples": [
                "JWT 'none' algorithm attack",
                "Session hijacking",
                "Brute force attacks",
                "Default credentials"
            ],
            "risk": RiskLevel.CRITICAL,
            "cwe": "CWE-287"
        },
        
        "file_upload": {
            "keywords": ["upload", "file", "attachment", "image upload", "file inclusion"],
            "name": "File Upload Vulnerabilities",
            "description": "Insecure file uploads can lead to remote code execution and other attacks.",
            "explanation": """
File upload vulnerabilities occur when applications don't properly validate uploaded files.
Attackers can upload:
• Malicious scripts (PHP, ASP, JSP)
• Overwriting existing files
• Malware for distribution
• Large files for DoS attacks

Example attack:
Upload a PHP file with: <?php system($_GET['cmd']); ?>
            """,
            "prevention": [
                "Validate file types (whitelist extensions)",
                "Scan files for malware",
                "Store files outside webroot",
                "Use random filenames",
                "Limit file size",
                "Check file content, not just extension"
            ],
            "examples": [
                "shell.php.jpg (double extension)",
                ".htaccess manipulation",
                "SVG with embedded scripts",
                "Zip bombs"
            ],
            "risk": RiskLevel.HIGH,
            "cwe": "CWE-434"
        },
        
        "ssrf": {
            "keywords": ["ssrf", "server side request", "url fetch", "internal network"],
            "name": "Server-Side Request Forgery (SSRF)",
            "description": "SSRF allows attackers to make requests from the vulnerable server to internal systems.",
            "explanation": """
SSRF vulnerabilities let attackers abuse server functionality to access internal resources.
Attackers can:
• Port scan internal networks
• Access cloud metadata endpoints
• Read internal files
• Bypass firewalls

Example attack:
http://169.254.169.254/latest/meta-data/ (AWS metadata)
file:///etc/passwd
            """,
            "prevention": [
                "Whitelist allowed URLs/domains",
                "Disable unnecessary URL schemas",
                "Validate and sanitize URLs",
                "Use network segmentation",
                "Block access to private IP ranges"
            ],
            "examples": [
                "AWS metadata endpoint",
                "Internal port scanning",
                "File protocol access",
                "Gopher protocol attacks"
            ],
            "risk": RiskLevel.HIGH,
            "cwe": "CWE-918"
        }
    }
    
    @classmethod
    def get_all_topics(cls):
        return list(cls.TOPICS.keys())
    
    @classmethod
    def get_topic_by_keywords(cls, text: str):
        """Find matching topic based on keywords"""
        text_lower = text.lower()
        matches = []
        
        for topic_id, topic_data in cls.TOPICS.items():
            score = 0
            for keyword in topic_data["keywords"]:
                if keyword in text_lower:
                    score += 1
            if score > 0:
                matches.append((topic_id, score))
        
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][0]
        
        return "general_security"
    
    @classmethod
    def get_explanation(cls, topic_id: str, mode: str = "medium"):
        """Get explanation based on mode"""
        if topic_id not in cls.TOPICS:
            return "Information not available."
        
        topic = cls.TOPICS[topic_id]
        
        if mode == "tiny":
            return topic["description"]
        elif mode == "short":
            return topic["explanation"][:500] + "..."
        elif mode == "medium":
            return topic["explanation"]
        elif mode == "long":
            return topic["explanation"] + "\n\nExamples:\n" + "\n".join([f"• {ex}" for ex in topic["examples"]])
        elif mode == "comprehensive":
            return topic["explanation"] + "\n\nExamples:\n" + "\n".join([f"• {ex}" for ex in topic["examples"]]) + \
                   "\n\nPrevention:\n" + "\n".join([f"• {p}" for p in topic["prevention"]])
        
        return topic["explanation"]

# ==================== AI ENGINE ====================

class CyberAIEngine:
    """Rule-based AI engine - no external APIs needed"""
    
    def __init__(self):
        self.knowledge = CyberSecurityKnowledge()
        self.conversation_history = []
        self.context_window = 5
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove common words
        stop_words = {'what', 'why', 'how', 'when', 'where', 'who', 'which', 'is', 'are', 
                      'was', 'were', 'will', 'shall', 'this', 'that', 'these', 'those',
                      'explain', 'define', 'tell', 'describe', 'about', 'with', 'from', 'have'}
        
        # Find words with 3+ letters
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stop words
        keywords = [w for w in words if w not in stop_words]
        
        # Count frequency
        keyword_freq = Counter(keywords)
        
        # Return top keywords
        return [k for k, v in keyword_freq.most_common(config.MAX_KEYWORDS)]
    
    def detect_topic(self, text: str) -> str:
        """Detect security topic from text"""
        return self.knowledge.get_topic_by_keywords(text)
    
    def generate_answer(self, question: str, mode: str = "medium") -> Dict[str, Any]:
        """Generate answer based on question"""
        
        # Extract keywords
        keywords = self.extract_keywords(question)
        
        # Detect topic
        topic_id = self.detect_topic(question)
        topic_data = self.knowledge.TOPICS.get(topic_id, {})
        
        # Get explanation
        explanation = self.knowledge.get_explanation(topic_id, mode)
        
        # Structure answer
        answer = {
            "question": question,
            "topic": topic_data.get("name", "General Security"),
            "topic_id": topic_id,
            "keywords": keywords,
            "explanation": explanation,
            "risk_level": topic_data.get("risk", RiskLevel.INFO).value,
            "prevention": topic_data.get("prevention", []),
            "examples": topic_data.get("examples", []),
            "cwe": topic_data.get("cwe", "N/A"),
            "confidence": self._calculate_confidence(keywords, topic_id)
        }
        
        # Add to history
        self.conversation_history.append({
            "question": question,
            "topic": topic_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history
        if len(self.conversation_history) > self.context_window:
            self.conversation_history = self.conversation_history[-self.context_window:]
        
        return answer
    
    def _calculate_confidence(self, keywords: List[str], topic_id: str) -> float:
        """Calculate confidence score"""
        if topic_id == "general_security":
            return 0.5
        
        topic = self.knowledge.TOPICS.get(topic_id, {})
        topic_keywords = topic.get("keywords", [])
        
        if not keywords or not topic_keywords:
            return 0.5
        
        matches = sum(1 for k in keywords if k in topic_keywords)
        return min(0.95, matches / len(keywords) + 0.5)
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history

# ==================== WEB SCRAPER ====================

class CyberScraper:
    """Advanced web scraper with parallel processing"""
    
    def __init__(self):
        self.sites = [
            {"name": "PortSwigger", "url": "https://portswigger.net/web-security", "category": "web"},
            {"name": "OWASP", "url": "https://owasp.org/www-community/", "category": "web"},
            {"name": "CVE Details", "url": "https://www.cvedetails.com/", "category": "vulnerabilities"},
            {"name": "Hacksplaining", "url": "https://www.hacksplaining.com/lessons", "category": "training"},
            {"name": "SANS Institute", "url": "https://www.sans.org/white-papers/", "category": "research"}
        ]
        self.cache = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    async def search(self, keywords: List[str], max_results: int = 5) -> List[Dict]:
        """Search across multiple sites in parallel"""
        if not SCRAPING_AVAILABLE:
            return self._get_mock_results(keywords)
        
        tasks = []
        async with aiohttp.ClientSession() as session:
            for site in self.sites[:config.MAX_SOURCES]:
                task = self._search_site(session, site, keywords)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter results
        all_results = []
        for res in results:
            if isinstance(res, list):
                all_results.extend(res)
        
        # Sort by relevance
        all_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return all_results[:max_results]
    
    async def _search_site(self, session, site: Dict, keywords: List[str]) -> List[Dict]:
        """Search individual site"""
        try:
            # Check cache
            cache_key = f"{site['url']}_{'_'.join(keywords)}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Make request
            async with session.get(site['url'], timeout=config.REQUEST_TIMEOUT) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract text
                    text = soup.get_text()
                    
                    # Calculate relevance
                    relevance = self._calculate_relevance(text, keywords)
                    
                    result = [{
                        "site": site['name'],
                        "url": site['url'],
                        "relevance": relevance,
                        "snippet": text[:500] + "...",
                        "category": site['category']
                    }]
                    
                    # Cache result
                    self.cache[cache_key] = result
                    return result
        except Exception as e:
            print(f"Error scraping {site['name']}: {e}")
        
        return []
    
    def _calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """Calculate text relevance to keywords"""
        text_lower = text.lower()
        matches = sum(1 for k in keywords if k in text_lower)
        return matches / len(keywords) if keywords else 0
    
    def _get_mock_results(self, keywords: List[str]) -> List[Dict]:
        """Get mock results when scraping unavailable"""
        results = []
        for site in self.sites[:3]:
            results.append({
                "site": site['name'],
                "url": site['url'],
                "relevance": random.uniform(0.5, 0.9),
                "snippet": f"Information about {', '.join(keywords)} from {site['name']}",
                "category": site['category'],
                "mock": True
            })
        return results

# ==================== TRANSLATOR ====================

class CyberTranslator:
    """Multi-language translator"""
    
    def __init__(self):
        self.cache = {}
        self.supported_languages = {
            "en": "English",
            "bn": "Bangla",
            "hi": "Hindi",
            "es": "Spanish",
            "fr": "French"
        }
    
    def translate(self, text: str, target: str = "bn") -> str:
        """Translate text to target language"""
        if not TRANSLATION_AVAILABLE or target == "en":
            return text
        
        # Check cache
        cache_key = f"{text}_{target}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Use deep-translator if available
            translator = GoogleTranslator(source='en', target=target)
            translated = translator.translate(text)
            self.cache[cache_key] = translated
            return translated
        except Exception as e:
            print(f"Translation error: {e}")
            # Mock translation for testing
            if target == "bn":
                return f"[বাংলা] {text[:200]}..."
            return text

# ==================== SUMMARIZER ====================

class CyberSummarizer:
    """Text summarization engine"""
    
    def summarize(self, text: str, max_sentences: int = 5) -> str:
        """Extract key sentences from text"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        if not sentences:
            return text[:300] + "..."
        
        # Return first few sentences
        summary = ". ".join(sentences[:max_sentences]) + "."
        
        if len(summary) > 1000:
            summary = summary[:1000] + "..."
        
        return summary

# ==================== IMAGE ANALYZER ====================

class CyberImageAnalyzer:
    """Basic image analyzer (mock)"""
    
    async def analyze(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Analyze image for security issues"""
        
        # Mock analysis result
        return {
            "filename": filename,
            "file_size": len(file_content),
            "analysis": """
🔍 CYBER AI IMAGE ANALYSIS

The uploaded image may contain:
• Code snippets
• Error messages
• Stack traces
• Configuration files

Security Recommendations:
• Review any visible credentials
• Check for exposed API keys
• Ensure no sensitive data is visible
• Verify code for vulnerabilities
            """,
            "findings": [
                "No immediate threats detected",
                "Manual review recommended",
                "Check for hardcoded secrets"
            ],
            "risk_level": "info"
        }

# ==================== MEMORY MANAGER ====================

class CyberMemory:
    """Chat history manager"""
    
    def __init__(self):
        self.sessions = {}
        self.max_sessions = 10
        self.max_messages_per_session = 50
    
    def add_message(self, session_id: str, question: str, answer: Dict):
        """Add message to history"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim if needed
        if len(self.sessions[session_id]) > self.max_messages_per_session:
            self.sessions[session_id] = self.sessions[session_id][-self.max_messages_per_session:]
        
        # Trim sessions if needed
        if len(self.sessions) > self.max_sessions:
            oldest = min(self.sessions.keys(), 
                        key=lambda k: self.sessions[k][0]["timestamp"] if self.sessions[k] else "")
            del self.sessions[oldest]
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get chat history"""
        if session_id not in self.sessions:
            return []
        
        return self.sessions[session_id][-limit:]
    
    def get_all_sessions(self) -> List[str]:
        """Get all session IDs"""
        return list(self.sessions.keys())

# ==================== FASTAPI APP ====================

# Initialize components
app = FastAPI(
    title="Cyber AI Assistant",
    description="Advanced AI-powered Cyber Security Learning Assistant (No External AI)",
    version="3.0.0",
    contact={
        "name": "Khaled Mahmud",
        "email": "khaled@cyberai.com",
    }
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_engine = CyberAIEngine()
scraper = CyberScraper()
translator = CyberTranslator()
summarizer = CyberSummarizer()
image_analyzer = CyberImageAnalyzer()
memory = CyberMemory()

# ==================== API ENDPOINTS ====================

@app.get("/")
async def home():
    """Home endpoint"""
    return {
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "developer": "Khaled Mahmud",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "ask": "/ask?q=your_question",
            "ask_advanced": "/ask/advanced?q=your_question&mode=medium&lang=bn",
            "sites": "/sites",
            "search": "/search?q=sql injection",
            "chat": "/chat/{session_id}",
            "image": "/image/analyze",
            "history": "/history/{session_id}",
            "topics": "/topics",
            "about": "/about"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "python_version": sys.version,
        "scraping_available": SCRAPING_AVAILABLE,
        "translation_available": TRANSLATION_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ask")
async def ask(
    q: str,
    mode: AnswerMode = AnswerMode.MEDIUM,
    lang: str = "en"
):
    """
    Ask a cybersecurity question
    
    - **q**: Your question
    - **mode**: Answer detail level (tiny, short, medium, long, comprehensive)
    - **lang**: Response language (en, bn, hi, es, fr)
    """
    if not q or len(q.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question must be at least 3 characters")
    
    start_time = time.time()
    
    # Generate answer
    answer_data = ai_engine.generate_answer(q, mode.value)
    
    # Translate if needed
    if lang != "en":
        answer_data["explanation"] = translator.translate(answer_data["explanation"], lang)
        answer_data["prevention"] = [translator.translate(p, lang) for p in answer_data["prevention"]]
    
    # Add metadata
    answer_data["processing_time"] = round(time.time() - start_time, 3)
    answer_data["language"] = lang
    
    return answer_data

@app.get("/ask/advanced")
async def ask_advanced(
    q: str,
    mode: AnswerMode = AnswerMode.MEDIUM,
    lang: str = "en",
    session_id: str = None,
    use_scraper: bool = True
):
    """
    Advanced question answering with web scraping
    
    - **q**: Your question
    - **mode**: Answer detail level
    - **lang**: Response language
    - **session_id**: Session ID for conversation tracking
    - **use_scraper**: Enable web scraping for additional info
    """
    start_time = time.time()
    
    # Generate base answer
    answer_data = ai_engine.generate_answer(q, mode.value)
    
    # Scrape additional info
    scraped_info = []
    if use_scraper and answer_data["keywords"]:
        scraped_info = await scraper.search(answer_data["keywords"])
    
    # Summarize scraped info
    if scraped_info:
        combined_text = " ".join([s.get("snippet", "") for s in scraped_info])
        scraped_summary = summarizer.summarize(combined_text, max_sentences=3)
        answer_data["additional_info"] = scraped_summary
        answer_data["sources"] = [s["site"] for s in scraped_info[:3]]
    
    # Translate
    if lang != "en":
        answer_data["explanation"] = translator.translate(answer_data["explanation"], lang)
        if "additional_info" in answer_data:
            answer_data["additional_info"] = translator.translate(answer_data["additional_info"], lang)
    
    # Save to memory
    if session_id:
        memory.add_message(session_id, q, answer_data)
    
    answer_data["processing_time"] = round(time.time() - start_time, 3)
    answer_data["language"] = lang
    answer_data["session_id"] = session_id
    
    return answer_data

@app.get("/sites")
async def sites():
    """List available learning sites"""
    return {
        "total": len(scraper.sites),
        "sites": scraper.sites
    }

@app.get("/search")
async def search(q: str, limit: int = 5):
    """Search across cybersecurity sites"""
    keywords = ai_engine.extract_keywords(q)
    results = await scraper.search(keywords, limit)
    
    return {
        "query": q,
        "keywords": keywords,
        "total": len(results),
        "results": results
    }

@app.get("/chat/{session_id}")
async def chat(
    session_id: str,
    q: str,
    mode: AnswerMode = AnswerMode.MEDIUM,
    lang: str = "en"
):
    """Chat with context awareness"""
    
    # Get history for context
    history = memory.get_history(session_id, limit=3)
    
    # Add context to question
    context_question = q
    if history:
        context_question = f"Previous conversation context: {history[-1]['question']} Now: {q}"
    
    # Generate answer
    answer_data = ai_engine.generate_answer(context_question, mode.value)
    
    # Save to memory
    memory.add_message(session_id, q, answer_data)
    
    # Translate
    if lang != "en":
        answer_data["explanation"] = translator.translate(answer_data["explanation"], lang)
    
    answer_data["session_id"] = session_id
    answer_data["history_length"] = len(history)
    
    return answer_data

@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 10):
    """Get chat history for a session"""
    history = memory.get_history(session_id, limit)
    
    return {
        "session_id": session_id,
        "total_messages": len(history),
        "history": history
    }

@app.get("/sessions")
async def get_sessions():
    """Get all active sessions"""
    return {
        "total": len(memory.get_all_sessions()),
        "sessions": memory.get_all_sessions()
    }

@app.post("/image/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze an image for security issues
    
    Supports: PNG, JPG, JPEG, GIF
    Max size: 10MB
    """
    # Check file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_types}"
        )
    
    # Read file
    content = await file.read()
    
    # Check size (10MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Analyze
    result = await image_analyzer.analyze(content, file.filename)
    
    return result

@app.get("/topics")
async def get_topics():
    """Get all available cybersecurity topics"""
    topics = []
    
    for topic_id, topic_data in CyberSecurityKnowledge.TOPICS.items():
        topics.append({
            "id": topic_id,
            "name": topic_data.get("name"),
            "description": topic_data.get("description"),
            "risk_level": topic_data.get("risk").value,
            "keywords": topic_data.get("keywords", [])[:3],
            "cwe": topic_data.get("cwe", "N/A")
        })
    
    return {
        "total": len(topics),
        "topics": topics
    }

@app.get("/topic/{topic_id}")
async def get_topic_details(topic_id: str, mode: AnswerMode = AnswerMode.MEDIUM):
    """Get detailed information about a specific topic"""
    
    if topic_id not in CyberSecurityKnowledge.TOPICS:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found")
    
    explanation = CyberSecurityKnowledge.get_explanation(topic_id, mode.value)
    topic_data = CyberSecurityKnowledge.TOPICS[topic_id]
    
    return {
        "id": topic_id,
        "name": topic_data.get("name"),
        "description": topic_data.get("description"),
        "explanation": explanation,
        "risk_level": topic_data.get("risk").value,
        "prevention": topic_data.get("prevention", []),
        "examples": topic_data.get("examples", []),
        "cwe": topic_data.get("cwe", "N/A"),
        "owasp_rank": topic_data.get("owasp_rank", "N/A")
    }

@app.get("/about")
async def about():
    """About the Cyber AI Assistant"""
    return {
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "developer": "Khaled Mahmud",
        "description": "AI-powered Cyber Security Learning Assistant",
        "features": [
            "Multi-topic cybersecurity knowledge base",
            "Keyword extraction and topic detection",
            "Parallel web scraping",
            "Smart summarization",
            "Multi-language support (English, Bangla, Hindi, Spanish, French)",
            "Chat history and session management",
            "Image analysis",
            "No external AI dependencies"
        ],
        "technologies": [
            "FastAPI",
            "BeautifulSoup4",
            "Deep Translator",
            "Asyncio",
            "Built-in knowledge base"
        ],
        "topics_covered": len(CyberSecurityKnowledge.TOPICS),
        "github": "https://github.com/khaled/cyber-ai",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_sessions": len(memory.get_all_sessions()),
        "total_topics": len(CyberSecurityKnowledge.TOPICS),
        "scraping_enabled": SCRAPING_AVAILABLE,
        "translation_enabled": TRANSLATION_AVAILABLE,
        "ai_engine": "Rule-based (No external AI)",
        "conversations": len(ai_engine.conversation_history)
    }

@app.get("/reset/{session_id}")
async def reset_session(session_id: str):
    """Reset a chat session"""
    if session_id in memory.sessions:
        del memory.sessions[session_id]
        return {"status": "success", "message": f"Session {session_id} reset"}
    return {"status": "error", "message": "Session not found"}

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=config.DEBUG
    )
