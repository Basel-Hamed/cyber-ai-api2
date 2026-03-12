"""
Advanced Image Analysis Engine with OCR, ML, and Security Features
"""

import asyncio
import base64
import io
import os
import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import logging
from pathlib import Path
import aiohttp
import aiofiles

# Image processing libraries
from PIL import Image
import cv2
import numpy as np

# OCR libraries
import pytesseract
from pdf2image import convert_from_bytes

# ML libraries (optional)
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageType(Enum):
    """Types of images that can be analyzed"""
    SCREENSHOT = "screenshot"
    CODE = "code_snippet"
    ERROR_LOG = "error_log"
    TERMINAL = "terminal_output"
    DIAGRAM = "diagram"
    TEXT = "text_image"
    UNKNOWN = "unknown"

class SecurityRisk(Enum):
    """Security risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "informational"
    NONE = "none"

@dataclass
class ExtractedText:
    """Extracted text with metadata"""
    text: str
    confidence: float
    bounding_boxes: List[Dict]
    language: str
    page_number: Optional[int] = None

@dataclass
class SecurityFinding:
    """Security finding from image analysis"""
    title: str
    description: str
    risk_level: SecurityRisk
    line_numbers: Optional[List[int]] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cve_id: Optional[str] = None

@dataclass
class ImageAnalysisResult:
    """Complete image analysis result"""
    image_type: ImageType
    extracted_text: str
    findings: List[SecurityFinding]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]
    raw_ocr_output: Optional[str] = None

class AdvancedImageAnalyzer:
    """Advanced Image Analysis Engine with Multiple Features"""
    
    def __init__(self, 
                 use_ml: bool = True,
                 ocr_engine: str = "tesseract",
                 enable_cve_check: bool = True,
                 cache_results: bool = True):
        """
        Initialize image analyzer
        
        Args:
            use_ml: Use machine learning models
            ocr_engine: OCR engine to use ('tesseract', 'easyocr', 'both')
            enable_cve_check: Check extracted text against CVE database
            cache_results: Cache analysis results
        """
        self.use_ml = use_ml and TRANSFORMERS_AVAILABLE
        self.ocr_engine = ocr_engine
        self.enable_cve_check = enable_cve_check
        self.cache_results = cache_results
        self.cache = {}
        
        # Initialize ML models if available
        if self.use_ml:
            self._init_ml_models()
        
        # Initialize EasyOCR if available and requested
        if ocr_engine in ["easyocr", "both"] and EASYOCR_AVAILABLE:
            self.easyocr_reader = easyocr.Reader(['en'])
        
        # Load security patterns
        self.security_patterns = self._load_security_patterns()
        
        # Load CVE database (simplified)
        self.cve_database = self._load_cve_database()
    
    def _init_ml_models(self):
        """Initialize ML models for image analysis"""
        try:
            # Image classification
            self.image_classifier = pipeline(
                "image-classification",
                model="google/vit-base-patch16-224"
            )
            
            # Object detection
            self.object_detector = pipeline(
                "object-detection",
                model="facebook/detr-resnet-50"
            )
            
            # Text classification for extracted text
            self.text_classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            logger.info("ML models initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize ML models: {e}")
            self.use_ml = False
    
    def _load_security_patterns(self) -> Dict[str, List[Dict]]:
        """Load security patterns for detection"""
        return {
            'sql_injection': [
                {
                    'pattern': r'(?i)(select.*from|insert.*into|update.*set|delete.*from|drop\s+table)',
                    'risk': SecurityRisk.HIGH,
                    'description': 'Possible SQL injection vulnerability'
                },
                {
                    'pattern': r"'.*?(or|and).*?=.*?'",
                    'risk': SecurityRisk.HIGH,
                    'description': 'SQL injection attempt with OR/AND conditions'
                },
                {
                    'pattern': r'--\s*$',
                    'risk': SecurityRisk.MEDIUM,
                    'description': 'SQL comment detected (possible injection)'
                }
            ],
            'xss': [
                {
                    'pattern': r'<script[^>]*>.*?</script>',
                    'risk': SecurityRisk.HIGH,
                    'description': 'JavaScript code detected (possible XSS)'
                },
                {
                    'pattern': r'on\w+\s*=\s*["\']?[^"\'>]*["\']?',
                    'risk': SecurityRisk.MEDIUM,
                    'description': 'Inline event handler (possible XSS)'
                },
                {
                    'pattern': r'javascript:',
                    'risk': SecurityRisk.HIGH,
                    'description': 'JavaScript protocol detected'
                }
            ],
            'credentials': [
                {
                    'pattern': r'(?i)(password|passwd|pwd)\s*[=:]\s*[\'"]?\S+[\'"]?',
                    'risk': SecurityRisk.CRITICAL,
                    'description': 'Hardcoded password detected'
                },
                {
                    'pattern': r'(?i)(api[_-]?key|secret|token)\s*[=:]\s*[\'"]?\S+[\'"]?',
                    'risk': SecurityRisk.CRITICAL,
                    'description': 'API key or secret token detected'
                },
                {
                    'pattern': r'(?i)username\s*[=:]\s*[\'"]?\S+[\'"]?',
                    'risk': SecurityRisk.HIGH,
                    'description': 'Hardcoded username detected'
                }
            ],
            'error_messages': [
                {
                    'pattern': r'(?i)(error|exception|fatal|warning|deprecated)',
                    'risk': SecurityRisk.INFO,
                    'description': 'Error message detected'
                },
                {
                    'pattern': r'(?i)(stack trace|at\s+\S+\.\S+\(|line\s+\d+)',
                    'risk': SecurityRisk.INFO,
                    'description': 'Stack trace detected'
                },
                {
                    'pattern': r'(?i)(database error|mysql error|sql error)',
                    'risk': SecurityRisk.MEDIUM,
                    'description': 'Database error message (may leak info)'
                }
            ],
            'file_paths': [
                {
                    'pattern': r'(?i)(/etc/|/var/|/usr/|C:\\|D:\\)',
                    'risk': SecurityRisk.MEDIUM,
                    'description': 'File system path detected'
                },
                {
                    'pattern': r'(?i)(\.\./|\.\.\\)',
                    'risk': SecurityRisk.HIGH,
                    'description': 'Path traversal detected'
                }
            ],
            'code_vulnerabilities': [
                {
                    'pattern': r'eval\s*\(',
                    'risk': SecurityRisk.HIGH,
                    'description': 'Use of eval() - code injection risk'
                },
                {
                    'pattern': r'exec\s*\(',
                    'risk': SecurityRisk.HIGH,
                    'description': 'Use of exec() - command injection risk'
                },
                {
                    'pattern': r'(?i)md5\s*\(',
                    'risk': SecurityRisk.MEDIUM,
                    'description': 'Use of MD5 (cryptographically broken)'
                },
                {
                    'pattern': r'(?i)sha1\s*\(',
                    'risk': SecurityRisk.MEDIUM,
                    'description': 'Use of SHA1 (cryptographically broken)'
                }
            ]
        }
    
    def _load_cve_database(self) -> Dict[str, Dict]:
        """Load simplified CVE database for vulnerability matching"""
        # In production, you would load actual CVE data
        return {
            'sql_injection': {
                'CVE-2023-1234': 'SQL injection in web application',
                'CVE-2022-5678': 'Blind SQL injection vulnerability'
            },
            'xss': {
                'CVE-2023-4321': 'Cross-site scripting in admin panel',
                'CVE-2022-8765': 'Reflected XSS vulnerability'
            },
            'command_injection': {
                'CVE-2023-9876': 'Command injection in file upload',
                'CVE-2022-5432': 'OS command injection'
            }
        }
    
    async def analyze_image(self, 
                           image_input: Any,
                           options: Optional[Dict] = None) -> ImageAnalysisResult:
        """
        Main image analysis function
        
        Args:
            image_input: Image file path, bytes, PIL Image, or base64 string
            options: Analysis options dictionary
            
        Returns:
            ImageAnalysisResult object
        """
        start_time = datetime.now()
        options = options or {}
        
        try:
            # Process image input
            image = await self._load_image(image_input)
            
            # Check cache
            cache_key = self._get_cache_key(image)
            if self.cache_results and cache_key in self.cache:
                return self.cache[cache_key]
            
            # Detect image type
            image_type = await self._detect_image_type(image)
            
            # Extract text using OCR
            extracted_text = await self._extract_text(image, options)
            
            # Analyze for security issues
            findings = await self._analyze_security(extracted_text, image_type)
            
            # Perform ML-based analysis if enabled
            if self.use_ml and options.get('use_ml', True):
                ml_findings = await self._ml_analysis(image, extracted_text)
                findings.extend(ml_findings)
            
            # Check against CVE database
            if self.enable_cve_check:
                cve_matches = await self._check_cve_database(extracted_text)
                findings.extend(cve_matches)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(extracted_text, findings)
            
            # Create result
            result = ImageAnalysisResult(
                image_type=image_type,
                extracted_text=extracted_text.text,
                findings=findings,
                confidence=confidence,
                processing_time=(datetime.now() - start_time).total_seconds(),
                metadata={
                    'image_size': f"{image.width}x{image.height}",
                    'ocr_engine': self.ocr_engine,
                    'languages': [extracted_text.language],
                    'text_length': len(extracted_text.text)
                },
                raw_ocr_output=extracted_text.text if options.get('include_raw', False) else None
            )
            
            # Cache result
            if self.cache_results:
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return ImageAnalysisResult(
                image_type=ImageType.UNKNOWN,
                extracted_text="",
                findings=[],
                confidence=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                metadata={'error': str(e)}
            )
    
    async def _load_image(self, image_input: Any) -> Image.Image:
        """Load image from various input types"""
        if isinstance(image_input, str):
            # Check if it's a file path
            if os.path.exists(image_input):
                return Image.open(image_input)
            # Check if it's base64
            try:
                image_data = base64.b64decode(image_input)
                return Image.open(io.BytesIO(image_data))
            except:
                pass
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            return image_input
        elif hasattr(image_input, 'read'):  # File-like object
            return Image.open(image_input)
        
        raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    def _get_cache_key(self, image: Image.Image) -> str:
        """Generate cache key from image"""
        # Resize and convert to grayscale for consistent hashing
        img_copy = image.copy()
        img_copy.thumbnail((100, 100))
        img_copy = img_copy.convert('L')
        
        # Generate hash
        img_bytes = img_copy.tobytes()
        return hashlib.sha256(img_bytes).hexdigest()
    
    async def _detect_image_type(self, image: Image.Image) -> ImageType:
        """Detect the type of image"""
        # Use ML classification if available
        if self.use_ml:
            try:
                predictions = self.image_classifier(image)
                top_prediction = predictions[0]['label'].lower()
                
                if 'screenshot' in top_prediction:
                    return ImageType.SCREENSHOT
                elif 'code' in top_prediction or 'text' in top_prediction:
                    return ImageType.CODE
                elif 'diagram' in top_prediction:
                    return ImageType.DIAGRAM
            except Exception as e:
                logger.warning(f"ML classification failed: {e}")
        
        # Fallback to basic detection
        # Check image properties
        width, height = image.size
        aspect_ratio = width / height
        
        # Screenshots are usually wide
        if aspect_ratio > 1.5:
            return ImageType.SCREENSHOT
        
        # Check for text-heavy image (based on color variance)
        gray_image = image.convert('L')
        image_array = np.array(gray_image)
        variance = np.var(image_array)
        
        if variance > 1000:  # High variance suggests text
            return ImageType.TEXT
        
        return ImageType.UNKNOWN
    
    async def _extract_text(self, 
                           image: Image.Image, 
                           options: Dict) -> ExtractedText:
        """Extract text from image using OCR"""
        all_text = ""
        all_boxes = []
        confidences = []
        
        # Try different OCR engines
        if self.ocr_engine in ["tesseract", "both"]:
            try:
                # Tesseract OCR
                text = pytesseract.image_to_string(image, config='--psm 6')
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                all_text += text + "\n"
                
                # Extract bounding boxes and confidences
                for i, conf in enumerate(data['conf']):
                    if int(conf) > 60:  # Filter low confidence
                        all_boxes.append({
                            'text': data['text'][i],
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i],
                            'confidence': conf
                        })
                        confidences.append(conf)
                
            except Exception as e:
                logger.warning(f"Tesseract OCR failed: {e}")
        
        if self.ocr_engine in ["easyocr", "both"] and EASYOCR_AVAILABLE:
            try:
                # EasyOCR
                img_np = np.array(image)
                results = self.easyocr_reader.readtext(img_np)
                
                for result in results:
                    bbox, text, conf = result
                    all_text += text + "\n"
                    all_boxes.append({
                        'text': text,
                        'bbox': bbox,
                        'confidence': conf
                    })
                    confidences.append(conf)
                    
            except Exception as e:
                logger.warning(f"EasyOCR failed: {e}")
        
        # Calculate average confidence
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        # Detect language
        language = self._detect_language(all_text)
        
        return ExtractedText(
            text=all_text.strip(),
            confidence=avg_confidence,
            bounding_boxes=all_boxes,
            language=language
        )
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        # Check for Bangla/Bengali characters
        bangla_range = re.compile(r'[\u0980-\u09FF]')
        if bangla_range.search(text):
            return 'bn'
        
        # Check for Devanagari (Hindi, Sanskrit)
        devanagari_range = re.compile(r'[\u0900-\u097F]')
        if devanagari_range.search(text):
            return 'hi'
        
        # Default to English
        return 'en'
    
    async def _analyze_security(self, 
                               extracted_text: ExtractedText, 
                               image_type: ImageType) -> List[SecurityFinding]:
        """Analyze extracted text for security issues"""
        findings = []
        text = extracted_text.text
        
        # Check each category of security patterns
        for category, patterns in self.security_patterns.items():
            for pattern_info in patterns:
                matches = re.finditer(pattern_info['pattern'], text)
                
                for match in matches:
                    # Get context (lines around the match)
                    lines = text.split('\n')
                    matched_line = None
                    line_number = None
                    
                    for i, line in enumerate(lines, 1):
                        if match.group() in line:
                            matched_line = line.strip()
                            line_number = i
                            break
                    
                    # Create finding
                    finding = SecurityFinding(
                        title=f"{category.replace('_', ' ').title()} Detected",
                        description=pattern_info['description'],
                        risk_level=pattern_info['risk'],
                        line_numbers=[line_number] if line_number else None,
                        code_snippet=matched_line,
                        recommendation=self._get_recommendation(category, pattern_info)
                    )
                    
                    # Check if similar finding already exists
                    if not self._has_similar_finding(findings, finding):
                        findings.append(finding)
        
        return findings
    
    def _get_recommendation(self, category: str, pattern_info: Dict) -> str:
        """Get recommendation for security finding"""
        recommendations = {
            'sql_injection': 'Use parameterized queries, input validation, and ORM frameworks',
            'xss': 'Implement output encoding, Content Security Policy, and input sanitization',
            'credentials': 'Remove hardcoded credentials, use environment variables or secure vaults',
            'error_messages': 'Implement proper error handling, avoid exposing sensitive information',
            'file_paths': 'Validate and sanitize file paths, use allowlists',
            'code_vulnerabilities': 'Avoid using dangerous functions, use secure alternatives'
        }
        
        return recommendations.get(category, 'Review and fix the identified security issue')
    
    def _has_similar_finding(self, findings: List[SecurityFinding], 
                             new_finding: SecurityFinding) -> bool:
        """Check if similar finding already exists"""
        for finding in findings:
            if (finding.title == new_finding.title and 
                finding.risk_level == new_finding.risk_level):
                return True
        return False
    
    async def _ml_analysis(self, 
                          image: Image.Image, 
                          extracted_text: ExtractedText) -> List[SecurityFinding]:
        """Perform ML-based analysis"""
        findings = []
        
        if not self.use_ml:
            return findings
        
        try:
            # Object detection in image
            objects = self.object_detector(image)
            
            for obj in objects:
                if obj['label'] in ['screen', 'laptop', 'computer']:
                    findings.append(SecurityFinding(
                        title="Screenshot Detected",
                        description=f"Image contains a {obj['label']} screen",
                        risk_level=SecurityRisk.INFO,
                        recommendation="Ensure no sensitive information is visible"
                    ))
            
            # Text classification
            if extracted_text.text:
                classification = self.text_classifier(extracted_text.text[:512])
                
                if classification[0]['label'] == 'NEGATIVE' and classification[0]['score'] > 0.8:
                    findings.append(SecurityFinding(
                        title="Negative Content Detected",
                        description="The extracted text contains negative sentiment (possible error messages)",
                        risk_level=SecurityRisk.INFO,
                        recommendation="Review error messages for sensitive information leakage"
                    ))
                    
        except Exception as e:
            logger.warning(f"ML analysis failed: {e}")
        
        return findings
    
    async def _check_cve_database(self, 
                                  extracted_text: ExtractedText) -> List[SecurityFinding]:
        """Check extracted text against CVE database"""
        findings = []
        text_lower = extracted_text.text.lower()
        
        for vuln_type, cves in self.cve_database.items():
            if vuln_type in text_lower:
                for cve_id, description in cves.items():
                    findings.append(SecurityFinding(
                        title=f"Potential {vuln_type.replace('_', ' ').title()} Vulnerability",
                        description=f"{cve_id}: {description}",
                        risk_level=SecurityRisk.HIGH,
                        recommendation="Update to patched version or apply mitigations",
                        cve_id=cve_id
                    ))
        
        return findings
    
    def _calculate_confidence(self, 
                             extracted_text: ExtractedText, 
                             findings: List[SecurityFinding]) -> float:
        """Calculate overall confidence score"""
        # Base confidence from OCR
        confidence = extracted_text.confidence
        
        # Adjust based on findings
        if findings:
            # More findings increase confidence (if they match patterns)
            confidence = min(1.0, confidence + (len(findings) * 0.05))
        
        # Adjust based on text length
        text_length = len(extracted_text.text)
        if text_length < 10:
            confidence *= 0.5
        elif text_length > 1000:
            confidence = min(1.0, confidence * 1.2)
        
        return round(confidence, 2)
    
    def generate_report(self, result: ImageAnalysisResult, format: str = "text") -> str:
        """Generate analysis report in various formats"""
        if format == "text":
            return self._generate_text_report(result)
        elif format == "html":
            return self._generate_html_report(result)
        elif format == "json":
            return self._generate_json_report(result)
        elif format == "markdown":
            return self._generate_markdown_report(result)
        else:
            return self._generate_text_report(result)
    
    def _generate_text_report(self, result: ImageAnalysisResult) -> str:
        """Generate text format report"""
        report = []
        report.append("="*60)
        report.append("CYBER AI IMAGE ANALYSIS REPORT")
        report.append("="*60)
        report.append(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Image Type: {result.image_type.value}")
        report.append(f"Confidence Score: {result.confidence*100:.1f}%")
        report.append(f"Processing Time: {result.processing_time:.2f}s")
        report.append("="*60)
        
        if result.extracted_text:
            report.append("\nEXTRACTED TEXT:")
            report.append("-"*40)
            # Show first 500 chars
            preview = result.extracted_text[:500] + "..." if len(result.extracted_text) > 500 else result.extracted_text
            report.append(preview)
        
        if result.findings:
            report.append("\nSECURITY FINDINGS:")
            report.append("-"*40)
            
            # Group by risk level
            for risk in SecurityRisk:
                risk_findings = [f for f in result.findings if f.risk_level == risk]
                if risk_findings:
                    report.append(f"\n{risk.value.upper()} RISK FINDINGS:")
                    for finding in risk_findings:
                        report.append(f"  • {finding.title}")
                        report.append(f"    Description: {finding.description}")
                        if finding.line_numbers:
                            report.append(f"    Lines: {', '.join(map(str, finding.line_numbers))}")
                        if finding.code_snippet:
                            report.append(f"    Code: {finding.code_snippet}")
                        if finding.recommendation:
                            report.append(f"    Recommendation: {finding.recommendation}")
                        if finding.cve_id:
                            report.append(f"    CVE: {finding.cve_id}")
                        report.append("")
        else:
            report.append("\nNo security findings detected.")
        
        report.append("="*60)
        report.append("RECOMMENDATIONS:")
        if result.findings:
            for finding in result.findings[:3]:
                if finding.recommendation:
                    report.append(f"• {finding.recommendation}")
        else:
            report.append("• No immediate security concerns detected")
            report.append("• Continue regular security monitoring")
        
        report.append("="*60)
        
        return "\n".join(report)
    
    def _generate_html_report(self, result: ImageAnalysisResult) -> str:
        """Generate HTML format report"""
        # Color mapping for risk levels
        risk_colors = {
            SecurityRisk.CRITICAL: "#dc3545",
            SecurityRisk.HIGH: "#fd7e14",
            SecurityRisk.MEDIUM: "#ffc107",
            SecurityRisk.LOW: "#28a745",
            SecurityRisk.INFO: "#17a2b8",
            SecurityRisk.NONE: "#6c757d"
        }
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cyber AI Image Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .finding {{ margin: 10px 0; padding: 10px; border-left: 4px solid; }}
                .risk-critical {{ border-color: #dc3545; }}
                .risk-high {{ border-color: #fd7e14; }}
                .risk-medium {{ border-color: #ffc107; }}
                .extracted-text {{ background: #f8f9fa; padding: 15px; }}
                .metadata {{ display: grid; grid-template-columns: auto auto; gap: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Cyber AI Image Analysis Report</h1>
                <p>Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Analysis Overview</h2>
                <div class="metadata">
                    <div><strong>Image Type:</strong> {result.image_type.value}</div>
                    <div><strong>Confidence:</strong> {result.confidence*100:.1f}%</div>
                    <div><strong>Processing Time:</strong> {result.processing_time:.2f}s</div>
                    <div><strong>Text Length:</strong> {len(result.extracted_text)} characters</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Extracted Text</h2>
                <div class="extracted-text">
                    <pre>{result.extracted_text[:1000]}{'...' if len(result.extracted_text) > 1000 else ''}</pre>
                </div>
            </div>
            
            <div class="section">
                <h2>Security Findings ({len(result.findings)})</h2>
        """
        
        for finding in result.findings:
            color = risk_colors.get(finding.risk_level, "#6c757d")
            html += f"""
                <div class="finding risk-{finding.risk_level.value}" style="border-left-color: {color};">
                    <h3>{finding.title}</h3>
                    <p><strong>Risk Level:</strong> {finding.risk_level.value.upper()}</p>
                    <p><strong>Description:</strong> {finding.description}</p>
            """
            
            if finding.line_numbers:
                html += f"<p><strong>Lines:</strong> {', '.join(map(str, finding.line_numbers))}</p>"
            
            if finding.code_snippet:
                html += f"<p><strong>Code:</strong> <code>{finding.code_snippet}</code></p>"
            
            if finding.recommendation:
                html += f"<p><strong>Recommendation:</strong> {finding.recommendation}</p>"
            
            if finding.cve_id:
                html += f"<p><strong>CVE:</strong> {finding.cve_id}</p>"
            
            html += "</div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_json_report(self, result: ImageAnalysisResult) -> str:
        """Generate JSON format report"""
        report_data = {
            'analysis_time': datetime.now().isoformat(),
            'image_type': result.image_type.value,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'extracted_text_preview': result.extracted_text[:500],
            'findings': [
                {
                    'title': f.title,
                    'description': f.description,
                    'risk_level': f.risk_level.value,
                    'line_numbers': f.line_numbers,
                    'code_snippet': f.code_snippet,
                    'recommendation': f.recommendation,
                    'cve_id': f.cve_id
                }
                for f in result.findings
            ],
            'metadata': result.metadata
        }
        
        return json.dumps(report_data, indent=2)
    
    def _generate_markdown_report(self, result: ImageAnalysisResult) -> str:
        """Generate Markdown format report"""
        md = []
        md.append("# Cyber AI Image Analysis Report")
        md.append("")
        md.append(f"**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Image Type:** {result.image_type.value}")
        md.append(f"**Confidence:** {result.confidence*100:.1f}%")
        md.append(f"**Processing Time:** {result.processing_time:.2f}s")
        md.append("")
        
        md.append("## Extracted Text")
        md.append("```")
        md.append(result.extracted_text[:500] + ("..." if len(result.extracted_text) > 500 else ""))
        md.append("```")
        md.append("")
        
        md.append(f"## Security Findings ({len(result.findings)})")
        md.append("")
        
        for finding in result.findings:
            md.append(f"### {finding.title}")
            md.append(f"- **Risk Level:** {finding.risk_level.value.upper()}")
            md.append(f"- **Description:** {finding.description}")
            if finding.line_numbers:
                md.append(f"- **Lines:** {', '.join(map(str, finding.line_numbers))}")
            if finding.code_snippet:
                md.append(f"- **Code:** `{finding.code_snippet}`")
            if finding.recommendation:
                md.append(f"- **Recommendation:** {finding.recommendation}")
            if finding.cve_id:
                md.append(f"- **CVE:** {finding.cve_id}")
            md.append("")
        
        md.append("## Recommendations")
        if result.findings:
            for finding in result.findings[:3]:
                if finding.recommendation:
                    md.append(f"- {finding.recommendation}")
        else:
            md.append("- No immediate security concerns detected")
            md.append("- Continue regular security monitoring")
        
        return "\n".join(md)

# Simplified async function for backward compatibility
async def analyze_image(image_input: Any, 
                       detailed: bool = False,
                       options: Optional[Dict] = None) -> str:
    """
    Analyze image for security issues
    
    Args:
        image_input: Image file path, bytes, or PIL Image
        detailed: Return detailed report if True
        options: Additional analysis options
    
    Returns:
        Analysis report as string
    """
    analyzer = AdvancedImageAnalyzer()
    
    # Perform analysis
    result = await analyzer.analyze_image(image_input, options or {})
    
    if detailed:
        # Return comprehensive report
        return analyzer.generate_report(result, format="markdown")
    else:
        # Simple summary for backward compatibility
        summary = ["🔍 CYBER AI IMAGE ANALYSIS", ""]
        
        if result.findings:
            summary.append(f"📊 Found {len(result.findings)} potential issues:")
            for finding in result.findings[:5]:  # Show top 5
                risk_icon = {
                    SecurityRisk.CRITICAL: "🔥",
                    SecurityRisk.HIGH: "⚠️",
                    SecurityRisk.MEDIUM: "⚡",
                    SecurityRisk.LOW: "ℹ️",
                    SecurityRisk.INFO: "📝"
                }.get(finding.risk_level, "•")
                
                summary.append(f"{risk_icon} {finding.title}")
            
            if len(result.findings) > 5:
                summary.append(f"... and {len(result.findings) - 5} more")
        else:
            summary.append("✅ No security issues detected")
        
        summary.append("")
        summary.append("📋 Cyber AI recommends manual review by a security analyst.")
        summary.append(f"⏱️ Analysis completed in {result.processing_time:.2f}s")
        
        return "\n".join(summary)

# Advanced usage with multiple images
async def analyze_multiple_images(image_inputs: List[Any], 
                                 concurrency: int = 3) -> List[ImageAnalysisResult]:
    """Analyze multiple images concurrently"""
    analyzer = AdvancedImageAnalyzer()
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async def analyze_with_semaphore(image_input):
        async with semaphore:
            return await analyzer.analyze_image(image_input)
    
    tasks = [analyze_with_semaphore(img) for img in image_inputs]
    return await asyncio.gather(*tasks)

# Example usage
async def main():
    # Example 1: Simple analysis
    print("="*60)
    print("SIMPLE ANALYSIS")
    print("="*60)
    
    # You would replace this with actual image data
    # result = await analyze_image("path/to/screenshot.png")
    # print(result)
    
    # Example 2: Detailed analysis with custom options
    print("\n" + "="*60)
    print("DETAILED ANALYSIS")
    print("="*60)
    
    analyzer = AdvancedImageAnalyzer(use_ml=False)  # Disable ML for testing
    
    # Simulate analysis with sample data
    class MockImage:
        def __init__(self):
            self.width = 1920
            self.height = 1080
    
    mock_image = MockImage()
    
    # Simulate extracted text with security patterns
    mock_text = ExtractedText(
        text="""
        Error: SQL injection detected in login form
        Query: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
        Stack trace: at login.php line 42
        
        Potential XSS: <script>alert('XSS')</script>
        Password: "supersecret123"
        """,
        confidence=0.85,
        bounding_boxes=[],
        language='en'
    )
    
    # Create mock result
    result = ImageAnalysisResult(
        image_type=ImageType.SCREENSHOT,
        extracted_text=mock_text.text,
        findings=[
            SecurityFinding(
                title="SQL Injection
