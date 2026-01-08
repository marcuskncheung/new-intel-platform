# utils/helpers.py
# Common helper functions

from datetime import datetime
import pytz

# Hong Kong timezone
HK_TZ = pytz.timezone('Asia/Hong_Kong')


def get_hk_time():
    """Get current time in Hong Kong timezone"""
    return datetime.now(HK_TZ)


def utc_to_hk(utc_dt):
    """Convert UTC/naive datetime to Hong Kong time"""
    if utc_dt is None:
        return None
    if not isinstance(utc_dt, datetime):
        return utc_dt
    if utc_dt.tzinfo is None:
        # Assume UTC if no timezone
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(HK_TZ)


def format_hk_time(dt, format='%Y-%m-%d %H:%M:%S'):
    """Format datetime in Hong Kong timezone"""
    if dt is None:
        return ""
    if not isinstance(dt, datetime):
        return str(dt)
    try:
        hk_time = utc_to_hk(dt)
        return hk_time.strftime(format)
    except Exception:
        return str(dt)


def html_to_plain_text(html_content):
    """Enhanced HTML to plain text conversion for Excel export"""
    import re
    import html
    
    if not html_content:
        return ""
    
    text = html_content
    
    # Remove CSS styles
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'style\s*=\s*"[^"]*"', '', text, flags=re.IGNORECASE)
    text = re.sub(r'style\s*=\s*\'[^\']*\'', '', text, flags=re.IGNORECASE)
    
    # Remove VML and Office-specific markup
    text = re.sub(r'v\:.*?\{[^}]*\}', '', text)
    text = re.sub(r'o\:.*?\{[^}]*\}', '', text)
    text = re.sub(r'w\:.*?\{[^}]*\}', '', text)
    text = re.sub(r'\.shape\s*\{[^}]*\}', '', text)
    text = re.sub(r'\.style\d+\s*\{[^}]*\}', '', text)
    
    # Remove CSS selectors and rules
    text = re.sub(r'[a-zA-Z0-9_\-\.#]+\s*\{[^}]*\}', '', text)
    
    # Handle HTML tags
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<div[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h[1-6][^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</h[1-6]>', '\n', text, flags=re.IGNORECASE)
    
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def convert_plain_text_to_html(text):
    """Convert plain text email content to HTML format for consistent display."""
    import re
    import html
    
    if not text:
        return ''
    
    # Check if content is already HTML
    if re.search(r'<[^>]+>', text):
        return text
    
    # Escape HTML characters
    html_content = html.escape(text)
    
    # Convert line breaks to <br> tags
    html_content = html_content.replace('\n', '<br>\n')
    
    # Convert URLs to clickable links
    url_pattern = r'(https?://[^\s<>"]+)'
    html_content = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', html_content)
    
    # Convert email addresses to mailto links
    email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    html_content = re.sub(email_pattern, r'<a href="mailto:\1">\1</a>', html_content)
    
    # Wrap in basic HTML structure
    html_content = f'<div style="font-family: Arial, sans-serif; line-height: 1.6;">{html_content}</div>'
    
    return html_content
