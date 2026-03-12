"""
Advanced AI Engine for Intelligent Question Answering
With NLP, ML, and Context-Aware Features
"""

import re
import json
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

# NLP Libraries (install with: pip install nltk scikit-learn transformers)
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnswerMode(Enum):
    """Answer modes with different detail levels"""
    TINY = "tiny"      # 1-2 sentences
    SHORT = "short"    # 1 paragraph
    MEDIUM = "medium"  # 2-3 paragraphs
    LONG = "long"      # detailed explanation
    COMPREHENSIVE = "comprehensive"  # full detailed with examples

class QuestionType(Enum):
    """Types of questions for better answer generation"""
    WHAT = "what"
    WHY = "why"
    HOW = "how"
    WHEN = "when"
    WHERE = "where"
    WHO = "who"
    COMPARE = "compare"
    DEFINE = "define"
    LIST = "list"
    EXPLAIN = "explain"
    UNKNOWN = "unknown"

@dataclass
class AnswerContext:
    """Context information for answers"""
    question: str
    question_type: QuestionType
    keywords: List[str]
    entities: List[str]
    confidence: float
    sources: List[str]
    timestamp: datetime

class AdvancedAIEngine:
    """Advanced AI Engine with NLP and ML capabilities"""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)
        self.knowledge_base = {}
        self.answer_cache = {}
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """Load predefined knowledge and patterns"""
        self.knowledge_base = {
            'security': {
                'keywords': ['vulnerability', 'exploit', 'attack', 'malicious', 'injection'],
                'patterns': {
                    'sql_injection': {
                        'description': 'SQL injection occurs when malicious SQL code is inserted into queries',
                        'prevention': ['Parameterized queries', 'Input validation', 'Stored procedures'],
                        'examples': ["' OR '1'='1", "'; DROP TABLE users; --"]
                    },
                    'xss': {
                        'description': 'Cross-site scripting injects malicious scripts into web pages',
                        'prevention': ['Output encoding', 'Content Security Policy', 'Input sanitization'],
                        'examples': ['<script>alert("XSS")</script>']
                    }
                }
            },
            'programming': {
                'keywords': ['python', 'java', 'function', 'class', 'variable'],
                'concepts': {
                    'oop': 'Object-oriented programming organizes code into objects and classes',
                    'algorithm': 'Step-by-step procedure for solving problems'
                }
            }
        }
    
    def extract_keywords_advanced(self, question: str, top_n: int = 5) -> List[str]:
        """Advanced keyword extraction with NLP"""
        try:
            # Tokenize and clean
            tokens = word_tokenize(question.lower())
            
            # Remove stopwords and punctuation
            keywords = [
                self.lemmatizer.lemmatize(token) 
                for token in tokens 
                if token.isalnum() and token not in self.stop_words
            ]
            
            # Get POS tags for better filtering
            pos_tags = nltk.pos_tag(keywords)
            
            # Keep only nouns, verbs, adjectives
            important_pos = ['NN', 'NNS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'JJ']
            filtered_keywords = [
                word for word, pos in pos_tags 
                if pos[:2] in important_pos
            ]
            
            # Count frequency and sort
            keyword_freq = Counter(filtered_keywords)
            
            # Return top N keywords
            return [word for word, _ in keyword_freq.most_common(top_n)]
            
        except Exception as e:
            logger.error(f"Error in keyword extraction: {e}")
            # Fallback to simple extraction
            words = re.findall(r'\b\w{4,}\b', question.lower())
            return words[:top_n]
    
    def detect_question_type(self, question: str) -> QuestionType:
        """Detect the type of question for better answer structure"""
        question_lower = question.lower().strip()
        
        # Pattern matching for question types
        patterns = {
            QuestionType.WHAT: r'^what|what\s+is|what\s+are',
            QuestionType.WHY: r'^why|why\s+do|why\s+does|reason',
            QuestionType.HOW: r'^how|how\s+to|how\s+do|method|process',
            QuestionType.WHEN: r'^when|what\s+time|what\s+date',
            QuestionType.WHERE: r'^where|location|place',
            QuestionType.WHO: r'^who|person|people',
            QuestionType.COMPARE: r'compare|difference|vs|versus|similar',
            QuestionType.DEFINE: r'define|definition|meaning',
            QuestionType.LIST: r'list|enumerate|examples|types',
            QuestionType.EXPLAIN: r'explain|describe|elaborate'
        }
        
        for q_type, pattern in patterns.items():
            if re.search(pattern, question_lower):
                return q_type
                
        return QuestionType.UNKNOWN
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text"""
        # Simple entity extraction (can be enhanced with spaCy)
        entities = []
        
        # Find capitalized words (potential proper nouns)
        words = word_tokenize(text)
        pos_tags = nltk.pos_tag(words)
        
        for word, pos in pos_tags:
            if pos == 'NNP' or pos == 'NNPS':  # Proper nouns
                entities.append(word)
        
        return list(set(entities))
    
    def calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score using TF-IDF and cosine similarity"""
        try:
            # Create TF-IDF vectors
            documents = [text] + keywords
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            
            # Calculate cosine similarity between text and keywords
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            return float(np.mean(similarity))
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            # Fallback to simple keyword matching
            text_lower = text.lower()
            matches = sum(1 for k in keywords if k.lower() in text_lower)
            return matches / len(keywords) if keywords else 0
    
    def generate_answer_structure(self, question_type: QuestionType, mode: AnswerMode) -> Dict:
        """Generate answer structure based on question type and mode"""
        
        structures = {
            QuestionType.WHAT: {
                'tiny': ['definition'],
                'short': ['definition', 'key_points'],
                'medium': ['definition', 'key_points', 'examples'],
                'long': ['definition', 'key_points', 'examples', 'applications'],
                'comprehensive': ['definition', 'key_points', 'examples', 'applications', 'related_concepts']
            },
            QuestionType.HOW: {
                'tiny': ['brief_explanation'],
                'short': ['explanation', 'steps'],
                'medium': ['explanation', 'steps', 'example'],
                'long': ['explanation', 'steps', 'example', 'best_practices'],
                'comprehensive': ['explanation', 'steps', 'example', 'best_practices', 'common_pitfalls']
            },
            QuestionType.WHY: {
                'tiny': ['reason'],
                'short': ['reason', 'explanation'],
                'medium': ['reason', 'explanation', 'evidence'],
                'long': ['reason', 'explanation', 'evidence', 'implications'],
                'comprehensive': ['reason', 'explanation', 'evidence', 'implications', 'alternatives']
            }
        }
        
        # Default structure for unknown types
        default = {
            'tiny': ['summary'],
            'short': ['summary', 'details'],
            'medium': ['summary', 'details', 'context'],
            'long': ['summary', 'details', 'context', 'examples'],
            'comprehensive': ['summary', 'details', 'context', 'examples', 'additional_info']
        }
        
        return structures.get(question_type, default).get(mode.value, default['short'])
    
    def generate_dynamic_answer(self, 
                               topic: str, 
                               content: str,
                               question: str,
                               mode: AnswerMode = AnswerMode.MEDIUM) -> Dict[str, Any]:
        """Generate intelligent answer with context awareness"""
        
        # Extract information
        keywords = self.extract_keywords_advanced(question)
        question_type = self.detect_question_type(question)
        entities = self.extract_entities(question)
        relevance = self.calculate_relevance(content, keywords)
        
        # Get answer structure
        structure = self.generate_answer_structure(question_type, mode)
        
        # Create context
        context = AnswerContext(
            question=question,
            question_type=question_type,
            keywords=keywords,
            entities=entities,
            confidence=relevance,
            sources=['web_search'],
            timestamp=datetime.now()
        )
        
        # Tokenize content
        sentences = sent_tokenize(content)
        paragraphs = content.split('\n\n')
        
        # Build answer based on structure
        answer_parts = []
        
        for section in structure:
            if section == 'definition' and sentences:
                answer_parts.append(f"📌 **Definition:**\n{sentences[0]}")
                
            elif section == 'key_points' and sentences:
                points = sentences[1:4]  # Next 3 sentences as key points
                bullet_points = '\n'.join([f"• {p}" for p in points if p])
                if bullet_points:
                    answer_parts.append(f"🔑 **Key Points:**\n{bullet_points}")
                    
            elif section == 'examples' and len(sentences) > 4:
                examples = sentences[4:7]
                if examples:
                    answer_parts.append(f"💡 **Examples:**\n" + "\n".join(examples))
                    
            elif section == 'explanation' and paragraphs:
                answer_parts.append(f"📝 **Detailed Explanation:**\n{paragraphs[0][:500]}")
                
            elif section == 'steps' and question_type == QuestionType.HOW:
                answer_parts.append(self.generate_how_to_steps(content))
                
            elif section == 'prevention' and 'security' in ' '.join(keywords):
                answer_parts.append(self.generate_security_prevention(topic))
        
        # Add context-aware insights
        insights = self.generate_insights(question_type, keywords, entities)
        if insights:
            answer_parts.append(f"🎯 **Key Insights:**\n{insights}")
        
        # Add confidence score
        confidence_message = self.get_confidence_message(relevance)
        answer_parts.append(f"\n---\n*{confidence_message}*")
        
        # Combine all parts
        final_answer = '\n\n'.join(answer_parts)
        
        # Trim based on mode
        final_answer = self.trim_answer(final_answer, mode)
        
        return {
            'answer': final_answer,
            'context': context,
            'metadata': {
                'question_type': question_type.value,
                'relevance_score': round(relevance * 100, 2),
                'keywords': keywords,
                'entities': entities,
                'structure_used': structure
            }
        }
    
    def generate_how_to_steps(self, content: str) -> str:
        """Generate step-by-step instructions for 'how' questions"""
        sentences = sent_tokenize(content)
        steps = []
        
        for i, sent in enumerate(sentences[:5], 1):
            # Look for action-oriented sentences
            if any(word in sent.lower() for word in ['step', 'first', 'then', 'next', 'finally']):
                steps.append(f"**Step {i}:** {sent}")
        
        if not steps and len(sentences) >= 3:
            # Generate generic steps
            for i, sent in enumerate(sentences[:4], 1):
                steps.append(f"**Step {i}:** {sent}")
        
        return '\n'.join(steps) if steps else "Steps not clearly defined."
    
    def generate_security_prevention(self, topic: str) -> str:
        """Generate security prevention tips"""
        prevention_tips = {
            'sql': [
                "• Use parameterized queries/prepared statements",
                "• Validate and sanitize all user inputs",
                "• Implement proper error handling",
                "• Use stored procedures",
                "• Apply least privilege principle"
            ],
            'xss': [
                "• Implement Content Security Policy (CSP)",
                "• Use output encoding/escaping",
                "• Validate input on server side",
                "• Use HTTP-only cookies",
                "• Sanitize HTML input"
            ],
            'general': [
                "• Regular security audits",
                "• Keep software updated",
                "• Use secure coding practices",
                "• Implement input validation",
                "• Follow defense in depth"
            ]
        }
        
        # Determine which category
        if 'sql' in topic.lower():
            tips = prevention_tips['sql']
        elif 'xss' in topic.lower() or 'script' in topic.lower():
            tips = prevention_tips['xss']
        else:
            tips = prevention_tips['general']
        
        return "🛡️ **Prevention Measures:**\n" + '\n'.join(tips)
    
    def generate_insights(self, q_type: QuestionType, keywords: List[str], entities: List[str]) -> str:
        """Generate additional insights based on question context"""
        insights = []
        
        # Add question-specific insights
        if q_type == QuestionType.WHY:
            insights.append("Understanding the reasoning behind this helps in better application")
        elif q_type == QuestionType.HOW:
            insights.append("Practical implementation requires practice and testing")
        elif q_type == QuestionType.COMPARE:
            insights.append("Consider your specific use case when choosing between options")
        
        # Add keyword-based insights
        if 'security' in keywords or 'vulnerability' in keywords:
            insights.append("Security is an ongoing process, not a one-time fix")
        
        if 'python' in keywords or 'programming' in keywords:
            insights.append("Best practices evolve with community standards")
        
        return ' '.join(insights) if insights else ""
    
    def get_confidence_message(self, relevance: float) -> str:
        """Generate confidence message based on relevance score"""
        if relevance > 0.8:
            return "✅ High confidence answer (strongly matches your query)"
        elif relevance > 0.5:
            return "⚠️ Medium confidence answer (partially matches your query)"
        else:
            return "❓ Low confidence answer (limited information available)"
    
    def trim_answer(self, answer: str, mode: AnswerMode) -> str:
        """Trim answer based on mode"""
        limits = {
            AnswerMode.TINY: 200,
            AnswerMode.SHORT: 500,
            AnswerMode.MEDIUM: 1500,
            AnswerMode.LONG: 3000,
            AnswerMode.COMPREHENSIVE: 5000
        }
        
        limit = limits.get(mode, 1500)
        
        if len(answer) > limit:
            # Try to cut at sentence boundary
            sentences = sent_tokenize(answer)
            trimmed = ""
            for sent in sentences:
                if len(trimmed) + len(sent) < limit:
                    trimmed += sent + " "
                else:
                    break
            return trimmed.strip() + "..."
        
        return answer
    
    def cache_answer(self, question: str, answer_data: Dict):
        """Cache answers for faster response"""
        cache_key = hashlib.md5(question.lower().encode()).hexdigest()
        self.answer_cache[cache_key] = {
            'data': answer_data,
            'timestamp': datetime.now()
        }
        
        # Clean old cache entries (older than 1 hour)
        current_time = datetime.now()
        self.answer_cache = {
            k: v for k, v in self.answer_cache.items()
            if (current_time - v['timestamp']).seconds < 3600
        }
    
    def get_cached_answer(self, question: str) -> Optional[Dict]:
        """Retrieve cached answer if available"""
        cache_key = hashlib.md5(question.lower().encode()).hexdigest()
        if cache_key in self.answer_cache:
            cache_entry = self.answer_cache[cache_key]
            # Check if cache is still valid (less than 30 minutes old)
            if (datetime.now() - cache_entry['timestamp']).seconds < 1800:
                return cache_entry['data']
        return None

# Simplified interface for backward compatibility
def extract_keyword(question: str) -> str:
    """Backward compatible keyword extraction"""
    ai_engine = AdvancedAIEngine()
    keywords = ai_engine.extract_keywords_advanced(question, top_n=1)
    return keywords[0] if keywords else question

def build_summary(texts: List[str], max_sentences: int = 8) -> str:
    """Enhanced summary builder"""
    if not texts:
        return "No relevant information found."
    
    ai_engine = AdvancedAIEngine()
    combined = " ".join(texts)
    
    # Use NLTK for better sentence tokenization
    sentences = sent_tokenize(combined)
    
    # Select most relevant sentences (first few usually contain main ideas)
    summary_sentences = sentences[:max_sentences]
    
    return ". ".join(summary_sentences) + "."

def build_answer(topic: str, text: str, mode: str = "medium") -> str:
    """Enhanced answer builder with NLP"""
    ai_engine = AdvancedAIEngine()
    
    # Convert string mode to AnswerMode enum
    mode_map = {
        "tiny": AnswerMode.TINY,
        "short": AnswerMode.SHORT,
        "medium": AnswerMode.MEDIUM,
        "long": AnswerMode.LONG,
        "comprehensive": AnswerMode.COMPREHENSIVE
    }
    
    answer_mode = mode_map.get(mode.lower(), AnswerMode.MEDIUM)
    
    # Generate intelligent answer
    result = ai_engine.generate_dynamic_answer(
        topic=topic,
        content=text,
        question=topic,  # Using topic as question for simplicity
        mode=answer_mode
    )
    
    # Format the output
    metadata = result['metadata']
    
    formatted_answer = f"""
{'='*60}
📌 TOPIC: {topic}
{'='*60}

{result['answer']}

{'─'*60}
📊 Analysis:
• Question Type: {metadata['question_type'].upper()}
• Relevance Score: {metadata['relevance_score']}%
• Key Terms: {', '.join(metadata['keywords'][:5])}
• Answer Structure: {' → '.join(metadata['structure_used'])}
{'='*60}
"""
    
    return formatted_answer

# Advanced usage example
if __name__ == "__main__":
    # Initialize AI engine
    ai = AdvancedAIEngine()
    
    # Test questions
    test_questions = [
        "What is SQL injection and how to prevent it?",
        "How does cross-site scripting work?",
        "Why is input validation important for security?"
    ]
    
    sample_content = """
    SQL injection is a code injection technique used to attack data-driven applications.
    Attackers insert malicious SQL statements into input fields for execution.
    Prevention methods include using parameterized queries and input validation.
    Always use prepared statements to separate SQL logic from data.
    """
    
    for question in test_questions:
        print(f"\n{'#'*60}")
        print(f"QUESTION: {question}")
        print('#'*60)
        
        # Generate answer
        result = ai.generate_dynamic_answer(
            topic=question,
            content=sample_content,
            question=question,
            mode=AnswerMode.MEDIUM
        )
        
        print(result['answer'])
        time.sleep(1)
