"""
Pydantic models for Cyber AI Assistant
Render-optimized with complete validation
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re

class AnswerMode(str, Enum):
    """Answer mode options"""
    TINY = "tiny"
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    COMPREHENSIVE = "comprehensive"

class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    BENGALI = "bn"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"

class RiskLevel(str, Enum):
    """Security risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    NONE = "none"

class AskRequest(BaseModel):
    """Request model for ask endpoint"""
    question: str = Field(..., min_length=3, max_length=1000, 
                          description="User's question about cybersecurity")
    mode: AnswerMode = Field(AnswerMode.MEDIUM, 
                            description="Answer length mode")
    language: Language = Field(Language.BENGALI, 
                              description="Target language for translation")
    session_id: Optional[str] = Field(None, 
                                      description="Session ID for conversation tracking")
    use_advanced: bool = Field(True, 
                               description="Use advanced AI features")
    
    @validator('question')
    def validate_question(cls, v):
        """Validate and clean question"""
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Question must be at least 3 characters')
        if len(v) > 1000:
            raise ValueError('Question too long (max 1000 characters)')
        # Remove any dangerous characters
        v = re.sub(r'[<>]', '', v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What is SQL injection?",
                "mode": "medium",
                "language": "bn",
                "session_id": "session_12345"
            }
        }

class AskResponse(BaseModel):
    """Response model for ask endpoint"""
    question: str
    answer_en: str
    answer_bn: str
    keywords: List[str]
    topic: str
    confidence: float
    sources: List[str]
    processing_time: float
    message_id: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What is SQL injection?",
                "answer_en": "SQL injection is a code injection technique...",
                "answer_bn": "এসকিউএল ইনজেকশন একটি কোড ইনজেকশন কৌশল...",
                "keywords": ["sql", "injection", "security"],
                "topic": "SQL Injection",
                "confidence": 0.95,
                "sources": ["portswigger", "owasp"],
                "processing_time": 2.5,
                "message_id": "msg_20240115_12345",
                "session_id": "session_12345"
            }
        }

class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis"""
    detailed: bool = Field(False, description="Return detailed analysis")
    include_ocr: bool = Field(True, description="Include OCR text extraction")
    security_check: bool = Field(True, description="Perform security analysis")
    format: str = Field("text", regex="^(text|html|json|markdown)$",
                       description="Output format")

class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis"""
    filename: str
    analysis: str
    image_type: str
    confidence: float
    findings_count: int
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time: float
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatMessage(BaseModel):
    """Chat message model"""
    message_id: str
    question: str
    answer: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    messages: List[ChatMessage]
    message_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('message_count', always=True)
    def calculate_message_count(cls, v, values):
        if 'messages' in values:
            return len(values['messages'])
        return v

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: str
    request_id: Optional[str]
    timestamp: datetime = Field(default_factory=datetime.now)
