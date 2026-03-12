"""
Advanced Chat History Management System with Database Support and Analytics
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import os
import sqlite3
import csv
from pathlib import Path
import logging
import pickle
from collections import Counter
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageType(Enum):
    """Storage types for history"""
    MEMORY = "memory"      # In-memory storage
    SQLITE = "sqlite"      # SQLite database
    JSON = "json"          # JSON file
    CSV = "csv"            # CSV file

class ExportFormat(Enum):
    """Export formats"""
    JSON = "json"
    CSV = "csv"
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "md"

@dataclass
class ChatMessage:
    """Individual chat message"""
    question: str
    answer: str
    timestamp: datetime
    message_id: str
    session_id: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class ChatSession:
    """Chat session containing multiple messages"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    messages: List[ChatMessage]
    metadata: Dict[str, Any] = None
    
    def get_duration(self) -> timedelta:
        """Get session duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return datetime.now() - self.start_time
    
    def get_message_count(self) -> int:
        """Get number of messages"""
        return len(self.messages)
    
    def get_topics(self) -> List[str]:
        """Extract main topics from session"""
        all_text = ' '.join([msg.question + ' ' + msg.answer for msg in self.messages])
        words = re.findall(r'\b\w{4,}\b', all_text.lower())
        return list(set(Counter(words).most_common(5)))

class AdvancedChatHistory:
    """Advanced Chat History Management System"""
    
    def __init__(self, 
                 storage_type: StorageType = StorageType.MEMORY,
                 storage_path: str = "chat_history",
                 max_history_per_session: int = 50,
                 auto_save: bool = True):
        """
        Initialize chat history manager
        
        Args:
            storage_type: Type of storage to use
            storage_path: Path for file-based storage
            max_history_per_session: Max messages per session
            auto_save: Auto-save to storage
        """
        self.storage_type = storage_type
        self.storage_path = Path(storage_path)
        self.max_history_per_session = max_history_per_session
        self.auto_save = auto_save
        
        # In-memory storage
        self.sessions: Dict[str, ChatSession] = {}
        self.current_session_id = self._generate_session_id()
        
        # Statistics
        self.stats = {
            'total_messages': 0,
            'total_sessions': 0,
            'unique_users': set(),
            'popular_topics': Counter()
        }
        
        # Initialize storage
        self._initialize_storage()
        
        # Create new session
        self._create_new_session()
    
    def _initialize_storage(self):
        """Initialize storage based on type"""
        try:
            if self.storage_type == StorageType.SQLITE:
                self._init_sqlite()
            elif self.storage_type == StorageType.JSON:
                self._init_json()
            elif self.storage_type == StorageType.CSV:
                self._init_csv()
                
            # Load existing history
            self.load_history()
            
        except Exception as e:
            logger.error(f"Storage initialization failed: {e}")
            # Fallback to memory storage
            self.storage_type = StorageType.MEMORY
    
    def _init_sqlite(self):
        """Initialize SQLite database"""
        db_path = self.storage_path / "chat_history.db"
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                metadata TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT,
                question TEXT,
                answer TEXT,
                timestamp TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                message_id TEXT,
                rating INTEGER,
                feedback_text TEXT,
                timestamp TEXT,
                FOREIGN KEY (message_id) REFERENCES messages (message_id)
            )
        ''')
        
        self.conn.commit()
    
    def _init_json(self):
        """Initialize JSON storage"""
        json_path = self.storage_path / "chat_history.json"
        if not json_path.exists():
            with open(json_path, 'w') as f:
                json.dump({'sessions': [], 'messages': []}, f)
    
    def _init_csv(self):
        """Initialize CSV storage"""
        csv_path = self.storage_path / "chat_history.csv"
        if not csv_path.exists():
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'session_id', 'question', 'answer', 'metadata'])
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_hash = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        return f"session_{timestamp}_{random_hash}"
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"msg_{timestamp}"
    
    def _create_new_session(self):
        """Create a new chat session"""
        session = ChatSession(
            session_id=self.current_session_id,
            start_time=datetime.now(),
            end_time=None,
            messages=[],
            metadata={'user_agent': 'Unknown', 'ip': 'Local'}
        )
        self.sessions[self.current_session_id] = session
        self.stats['total_sessions'] += 1
    
    def save_chat(self, 
                  question: str, 
                  answer: str, 
                  metadata: Optional[Dict] = None,
                  session_id: Optional[str] = None) -> str:
        """
        Save chat message with advanced features
        
        Args:
            question: User question
            answer: AI answer
            metadata: Additional metadata
            session_id: Session ID (uses current if not provided)
        
        Returns:
            message_id of saved message
        """
        # Use provided session or current
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            session = self.sessions[self.current_session_id]
        
        # Create message
        message_id = self._generate_message_id()
        message = ChatMessage(
            question=question,
            answer=answer,
            timestamp=datetime.now(),
            message_id=message_id,
            session_id=session.session_id,
            metadata=metadata or {}
        )
        
        # Add to session
        session.messages.append(message)
        
        # Enforce max history per session
        if len(session.messages) > self.max_history_per_session:
            session.messages.pop(0)
        
        # Update statistics
        self.stats['total_messages'] += 1
        
        # Extract topics for stats
        self._update_topics(question, answer)
        
        # Auto-save if enabled
        if self.auto_save:
            self._persist_message(message)
        
        # Check if session is too long and create new if needed
        if len(session.messages) >= self.max_history_per_session:
            self.end_current_session()
            self.start_new_session()
        
        return message_id
    
    def _update_topics(self, question: str, answer: str):
        """Update topic statistics"""
        text = f"{question} {answer}".lower()
        words = re.findall(r'\b\w{4,}\b', text)
        for word in words[:10]:  # Limit to top words
            self.stats['popular_topics'][word] += 1
    
    def _persist_message(self, message: ChatMessage):
        """Persist message to storage"""
        try:
            if self.storage_type == StorageType.SQLITE:
                self._persist_to_sqlite(message)
            elif self.storage_type == StorageType.JSON:
                self._persist_to_json(message)
            elif self.storage_type == StorageType.CSV:
                self._persist_to_csv(message)
        except Exception as e:
            logger.error(f"Failed to persist message: {e}")
    
    def _persist_to_sqlite(self, message: ChatMessage):
        """Save to SQLite"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO messages 
                (message_id, session_id, question, answer, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                message.message_id,
                message.session_id,
                message.question,
                message.answer,
                message.timestamp.isoformat(),
                json.dumps(message.metadata)
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"SQLite persist failed: {e}")
    
    def _persist_to_json(self, message: ChatMessage):
        """Save to JSON file"""
        try:
            json_path = self.storage_path / "chat_history.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data['messages'].append(message.to_dict())
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"JSON persist failed: {e}")
    
    def _persist_to_csv(self, message: ChatMessage):
        """Save to CSV file"""
        try:
            csv_path = self.storage_path / "chat_history.csv"
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    message.timestamp.isoformat(),
                    message.session_id,
                    message.question,
                    message.answer,
                    json.dumps(message.metadata, ensure_ascii=False)
                ])
        except Exception as e:
            logger.error(f"CSV persist failed: {e}")
    
    def get_history(self, 
                   session_id: Optional[str] = None,
                   limit: int = 50,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   keyword: Optional[str] = None) -> List[Dict]:
        """
        Get chat history with filters
        
        Args:
            session_id: Filter by session
            limit: Maximum number of messages
            start_date: Filter by start date
            end_date: Filter by end date
            keyword: Filter by keyword
        
        Returns:
            List of chat messages as dictionaries
        """
        messages = []
        
        # Get messages from sessions
        for session in self.sessions.values():
            if session_id and session.session_id != session_id:
                continue
            
            for msg in session.messages:
                # Apply date filters
                if start_date and msg.timestamp < start_date:
                    continue
                if end_date and msg.timestamp > end_date:
                    continue
                
                # Apply keyword filter
                if keyword:
                    text = f"{msg.question} {msg.answer}".lower()
                    if keyword.lower() not in text:
                        continue
                
                messages.append(msg.to_dict())
        
        # Sort by timestamp (newest first) and limit
        messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return messages[:limit]
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Dict:
        """Get summary of a session"""
        if not session_id:
            session_id = self.current_session_id
        
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            'session_id': session.session_id,
            'duration': str(session.get_duration()),
            'message_count': session.get_message_count(),
            'topics': session.get_topics(),
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'metadata': session.metadata
        }
    
    def search_history(self, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Search chat history for specific text"""
        results = []
        query = query if case_sensitive else query.lower()
        
        for session in self.sessions.values():
            for msg in session.messages:
                question = msg.question if case_sensitive else msg.question.lower()
                answer = msg.answer if case_sensitive else msg.answer.lower()
                
                if query in question or query in answer:
                    results.append({
                        **msg.to_dict(),
                        'session_id': session.session_id
                    })
        
        return results
    
    def add_feedback(self, message_id: str, rating: int, feedback_text: str = ""):
        """Add user feedback for a message"""
        if self.storage_type == StorageType.SQLITE:
            try:
                self.cursor.execute('''
                    INSERT INTO feedback (message_id, rating, feedback_text, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (message_id, rating, feedback_text, datetime.now().isoformat()))
                self.conn.commit()
            except Exception as e:
                logger.error(f"Failed to add feedback: {e}")
    
    def export_history(self, 
                      format: ExportFormat = ExportFormat.JSON,
                      session_id: Optional[str] = None,
                      filepath: Optional[str] = None) -> str:
        """
        Export chat history to various formats
        
        Args:
            format: Export format
            session_id: Specific session to export
            filepath: Output file path
        
        Returns:
            Path to exported file
        """
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = self.storage_path / f"chat_export_{timestamp}.{format.value}"
        
        messages = self.get_history(session_id=session_id, limit=10000)
        
        if format == ExportFormat.JSON:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_date': datetime.now().isoformat(),
                    'total_messages': len(messages),
                    'messages': messages
                }, f, indent=2, ensure_ascii=False)
        
        elif format == ExportFormat.CSV:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'session_id', 'question', 'answer', 'metadata'])
                for msg in messages:
                    writer.writerow([
                        msg['timestamp'],
                        msg['session_id'],
                        msg['question'],
                        msg['answer'],
                        json.dumps(msg.get('metadata', {}))
                    ])
        
        elif format == ExportFormat.TEXT:
            with open(filepath, 'w', encoding='utf-8') as f:
                for msg in messages:
                    f.write(f"Q: {msg['question']}\n")
                    f.write(f"A: {msg['answer']}\n")
                    f.write(f"Time: {msg['timestamp']}\n")
                    f.write("-" * 50 + "\n\n")
        
        elif format == ExportFormat.HTML:
            self._export_to_html(messages, filepath)
        
        elif format == ExportFormat.MARKDOWN:
            self._export_to_markdown(messages, filepath)
        
        return str(filepath)
    
    def _export_to_html(self, messages: List[Dict], filepath: str):
        """Export to HTML format"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat History Export</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .message { margin: 20px 0; padding: 15px; border-radius: 8px; }
                .question { background: #e3f2fd; }
                .answer { background: #f1f8e9; }
                .timestamp { color: #666; font-size: 0.8em; }
                .session { border-bottom: 2px solid #ccc; margin: 30px 0; }
            </style>
        </head>
        <body>
            <h1>Chat History Export</h1>
            <p>Export Date: {export_date}</p>
            <p>Total Messages: {total}</p>
        """.format(export_date=datetime.now().isoformat(), total=len(messages))
        
        for msg in messages:
            html_content += f"""
            <div class="session">
                <div class="message question">
                    <div class="timestamp">{msg['timestamp']}</div>
                    <strong>Q:</strong> {msg['question']}
                </div>
                <div class="message answer">
                    <strong>A:</strong> {msg['answer']}
                </div>
            </div>
            """
        
        html_content += "</body></html>"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _export_to_markdown(self, messages: List[Dict], filepath: str):
        """Export to Markdown format"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Chat History Export\n\n")
            f.write(f"**Export Date:** {datetime.now().isoformat()}\n")
            f.write(f"**Total Messages:** {len(messages)}\n\n")
            
            for msg in messages:
                f.write(f"### {msg['timestamp']}\n\n")
                f.write(f"**Q:** {msg['question']}\n\n")
                f.write(f"**A:** {msg['answer']}\n\n")
                f.write("---\n\n")
    
    def get_statistics(self) -> Dict:
        """Get detailed statistics"""
        return {
            'total_messages': self.stats['total_messages'],
            'total_sessions': len(self.sessions),
            'current_session_messages': len(self.sessions[self.current_session_id].messages),
            'popular_topics': dict(self.stats['popular_topics'].most_common(10)),
            'storage_type': self.storage_type.value,
            'auto_save': self.auto_save
        }
    
    def start_new_session(self) -> str:
        """Start a new chat session"""
        self.current_session_id = self._generate_session_id()
        self._create_new_session()
        return self.current_session_id
    
    def end_current_session(self):
        """End current chat session"""
        if self.current_session_id in self.sessions:
            self.sessions[self.current_session_id].end_time = datetime.now()
            
            # Save session to storage
            if self.storage_type == StorageType.SQLITE:
                try:
                    session = self.sessions[self.current_session_id]
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO sessions (session_id, start_time, end_time, metadata)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        session.session_id,
                        session.start_time.isoformat(),
                        session.end_time.isoformat() if session.end_time else None,
                        json.dumps(session.metadata)
                    ))
                    self.conn.commit()
                except Exception as e:
                    logger.error(f"Failed to save session: {e}")
    
    def load_history(self):
        """Load history from storage"""
        if self.storage_type == StorageType.SQLITE:
            self._load_from_sqlite()
        elif self.storage_type == StorageType.JSON:
            self._load_from_json()
        elif self.storage_type == StorageType.CSV:
            self._load_from_csv()
    
    def _load_from_sqlite(self):
        """Load history from SQLite"""
        try:
            # Load sessions
            self.cursor.execute("SELECT * FROM sessions")
            for row in self.cursor.fetchall():
                session = ChatSession(
                    session_id=row[0],
                    start_time=datetime.fromisoformat(row[1]),
                    end_time=datetime.fromisoformat(row[2]) if row[2] else None,
                    messages=[],
                    metadata=json.loads(row[3]) if row[3] else {}
                )
                self.sessions[session.session_id] = session
            
            # Load messages
            self.cursor.execute("SELECT * FROM messages ORDER BY timestamp")
            for row in self.cursor.fetchall():
                message = ChatMessage(
                    message_id=row[0],
                    session_id=row[1],
                    question=row[2],
                    answer=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    metadata=json.loads(row[5]) if row[5] else {}
                )
                if message.session_id in self.sessions:
                    self.sessions[message.session_id].messages.append(message)
                    self.stats['total_messages'] += 1
            
        except Exception as e:
            logger.error(f"Failed to load from SQLite: {e}")
    
    def _load_from_json(self):
        """Load history from JSON"""
        try:
            json_path = self.storage_path / "chat_history.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for msg_data in data.get('messages', []):
                    message = ChatMessage.from_dict(msg_data)
                    if message.session_id not in self.sessions:
                        self.sessions[message.session_id] = ChatSession(
                            session_id=message.session_id,
                            start_time=message.timestamp,
                            end_time=None,
                            messages=[]
                        )
                    self.sessions[message.session_id].messages.append(message)
                    self.stats['total_messages'] += 1
        except Exception as e:
            logger.error(f"Failed to load from JSON: {e}")
    
    def _load_from_csv(self):
        """Load history from CSV"""
        try:
            csv_path = self.storage_path / "chat_history.csv"
            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        message = ChatMessage(
                            message_id=self._generate_message_id(),
                            session_id=row['session_id'],
                            question=row['question'],
                            answer=row['answer'],
                            timestamp=datetime.fromisoformat(row['timestamp']),
                            metadata=json.loads(row['metadata']) if row['metadata'] else {}
                        )
                        if message.session_id not in self.sessions:
                            self.sessions[message.session_id] = ChatSession(
                                session_id=message.session_id,
                                start_time=message.timestamp,
                                end_time=None,
                                messages=[]
                            )
                        self.sessions[message.session_id].messages.append(message)
                        self.stats['total_messages'] += 1
        except Exception as e:
            logger.error(f"Failed to load from CSV: {e}")
    
    def clear_history(self, session_id: Optional[str] = None):
        """Clear chat history"""
        if session_id:
            if session_id in self.sessions:
                del self.sessions[session_id]
        else:
            self.sessions.clear()
            self.stats['total_messages'] = 0
            self.stats['popular_topics'].clear()
            self.start_new_session()

# Simple interface for backward compatibility
history = []

def save_chat(question: str, answer: str, use_advanced: bool = False, **kwargs):
    """
    Save chat with optional advanced features
    """
    if use_advanced:
        # Use global advanced history manager
        if 'advanced_history' not in globals():
            globals()['advanced_history'] = AdvancedChatHistory()
        globals()['advanced_history'].save_chat(question, answer, **kwargs)
    else:
        # Simple in-memory storage for backward compatibility
        global history
        history.append({
            "question": question,
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })
        if len(history) > 10:
            history.pop(0)

def get_history(use_advanced: bool = False, **kwargs) -> List[Dict]:
    """
    Get chat history with optional filters
    """
    if use_advanced:
        if 'advanced_history' in globals():
            return globals()['advanced_history'].get_history(**kwargs)
        return []
    else:
        # Simple history for backward compatibility
        global history
        return history

# Advanced usage functions
def get_chat_statistics() -> Dict:
    """Get chat statistics"""
    if 'advanced_history' in globals():
        return globals()['advanced_history'].get_statistics()
    return {"total_messages": len(history) if 'history' in globals() else 0}

def export_chat_history(format: str = "json", filepath: Optional[str] = None) -> str:
    """Export chat history to file"""
    if 'advanced_history' in globals():
        format_enum = ExportFormat[format.upper()]
        return globals()['advanced_history'].export_history(format=format_enum, filepath=filepath)
    return ""

def search_chat_history(query: str) -> List[Dict]:
    """Search chat history"""
    if 'advanced_history' in globals():
        return globals()['advanced_history'].search_history(query)
    return []

# Example usage
if __name__ == "__main__":
    # Advanced usage
    print("="*60)
    print("ADVANCED CHAT HISTORY MANAGER")
    print("="*60)
    
    # Create advanced history manager
    history_mgr = AdvancedChatHistory(
        storage_type=StorageType.SQLITE,
        storage_path="./chat_data"
    )
    
    # Save some messages
    history_mgr.save_chat("What is Python?", "Python is a programming language")
    history_mgr.save_chat("How to learn Python?", "Practice coding daily", 
                         metadata={'topic': 'programming'})
    history_mgr.save_chat("What is AI?", "Artificial Intelligence", 
                         metadata={'difficulty': 'beginner'})
    
    # Get history with filters
    print("\nRecent History:")
    recent = history_mgr.get_history(limit=5)
    for msg in recent:
        print(f"Q: {msg['question']}")
        print(f"A: {msg['answer']}")
        print(f"Time: {msg['timestamp']}")
        print("-"*30)
    
    # Search history
    print("\nSearch Results for 'python':")
    results = history_mgr.search_history("python")
    for result in results:
        print(f"Found: {result['question']}")
    
    # Get statistics
    print("\nStatistics:")
    stats = history_mgr.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Export history
    export_file = history_mgr.export_history(format=ExportFormat.JSON)
    print(f"\nExported to: {export_file}")
    
    # Simple usage (backward compatible)
    print("\n" + "="*60)
    print("SIMPLE HISTORY (Backward Compatible)")
    print("="*60)
    
    save_chat("Hello", "Hi there!")
    save_chat("How are you?", "I'm fine, thanks!")
    
    simple_history = get_history()
    for item in simple_history:
        print(f"Q: {item['question']}")
        print(f"A: {item['answer']}")
        print("-"*20)
