import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from heapq import nlargest
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textstat
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedSummarizer:
    """Advanced Text Summarization Engine"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
    def extractive_summarize(self, texts: list, num_sentences: int = 10, 
                            min_sentence_length: int = 40, 
                            method: str = 'tfidf') -> str:
        """
        Advanced extractive summarization with multiple methods
        
        Args:
            texts: List of text strings
            num_sentences: Number of sentences in summary
            min_sentence_length: Minimum sentence length to include
            method: 'tfidf', 'frequency', 'position', or 'hybrid'
        """
        if not texts:
            return "No relevant information found from the learning sources."
        
        # Combine and clean texts
        combined = self.preprocess_texts(texts)
        
        # Split into sentences
        sentences = sent_tokenize(combined)
        
        # Clean and filter sentences
        sentences = self.clean_sentences(sentences, min_sentence_length)
        
        if len(sentences) <= num_sentences:
            return ' '.join(sentences)
        
        # Choose summarization method
        if method == 'tfidf':
            summary_sentences = self.tfidf_summarize(sentences, num_sentences)
        elif method == 'frequency':
            summary_sentences = self.frequency_summarize(sentences, num_sentences)
        elif method == 'position':
            summary_sentences = self.position_summarize(sentences, num_sentences)
        else:  # hybrid
            summary_sentences = self.hybrid_summarize(sentences, num_sentences)
        
        # Reconstruct summary
        summary = self.reconstruct_summary(sentences, summary_sentences)
        
        return summary
    
    def preprocess_texts(self, texts: list) -> str:
        """Combine and clean texts"""
        # Join texts
        combined = " ".join(texts)
        
        # Clean extra whitespace
        combined = re.sub(r'\s+', ' ', combined)
        
        # Remove special characters but keep sentence structure
        combined = re.sub(r'[^\w\s\.\!\?]', ' ', combined)
        
        return combined
    
    def clean_sentences(self, sentences: list, min_length: int) -> list:
        """Clean and filter sentences"""
        cleaned = []
        
        for sent in sentences:
            # Remove extra whitespace
            sent = ' '.join(sent.split())
            
            # Check minimum length
            if len(sent) >= min_length:
                cleaned.append(sent)
        
        return cleaned
    
    def tfidf_summarize(self, sentences: list, num_sentences: int) -> list:
        """Summarize using TF-IDF scores"""
        try:
            # Create TF-IDF matrix
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2)
            )
            
            # Fit and transform sentences
            tfidf_matrix = vectorizer.fit_transform(sentences)
            
            # Calculate sentence scores (sum of TF-IDF values)
            sentence_scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
            
            # Get top sentences
            top_indices = sentence_scores.argsort()[-num_sentences:][::-1]
            
            return [sentences[i] for i in sorted(top_indices)]
            
        except Exception as e:
            logger.error(f"TF-IDF summarization failed: {e}")
            return self.frequency_summarize(sentences, num_sentences)
    
    def frequency_summarize(self, sentences: list, num_sentences: int) -> list:
        """Summarize using word frequency"""
        # Tokenize all words
        words = word_tokenize(' '.join(sentences).lower())
        
        # Remove stopwords and punctuation
        words = [word for word in words 
                if word.isalnum() and word not in self.stop_words]
        
        # Calculate word frequencies
        word_freq = FreqDist(words)
        
        # Calculate sentence scores
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = word_tokenize(sentence.lower())
            score = sum(word_freq[word] for word in sentence_words 
                       if word in word_freq)
            sentence_scores[i] = score / len(sentence_words) if sentence_words else 0
        
        # Get top sentences
        top_indices = nlargest(num_sentences, sentence_scores, 
                              key=sentence_scores.get)
        
        return [sentences[i] for i in sorted(top_indices)]
    
    def position_summarize(self, sentences: list, num_sentences: int) -> list:
        """Summarize based on sentence position"""
        # Early sentences often contain important information
        sentence_scores = {}
        
        for i, sentence in enumerate(sentences):
            # Higher score for early sentences
            position_score = 1.0 - (i / len(sentences))
            
            # Boost for first and last sentences
            if i == 0 or i == len(sentences) - 1:
                position_score *= 2
            
            sentence_scores[i] = position_score
        
        # Get top sentences
        top_indices = nlargest(num_sentences, sentence_scores, 
                              key=sentence_scores.get)
        
        return [sentences[i] for i in sorted(top_indices)]
    
    def hybrid_summarize(self, sentences: list, num_sentences: int) -> list:
        """Combine multiple summarization methods"""
        # Get results from different methods
        tfidf_sentences = set(self.tfidf_summarize(sentences, num_sentences * 2))
        freq_sentences = set(self.frequency_summarize(sentences, num_sentences * 2))
        pos_sentences = set(self.position_summarize(sentences, num_sentences))
        
        # Combine scores
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            if sentence in tfidf_sentences:
                score += 3
            if sentence in freq_sentences:
                score += 2
            if sentence in pos_sentences:
                score += 1
            sentence_scores[i] = score
        
        # Get top sentences
        top_indices = nlargest(num_sentences, sentence_scores, 
                              key=sentence_scores.get)
        
        return [sentences[i] for i in sorted(top_indices)]
    
    def reconstruct_summary(self, original_sentences: list, 
                           selected_sentences: list) -> str:
        """Reconstruct summary maintaining original order"""
        # Find indices of selected sentences in original order
        indices = []
        for sent in selected_sentences:
            try:
                idx = original_sentences.index(sent)
                indices.append(idx)
            except ValueError:
                continue
        
        # Sort by original index
        indices.sort()
        
        # Build summary
        summary_sentences = [original_sentences[i] for i in indices]
        
        return ' '.join(summary_sentences)
    
    def abstractive_summarize(self, texts: list, max_length: int = 500) -> str:
        """
        Simple abstractive summarization using key phrase extraction
        """
        combined = self.preprocess_texts(texts)
        
        # Extract key phrases
        key_phrases = self.extract_key_phrases(combined, num_phrases=5)
        
        # Build abstractive summary
        summary = f"This text discusses: {', '.join(key_phrases)}. "
        
        # Add important sentences
        sentences = sent_tokenize(combined)
        important_sents = self.extract_important_sentences(sentences)
        
        if important_sents:
            summary += " Key points include: " + ' '.join(important_sents[:3])
        
        return summary[:max_length]
    
    def extract_key_phrases(self, text: str, num_phrases: int = 5) -> list:
        """Extract key phrases using NLTK"""
        words = word_tokenize(text.lower())
        
        # Get POS tags
        pos_tags = nltk.pos_tag(words)
        
        # Extract noun phrases
        phrases = []
        current_phrase = []
        
        for word, pos in pos_tags:
            if pos.startswith('NN') or pos.startswith('JJ'):
                current_phrase.append(word)
            else:
                if len(current_phrase) > 1:
                    phrases.append(' '.join(current_phrase))
                current_phrase = []
        
        if len(current_phrase) > 1:
            phrases.append(' '.join(current_phrase))
        
        # Count phrase frequencies
        phrase_freq = Counter(phrases)
        
        # Return most common phrases
        return [phrase for phrase, _ in phrase_freq.most_common(num_phrases)]
    
    def extract_important_sentences(self, sentences: list, num_sentences: int = 3) -> list:
        """Extract most important sentences"""
        if len(sentences) <= num_sentences:
            return sentences
        
        # Score sentences based on length and content words
        sentence_scores = []
        
        for sent in sentences:
            words = word_tokenize(sent.lower())
            content_words = [w for w in words if w.isalnum() and w not in self.stop_words]
            
            # Score based on number of content words
            score = len(content_words)
            
            sentence_scores.append((sent, score))
        
        # Sort by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [sent for sent, _ in sentence_scores[:num_sentences]]
    
    def summarize_with_stats(self, texts: list, **kwargs) -> dict:
        """
        Summarize and return statistics
        """
        summary = self.extractive_summarize(texts, **kwargs)
        
        # Calculate statistics
        original_length = sum(len(t.split()) for t in texts)
        summary_length = len(summary.split())
        
        stats = {
            'summary': summary,
            'original_word_count': original_length,
            'summary_word_count': summary_length,
            'compression_ratio': f"{(summary_length/original_length*100):.1f}%",
            'readability_score': textstat.flesch_reading_ease(summary),
            'num_sentences': len(sent_tokenize(summary))
        }
        
        return stats
    
    def multi_document_summarize(self, document_groups: list, 
                                 summaries_per_group: int = 5) -> str:
        """
        Summarize multiple document groups
        """
        all_summaries = []
        
        for i, docs in enumerate(document_groups):
            group_summary = self.extractive_summarize(
                docs, 
                num_sentences=summaries_per_group
            )
            all_summaries.append(f"[Source {i+1}] {group_summary}")
        
        # Combine group summaries
        combined = ' '.join(all_summaries)
        
        # Final summary
        final_summary = self.extractive_summarize(
            [combined], 
            num_sentences=summaries_per_group
        )
        
        return final_summary

# Simplified version for backward compatibility
def summarize(texts: list, num_sentences: int = 10, 
             min_length: int = 40, method: str = 'hybrid') -> str:
    """
    Enhanced summarize function with multiple options
    
    Args:
        texts: List of text strings
        num_sentences: Number of sentences in summary
        min_length: Minimum sentence length
        method: 'tfidf', 'frequency', 'position', or 'hybrid'
    """
    summarizer = AdvancedSummarizer()
    return summarizer.extractive_summarize(
        texts, 
        num_sentences=num_sentences,
        min_sentence_length=min_length,
        method=method
    )

# Advanced usage with statistics
def summarize_advanced(texts: list, **kwargs) -> dict:
    """
    Advanced summarization with statistics
    """
    summarizer = AdvancedSummarizer()
    return summarizer.summarize_with_stats(texts, **kwargs)

# Multi-document summarization
def summarize_multiple(document_groups: list, **kwargs) -> str:
    """
    Summarize multiple document groups
    """
    summarizer = AdvancedSummarizer()
    return summarizer.multi_document_summarize(document_groups, **kwargs)

# Example usage and testing
if __name__ == "__main__":
    # Sample texts
    sample_texts = [
        "SQL injection is a code injection technique used to attack data-driven applications. Attackers insert malicious SQL statements into input fields for execution. This can lead to unauthorized data access and manipulation.",
        "Prevention methods include using parameterized queries and input validation. Always use prepared statements to separate SQL logic from data. Implement proper error handling to avoid information leakage.",
        "Security testing should include automated scanning and manual penetration testing. Regular security audits help identify vulnerabilities. Training developers on secure coding practices is essential."
    ]
    
    print("="*60)
    print("BASIC SUMMARIZATION")
    print("="*60)
    summary = summarize(sample_texts)
    print(summary)
    
    print("\n" + "="*60)
    print("ADVANCED SUMMARIZATION WITH STATS")
    print("="*60)
    result = summarize_advanced(sample_texts, method='hybrid')
    print(f"Summary: {result['summary']}")
    print(f"\nStatistics:")
    print(f"- Original words: {result['original_word_count']}")
    print(f"- Summary words: {result['summary_word_count']}")
    print(f"- Compression: {result['compression_ratio']}")
    print(f"- Readability: {result['readability_score']}")
    
    print("\n" + "="*60)
    print("DIFFERENT SUMMARIZATION METHODS")
    print("="*60)
    
    methods = ['tfidf', 'frequency', 'position', 'hybrid']
    for method in methods:
        summary = summarize(sample_texts, method=method, num_sentences=5)
        print(f"\n{method.upper()} method:")
        print(summary[:150] + "...")
