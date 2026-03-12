"""
Advanced Translation Engine with Multiple Services and Language Detection
"""

import time
import hashlib
from typing import Optional, Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
import os

# Translation libraries
from deep_translator import GoogleTranslator, MicrosoftTranslator, PonsTranslator
from googletrans import Translator as GoogleTransV2
from langdetect import detect, DetectorFactory
from textblob import TextBlob
import requests

# For consistent language detection
DetectorFactory.seed = 0

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService(Enum):
    """Available translation services"""
    GOOGLE = "google"
    GOOGLE_V2 = "google_v2"
    MICROSOFT = "microsoft"
    PONS = "pons"
    AUTO = "auto"  # Automatically choose best service

class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    BENGALI = "bn"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh-CN"
    JAPANESE = "ja"
    ARABIC = "ar"
    RUSSIAN = "ru"
    
    @classmethod
    def get_name(cls, code: str) -> str:
        """Get language name from code"""
        names = {
            "en": "English",
            "bn": "Bangla",
            "hi": "Hindi",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "zh-CN": "Chinese",
            "ja": "Japanese",
            "ar": "Arabic",
            "ru": "Russian"
        }
        return names.get(code, code)

@dataclass
class TranslationResult:
    """Translation result with metadata"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    service_used: TranslationService
    confidence: float
    timestamp: datetime
    alternative_translations: List[str] = None
    
class AdvancedTranslator:
    """Advanced Translation Engine with Multiple Features"""
    
    def __init__(self, cache_size: int = 1000, cache_ttl: int = 3600):
        """
        Initialize translator with caching
        
        Args:
            cache_size: Maximum number of cached translations
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache = {}
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self.translation_stats = {
            'total_translations': 0,
            'successful': 0,
            'failed': 0,
            'cached_used': 0
        }
        
        # Initialize translators
        self.translators = self._init_translators()
        
    def _init_translators(self) -> Dict:
        """Initialize different translation services"""
        translators = {}
        
        try:
            translators[TranslationService.GOOGLE] = GoogleTranslator
        except Exception as e:
            logger.warning(f"Failed to initialize GoogleTranslator: {e}")
            
        try:
            translators[TranslationService.GOOGLE_V2] = GoogleTransV2
        except Exception as e:
            logger.warning(f"Failed to initialize GoogleTransV2: {e}")
            
        try:
            # You would need to add your API keys here
            translators[TranslationService.MICROSOFT] = None  # Requires API key
        except Exception as e:
            logger.warning(f"Failed to initialize MicrosoftTranslator: {e}")
            
        return translators
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of text with confidence score
        
        Returns:
            Tuple of (language_code, confidence_score)
        """
        try:
            # Use langdetect
            lang = detect(text)
            confidence = 0.95  # langdetect doesn't provide confidence
            
            # Use TextBlob as backup/verification
            blob = TextBlob(text)
            if blob.detect_language():
                # Simple confidence calculation
                confidence = 0.90
            
            return lang, confidence
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en", 0.5  # Default to English with low confidence
    
    def _get_cache_key(self, text: str, source: str, target: str) -> str:
        """Generate cache key for translation"""
        key_string = f"{text}|{source}|{target}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached(self, cache_key: str) -> Optional[TranslationResult]:
        """Get cached translation if available and not expired"""
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached.timestamp < timedelta(seconds=self.cache_ttl):
                self.translation_stats['cached_used'] += 1
                return cached
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: TranslationResult):
        """Cache translation result"""
        # Manage cache size
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]
        
        self.cache[cache_key] = result
    
    def translate(self, 
                 text: str, 
                 target: str = "bn", 
                 source: str = "auto",
                 service: TranslationService = TranslationService.AUTO,
                 alternatives: bool = False) -> TranslationResult:
        """
        Advanced translation with multiple features
        
        Args:
            text: Text to translate
            target: Target language code
            source: Source language code (auto for detection)
            service: Translation service to use
            alternatives: Whether to get alternative translations
        
        Returns:
            TranslationResult object with metadata
        """
        self.translation_stats['total_translations'] += 1
        
        # Detect source language if auto
        if source == "auto":
            detected_lang, confidence = self.detect_language(text)
            source = detected_lang
        else:
            confidence = 0.95
        
        # Check cache
        cache_key = self._get_cache_key(text, source, target)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # Determine which service to use
        if service == TranslationService.AUTO:
            service = self._select_best_service(text, source, target)
        
        # Perform translation
        translated_text = self._translate_with_service(text, source, target, service)
        
        # Get alternatives if requested
        alternatives_list = None
        if alternatives and translated_text != text:
            alternatives_list = self._get_alternatives(text, source, target)
        
        # Create result
        result = TranslationResult(
            original_text=text,
            translated_text=translated_text,
            source_lang=source,
            target_lang=target,
            service_used=service,
            confidence=confidence,
            timestamp=datetime.now(),
            alternative_translations=alternatives_list
        )
        
        # Cache result
        self._cache_result(cache_key, result)
        
        # Update stats
        if translated_text != text:
            self.translation_stats['successful'] += 1
        else:
            self.translation_stats['failed'] += 1
        
        return result
    
    def _select_best_service(self, text: str, source: str, target: str) -> TranslationService:
        """Select the best translation service based on language pair"""
        
        # Language pairs and their preferred services
        preferred_services = {
            ("en", "bn"): TranslationService.GOOGLE,  # English to Bangla
            ("bn", "en"): TranslationService.GOOGLE,  # Bangla to English
            ("en", "hi"): TranslationService.GOOGLE,  # English to Hindi
            ("hi", "en"): TranslationService.GOOGLE,  # Hindi to English
        }
        
        # Check if we have a preferred service for this language pair
        key = (source, target)
        if key in preferred_services:
            return preferred_services[key]
        
        # Default to Google
        return TranslationService.GOOGLE
    
    def _translate_with_service(self, text: str, source: str, 
                               target: str, service: TranslationService) -> str:
        """Perform translation using specified service"""
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if service == TranslationService.GOOGLE:
                    translator = GoogleTranslator(source=source, target=target)
                    return translator.translate(text)
                    
                elif service == TranslationService.GOOGLE_V2:
                    translator = GoogleTransV2()
                    result = translator.translate(text, src=source, dest=target)
                    return result.text
                    
                elif service == TranslationService.MICROSOFT:
                    # Implement Microsoft Translator with API key
                    # You would need to add your API key here
                    return self._microsoft_translate(text, source, target)
                    
                else:
                    # Fallback to Google
                    translator = GoogleTranslator(source=source, target=target)
                    return translator.translate(text)
                    
            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"All translation attempts failed for: {text[:50]}...")
                    return text  # Return original text on failure
        
        return text
    
    def _microsoft_translate(self, text: str, source: str, target: str) -> str:
        """Microsoft Translator implementation"""
        # You would need to add your Microsoft Translator API key
        # This is a placeholder implementation
        api_key = os.getenv("MICROSOFT_TRANSLATOR_KEY")
        if not api_key:
            raise Exception("Microsoft Translator API key not found")
        
        endpoint = "https://api.cognitive.microsofttranslator.com/translate"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/json"
        }
        params = {
            "api-version": "3.0",
            "from": source,
            "to": target
        }
        body = [{"text": text}]
        
        response = requests.post(endpoint, headers=headers, params=params, json=body)
        response.raise_for_status()
        
        result = response.json()
        return result[0]["translations"][0]["text"]
    
    def _get_alternatives(self, text: str, source: str, target: str) -> List[str]:
        """Get alternative translations using different services"""
        alternatives = []
        services_tried = []
        
        for service in [TranslationService.GOOGLE, TranslationService.GOOGLE_V2]:
            if service not in services_tried:
                try:
                    alt_trans = self._translate_with_service(text, source, target, service)
                    if alt_trans != text and alt_trans not in alternatives:
                        alternatives.append(alt_trans)
                        services_tried.append(service)
                except:
                    continue
        
        return alternatives[:3]  # Return up to 3 alternatives
    
    def translate_batch(self, texts: List[str], target: str = "bn", 
                       source: str = "auto") -> List[TranslationResult]:
        """Translate multiple texts"""
        results = []
        for text in texts:
            try:
                result = self.translate(text, target, source)
                results.append(result)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Batch translation failed for: {text[:50]}... Error: {e}")
                results.append(TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_lang=source if source != "auto" else "unknown",
                    target_lang=target,
                    service_used=TranslationService.AUTO,
                    confidence=0,
                    timestamp=datetime.now()
                ))
        
        return results
    
    def translate_with_context(self, text: str, context: str, 
                              target: str = "bn") -> TranslationResult:
        """Translate with additional context for better accuracy"""
        # Combine context with text for better translation
        combined = f"{context}\n\n{text}"
        
        # Translate combined text
        result = self.translate(combined, target)
        
        # Extract just the translated original text portion
        # This is simplistic - in reality you'd need more sophisticated parsing
        translated_parts = result.translated_text.split('\n\n')
        if len(translated_parts) > 1:
            result.translated_text = translated_parts[-1]
        
        return result
    
    def get_translation_stats(self) -> Dict:
        """Get translation statistics"""
        return {
            **self.translation_stats,
            'cache_size': len(self.cache),
            'cache_capacity': self.cache_size,
            'cache_ttl': self.cache_ttl
        }
    
    def clear_cache(self):
        """Clear translation cache"""
        self.cache.clear()
        logger.info("Translation cache cleared")

# Simple interface for backward compatibility
def translate_bn(text: str, use_advanced: bool = False, **kwargs) -> str:
    """
    Translate text to Bangla
    
    Args:
        text: Text to translate
        use_advanced: Use advanced translation features
        **kwargs: Additional arguments for advanced translation
    
    Returns:
        Translated text
    """
    if use_advanced:
        translator = AdvancedTranslator()
        result = translator.translate(text, target="bn", **kwargs)
        return result.translated_text
    else:
        # Simple translation for backward compatibility
        try:
            return GoogleTranslator(source="auto", target="bn").translate(text)
        except Exception as e:
            logger.error(f"Simple translation failed: {e}")
            return text

# Advanced usage functions
def translate_advanced(text: str, target: str = "bn", 
                      source: str = "auto", 
                      alternatives: bool = False) -> Dict:
    """
    Advanced translation with full metadata
    
    Returns:
        Dictionary with translation and metadata
    """
    translator = AdvancedTranslator()
    result = translator.translate(text, target, source, alternatives=alternatives)
    
    return {
        'translated_text': result.translated_text,
        'source_language': Language.get_name(result.source_lang),
        'target_language': Language.get_name(result.target_lang),
        'confidence': f"{result.confidence * 100:.1f}%",
        'service_used': result.service_used.value,
        'alternatives': result.alternative_translations or []
    }

def detect_and_translate(text: str, target: str = "bn") -> Dict:
    """
    Detect language and translate automatically
    """
    translator = AdvancedTranslator()
    
    # Detect language
    detected_lang, confidence = translator.detect_language(text)
    
    # Translate
    result = translator.translate(text, target, source=detected_lang)
    
    return {
        'original_text': text,
        'detected_language': Language.get_name(detected_lang),
        'detection_confidence': f"{confidence * 100:.1f}%",
        'translated_text': result.translated_text,
        'translation_confidence': f"{result.confidence * 100:.1f}%"
    }

# Example usage and testing
if __name__ == "__main__":
    # Test texts
    test_texts = [
        "Hello, how are you?",
        "What is your name?",
        "I love programming in Python",
        "The weather is very nice today"
    ]
    
    print("="*60)
    print("SIMPLE TRANSLATION")
    print("="*60)
    for text in test_texts:
        translated = translate_bn(text)
        print(f"Original: {text}")
        print(f"Bangla: {translated}\n")
    
    print("="*60)
    print("ADVANCED TRANSLATION WITH METADATA")
    print("="*60)
    
    translator = AdvancedTranslator()
    
    for text in test_texts:
        result = translator.translate(text, target="bn", alternatives=True)
        print(f"Original: {result.original_text}")
        print(f"Translated: {result.translated_text}")
        print(f"Source Lang: {Language.get_name(result.source_lang)}")
        print(f"Service: {result.service_used.value}")
        print(f"Confidence: {result.confidence * 100:.1f}%")
        if result.alternative_translations:
            print(f"Alternatives: {result.alternative_translations[:2]}")
        print("-"*40)
    
    print("\n" + "="*60)
    print("LANGUAGE DETECTION + TRANSLATION")
    print("="*60)
    
    mixed_texts = [
        "Bonjour, comment allez-vous?",
        "今日はいい天気ですね",
        "আপনি কেমন আছেন?"
    ]
    
    for text in mixed_texts:
        result = detect_and_translate(text)
        print(f"Original: {text}")
        print(f"Detected: {result['detected_language']} ({result['detection_confidence']})")
        print(f"Translated: {result['translated_text']}")
        print("-"*40)
    
    print("\n" + "="*60)
    print("TRANSLATION STATISTICS")
    print("="*60)
    stats = translator.get_translation_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
