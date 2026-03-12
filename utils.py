"""
Utility functions for Cyber AI Assistant
Render-optimized with error handling
"""

import re
import hashlib
import uuid
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import random
import string

logger = logging.getLogger(__name__)

def generate_request_id() -> str:
    """Generate unique request ID"""
    try:
        return str(uuid.uuid4())
    except Exception as e:
        logger.error(f"Error generating request ID: {e}")
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"req_{timestamp}_{random_part}"

def generate_message_id() -> str:
    """Generate unique message ID"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        return f"msg_{timestamp}_{random_part}"
    except Exception as e:
        logger.error(f"Error generating message ID: {e}")
        return f"msg_{int(datetime.now().timestamp())}"

def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Remove special characters and extra spaces"""
    try:
        if not text:
            return ""
        
        # Remove extra spaces
        text = ' '.join(str(text).split())
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\[\]]', ' ', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error sanitizing text: {e}")
        return str(text)[:max_length] if max_length else str(text)

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length"""
    try:
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    except Exception as e:
        logger.error(f"Error truncating text: {e}")
        return str(text)[:max_length]

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception as e:
        logger.error(f"Error extracting domain from {url}: {e}")
        return url

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safe division with zero check"""
    try:
        return a / b if b != 0 else default
    except Exception:
        return default

def format_timestamp(dt: Optional[datetime] = None, format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format timestamp for logging"""
    try:
        if dt is None:
            dt = datetime.now()
        return dt.strftime(format)
    except Exception as e:
        logger.error(f"Error formatting timestamp: {e}")
        return str(datetime.now())

def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely load JSON data"""
    try:
        return json.loads(data)
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        return default if default is not None else {}

def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Safely dump JSON data"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Error dumping JSON: {e}")
        return default

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists"""
    try:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return Path(".")

def extract_keywords_from_text(text: str, max_keywords: int = 5) -> List[str]:
    """Extract keywords from text"""
    try:
        # Simple keyword extraction (can be enhanced)
        words = re.findall(r'\b\w{4,}\b', text.lower())
        # Remove common words
        stopwords = {'what', 'why', 'how', 'when', 'where', 'who', 'which',
                    'this', 'that', 'these', 'those', 'with', 'from', 'have'}
        keywords = [w for w in words if w not in stopwords]
        # Get unique and limit
        seen = set()
        unique_keywords = []
        for w in keywords:
            if w not in seen:
                seen.add(w)
                unique_keywords.append(w)
        return unique_keywords[:max_keywords]
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity"""
    try:
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)
    except Exception:
        return 0.0

def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes"""
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return 0

def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False
