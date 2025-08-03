"""
Utility functions for text processing and other common tasks.
"""
import re

def clean_telegram_text(text):
    """
    Clean text for display like in Telegram.
    
    Args:
        text (str): Raw text to clean
        
    Returns:
        str: Cleaned text with proper formatting
    """
    if not text:
        return ''
    
    # Handle escaped newlines and convert them to actual newlines
    cleaned = text
    # Convert literal \n to actual newlines
    cleaned = cleaned.replace('\\n', '\n')
    
    # Remove tabs completely
    cleaned = cleaned.replace('\t', '')
    
    # Remove leading spaces from each line but preserve line breaks
    lines = cleaned.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove leading and trailing spaces from each line
        cleaned_line = line.strip()
        cleaned_lines.append(cleaned_line)
    
    # Join lines back with newlines
    cleaned = '\n'.join(cleaned_lines)
    
    # Remove excessive consecutive spaces within lines
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    # Remove special unicode characters that are not emojis
    cleaned = re.sub(r'[\u200B-\u200D\uFEFF]', '', cleaned)
    
    # Replace multiple line breaks with double line breaks (max 2 consecutive)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Remove leading/trailing whitespace from entire text
    cleaned = cleaned.strip()
    
    return cleaned

def register_filters(app):
    """Register Jinja2 template filters."""
    app.jinja_env.filters['clean_text'] = clean_telegram_text
