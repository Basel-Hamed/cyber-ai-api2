"""
Advanced Text Formatter for Cyber AI Assistant
With multiple formatting styles, templates, and export options
"""

import re
import textwrap
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class FormatStyle(Enum):
    """Available formatting styles"""
    PLAIN = "plain"
    MARKDOWN = "markdown"
    HTML = "html"
    RICH = "rich"
    MINIMAL = "minimal"
    BULLET = "bullet"
    NUMBERED = "numbered"
    CODE = "code"

class OutputFormat(Enum):
    """Output format options"""
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"  # for future use

class SecurityTipLevel(Enum):
    """Security tip importance levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AdvancedFormatter:
    """Advanced text formatter with multiple features"""
    
    def __init__(self, 
                 line_width: int = 80,
                 indent_size: int = 4,
                 use_emoji: bool = True):
        """
        Initialize formatter
        
        Args:
            line_width: Maximum line width for wrapping
            indent_size: Number of spaces for indentation
            use_emoji: Use emoji indicators
        """
        self.line_width = line_width
        self.indent_size = indent_size
        self.use_emoji = use_emoji
        
        # Emoji mappings
        self.emoji_map = {
            'topic': '📌',
            'explanation': '📝',
            'security': '🔒',
            'warning': '⚠️',
            'tip': '💡',
            'example': '🔍',
            'prevention': '🛡️',
            'attack': '⚔️',
            'vulnerability': '🐛',
            'solution': '✅',
            'code': '💻',
            'output': '📊',
            'error': '❌',
            'success': '🎉',
            'info': 'ℹ️',
            'quote': '💬',
            'link': '🔗',
            'download': '📥',
            'upload': '📤',
            'time': '⏱️',
            'warning_high': '🔥',
            'warning_medium': '⚡',
            'warning_low': '⚠️'
        }
    
    def format_answer(self, 
                     text: str, 
                     mode: str = "medium",
                     style: FormatStyle = FormatStyle.RICH,
                     topic: Optional[str] = None,
                     include_security_tips: bool = True,
                     include_metadata: bool = True) -> str:
        """
        Format answer with advanced options
        
        Args:
            text: Text to format
            mode: Length mode (tiny/short/medium/long/comprehensive)
            style: Formatting style
            topic: Optional topic title
            include_security_tips: Include security tips
            include_metadata: Include metadata
        """
        try:
            if not text:
                return self._get_empty_message(style)
            
            # Trim based on mode
            text = self._trim_by_mode(text, mode)
            
            # Format based on style
            if style == FormatStyle.PLAIN:
                return self._format_plain(text, topic, include_security_tips)
            elif style == FormatStyle.MARKDOWN:
                return self._format_markdown(text, topic, include_security_tips, include_metadata)
            elif style == FormatStyle.HTML:
                return self._format_html(text, topic, include_security_tips, include_metadata)
            elif style == FormatStyle.RICH:
                return self._format_rich(text, topic, include_security_tips, include_metadata)
            elif style == FormatStyle.MINIMAL:
                return self._format_minimal(text)
            elif style == FormatStyle.BULLET:
                return self._format_bullet(text)
            elif style == FormatStyle.NUMBERED:
                return self._format_numbered(text)
            elif style == FormatStyle.CODE:
                return self._format_code(text)
            else:
                return self._format_rich(text, topic, include_security_tips, include_metadata)
                
        except Exception as e:
            logger.error(f"Error formatting answer: {e}")
            return text
    
    def _trim_by_mode(self, text: str, mode: str) -> str:
        """Trim text based on mode"""
        limits = {
            "tiny": 200,
            "short": 500,
            "medium": 1500,
            "long": 3000,
            "comprehensive": 5000
        }
        
        limit = limits.get(mode.lower(), 1500)
        
        if len(text) > limit:
            # Try to cut at sentence boundary
            sentences = re.split(r'(?<=[.!?])\s+', text)
            trimmed = ""
            for sent in sentences:
                if len(trimmed) + len(sent) < limit:
                    trimmed += sent + " "
                else:
                    break
            return trimmed.strip() + "..."
        
        return text
    
    def _get_empty_message(self, style: FormatStyle) -> str:
        """Get empty message based on style"""
        messages = {
            FormatStyle.PLAIN: "No information found.",
            FormatStyle.MARKDOWN: "_No information found._",
            FormatStyle.HTML: "<p><em>No information found.</em></p>",
            FormatStyle.RICH: f"{self._get_emoji('info')} No information found.",
            FormatStyle.MINIMAL: "-",
            FormatStyle.BULLET: "• No information found",
            FormatStyle.NUMBERED: "1. No information found",
            FormatStyle.CODE: "# No information found"
        }
        return messages.get(style, "No information found.")
    
    def _get_emoji(self, key: str) -> str:
        """Get emoji if enabled"""
        if self.use_emoji:
            return self.emoji_map.get(key, '•')
        return ''
    
    def _format_plain(self, text: str, topic: Optional[str], include_tips: bool) -> str:
        """Plain text formatting"""
        lines = []
        
        if topic:
            lines.append(f"Topic: {topic}")
            lines.append("-" * 40)
        
        lines.append(textwrap.fill(text, width=self.line_width))
        
        if include_tips:
            lines.extend([
                "",
                "Security Tips:",
                "- Always validate input",
                "- Use prepared statements",
                "- Keep software updated",
                "- Implement least privilege",
                "- Regular security audits"
            ])
        
        return "\n".join(lines)
    
    def _format_markdown(self, text: str, topic: Optional[str], 
                        include_tips: bool, include_metadata: bool) -> str:
        """Markdown formatting"""
        lines = []
        
        if topic:
            lines.append(f"# {topic}")
            lines.append("")
        
        lines.append(text)
        lines.append("")
        
        if include_tips:
            lines.extend([
                "## 🔒 Security Tips",
                "",
                "- **Input Validation**: Always validate and sanitize user input",
                "- **Prepared Statements**: Use parameterized queries for databases",
                "- **Updates**: Keep all software and dependencies updated",
                "- **Least Privilege**: Grant minimum necessary permissions",
                "- **Audit**: Regular security audits and penetration testing",
                "",
                "### Additional Recommendations",
                "1. Enable logging and monitoring",
                "2. Use HTTPS everywhere",
                "3. Implement CSP headers",
                "4. Regular backups",
                "5. Security training for developers"
            ])
        
        if include_metadata:
            lines.extend([
                "",
                "---",
                f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                f"*Format: Markdown*"
            ])
        
        return "\n".join(lines)
    
    def _format_html(self, text: str, topic: Optional[str], 
                    include_tips: bool, include_metadata: bool) -> str:
        """HTML formatting"""
        html = ['<div class="cyber-ai-answer">']
        
        if topic:
            html.append(f'<h2>{self._get_emoji("topic")} {topic}</h2>')
        
        # Convert text to paragraphs
        paragraphs = text.split('\n\n')
        for p in paragraphs:
            if p.strip():
                html.append(f'<p>{p}</p>')
        
        if include_tips:
            html.extend([
                '<div class="security-tips">',
                f'<h3>{self._get_emoji("security")} Security Tips</h3>',
                '<ul>',
                '<li><strong>Input Validation:</strong> Always validate and sanitize user input</li>',
                '<li><strong>Prepared Statements:</strong> Use parameterized queries for databases</li>',
                '<li><strong>Updates:</strong> Keep all software updated</li>',
                '<li><strong>Least Privilege:</strong> Grant minimum necessary permissions</li>',
                '</ul>',
                '</div>'
            ])
        
        if include_metadata:
            html.append(
                f'<p class="metadata"><small>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</small></p>'
            )
        
        html.append('</div>')
        
        # Add basic CSS
        css = """
        <style>
        .cyber-ai-answer { font-family: Arial, sans-serif; line-height: 1.6; }
        .security-tips { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .security-tips h3 { color: #dc3545; margin-top: 0; }
        .metadata { color: #6c757d; font-size: 0.8em; }
        </style>
        """
        
        return css + "\n".join(html)
    
    def _format_rich(self, text: str, topic: Optional[str], 
                    include_tips: bool, include_metadata: bool) -> str:
        """Rich text formatting with emojis and boxes"""
        lines = []
        width = self.line_width
        
        # Header
        lines.append("┌" + "─" * (width - 2) + "┐")
        
        if topic:
            title = f"{self._get_emoji('topic')} {topic}"
            lines.append(f"│{title.center(width - 2)}│")
            lines.append("├" + "─" * (width - 2) + "┤")
        
        # Content
        wrapped_lines = textwrap.wrap(text, width=width - 4)
        for line in wrapped_lines:
            lines.append(f"│  {line.ljust(width - 4)}│")
        
        if include_tips:
            lines.append("├" + "─" * (width - 2) + "┤")
            lines.append(f"│{self._get_emoji('security')} SECURITY TIPS".ljust(width - 2) + "│")
            
            tips = [
                f"{self._get_emoji('tip')} Validate all user input",
                f"{self._get_emoji('tip')} Use prepared statements",
                f"{self._get_emoji('tip')} Keep software updated",
                f"{self._get_emoji('tip')} Implement least privilege"
            ]
            
            for tip in tips:
                lines.append(f"│  {tip.ljust(width - 4)}│")
        
        if include_metadata:
            lines.append("├" + "─" * (width - 2) + "┤")
            timestamp = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            lines.append(f"│{timestamp.center(width - 2)}│")
        
        lines.append("└" + "─" * (width - 2) + "┘")
        
        return "\n".join(lines)
    
    def _format_minimal(self, text: str) -> str:
        """Minimal formatting"""
        return text.strip()
    
    def _format_bullet(self, text: str) -> str:
        """Bullet point formatting"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        bullets = [f"• {s}" for s in sentences if s.strip()]
        return "\n".join(bullets)
    
    def _format_numbered(self, text: str) -> str:
        """Numbered list formatting"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        numbered = [f"{i+1}. {s}" for i, s in enumerate(sentences) if s.strip()]
        return "\n".join(numbered)
    
    def _format_code(self, text: str) -> str:
        """Code block formatting"""
        return f"```\n{text}\n```"
    
    def format_security_finding(self, 
                               finding: Dict[str, Any],
                               style: FormatStyle = FormatStyle.RICH) -> str:
        """Format a security finding"""
        title = finding.get('title', 'Security Finding')
        description = finding.get('description', '')
        risk_level = finding.get('risk_level', 'medium')
        recommendation = finding.get('recommendation', '')
        
        risk_emojis = {
            'critical': '🔥',
            'high': '⚠️',
            'medium': '⚡',
            'low': 'ℹ️',
            'info': '📝'
        }
        
        emoji = risk_emojis.get(risk_level, '•')
        
        if style == FormatStyle.MARKDOWN:
            return f"""
### {emoji} {title}
**Risk Level:** {risk_level.upper()}
**Description:** {description}
**Recommendation:** {recommendation}
"""
        elif style == FormatStyle.HTML:
            return f"""
<div class="finding risk-{risk_level}">
    <h3>{emoji} {title}</h3>
    <p><strong>Risk Level:</strong> {risk_level.upper()}</p>
    <p><strong>Description:</strong> {description}</p>
    <p><strong>Recommendation:</strong> {recommendation}</p>
</div>
"""
        else:
            return f"""
{emoji} {title}
Risk Level: {risk_level.upper()}
Description: {description}
Recommendation: {recommendation}
"""
    
    def format_multiple_answers(self, 
                               answers: List[str],
                               titles: Optional[List[str]] = None,
                               style: FormatStyle = FormatStyle.RICH) -> str:
        """Format multiple answers"""
        formatted = []
        
        for i, answer in enumerate(answers):
            title = titles[i] if titles and i < len(titles) else f"Answer {i+1}"
            
            formatted.append(
                self.format_answer(
                    answer,
                    mode="medium",
                    style=style,
                    topic=title,
                    include_metadata=False
                )
            )
        
        if style == FormatStyle.RICH:
            separator = "\n" + "═" * self.line_width + "\n"
        elif style == FormatStyle.MARKDOWN:
            separator = "\n---\n"
        elif style == FormatStyle.HTML:
            separator = "<hr>"
        else:
            separator = "\n" + "-" * 40 + "\n"
        
        return separator.join(formatted)
    
    def format_for_chat(self, 
                       question: str,
                       answer: str,
                       style: FormatStyle = FormatStyle.RICH) -> str:
        """Format Q&A for chat display"""
        if style == FormatStyle.MARKDOWN:
            return f"""
**Q:** {question}

**A:** {answer}
"""
        elif style == FormatStyle.HTML:
            return f"""
<div class="chat-message question">
    <strong>Q:</strong> {question}
</div>
<div class="chat-message answer">
    <strong>A:</strong> {answer}
</div>
"""
        else:
            q_emoji = self._get_emoji('quote')
            a_emoji = self._get_emoji('tip')
            
            return f"""
{q_emoji} Q: {question}
{a_emoji} A: {answer}
{'-' * 40}
"""
    
    def generate_report_header(self, 
                              title: str,
                              style: FormatStyle = FormatStyle.RICH) -> str:
        """Generate report header"""
        if style == FormatStyle.RICH:
            return f"""
┌{"─" * 60}┐
│{title.center(60)}│
├{"─" * 60}┤
│{datetime.now().strftime('%Y-%m-%d %H:%M:%S').center(60)}│
└{"─" * 60}┘
"""
        elif style == FormatStyle.MARKDOWN:
            return f"# {title}\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n---\n"
        else:
            return f"{title}\n{'=' * 40}\n"
    
    def format_with_template(self, 
                           template: str,
                           **kwargs) -> str:
        """Format using a template"""
        try:
            return template.format(**kwargs)
        except Exception as e:
            logger.error(f"Template formatting error: {e}")
            return str(kwargs)

# Simplified function for backward compatibility
def format_answer(text: str, mode: str = "medium") -> str:
    """
    Simplified answer formatter
    (Backward compatible with your original function)
    """
    formatter = AdvancedFormatter(use_emoji=True)
    return formatter.format_answer(
        text=text,
        mode=mode,
        style=FormatStyle.RICH,
        topic="Cyber Security Analysis",
        include_security_tips=True,
        include_metadata=True
    )

# Advanced formatting functions
def format_advanced(text: str, 
                   mode: str = "medium",
                   style: str = "rich",
                   topic: Optional[str] = None) -> str:
    """Advanced formatting with style selection"""
    formatter = AdvancedFormatter()
    
    style_map = {
        "plain": FormatStyle.PLAIN,
        "markdown": FormatStyle.MARKDOWN,
        "html": FormatStyle.HTML,
        "rich": FormatStyle.RICH,
        "minimal": FormatStyle.MINIMAL,
        "bullet": FormatStyle.BULLET,
        "numbered": FormatStyle.NUMBERED,
        "code": FormatStyle.CODE
    }
    
    return formatter.format_answer(
        text=text,
        mode=mode,
        style=style_map.get(style, FormatStyle.RICH),
        topic=topic
    )

def format_security_report(findings: List[Dict]) -> str:
    """Format security findings as report"""
    formatter = AdvancedFormatter()
    
    lines = [
        formatter.generate_report_header("SECURITY ANALYSIS REPORT"),
        ""
    ]
    
    for finding in findings:
        lines.append(formatter.format_security_finding(finding))
        lines.append("")
    
    return "\n".join(lines)

# Example usage
if __name__ == "__main__":
    # Test the formatter
    sample_text = """
    SQL injection is a code injection technique used to attack data-driven applications. 
    Attackers insert malicious SQL statements into input fields for execution. 
    This can lead to unauthorized data access and manipulation.
    """
    
    print("="*60)
    print("BASIC FORMATTING")
    print("="*60)
    print(format_answer(sample_text, mode="short"))
    
    print("\n" + "="*60)
    print("MARKDOWN FORMATTING")
    print("="*60)
    print(format_advanced(sample_text, mode="medium", style="markdown"))
    
    print("\n" + "="*60)
    print("RICH FORMATTING WITH EMOJIS")
    print("="*60)
    print(format_advanced(sample_text, mode="medium", style="rich"))
