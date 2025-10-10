def split_email_thread(raw_body):
    # Simple split by lines starting with "From:" or "Sent:"
    import re
    blocks = re.split(r'(?=^From:|^Sent:)', raw_body, flags=re.MULTILINE)
    return [b.strip() for b in blocks if b.strip()]

def extract_meta_and_content(block):
    # Return first line as meta, rest as content
    lines = block.splitlines()
    if not lines:
        return ("", "")
    meta = lines[0]
    content = "\n".join(lines[1:]).strip()
    return (meta, content)

def generate_email_thread_blocks(raw_body):
    """
    Parse email body into thread blocks for comprehensive AI analysis
    Handles both HTML and plain text emails with proper thread extraction
    Returns list of dictionaries with content and metadata for each email in thread
    """
    import re
    
    if not raw_body:
        return [{'content': '', 'meta': 'No content'}]
    
    # Check if this is HTML content
    is_html = bool(re.search(r'<html|<body|<div|<p>', raw_body, re.IGNORECASE))
    
    if is_html:
        # Handle HTML email threading
        return parse_html_email_threads(raw_body)
    else:
        # Handle plain text email threading
        return parse_plain_text_threads(raw_body)

def parse_html_email_threads(html_body):
    """
    Parse HTML email body to extract threaded conversations
    """
    import re
    from html import unescape
    
    # SECURITY: Use industry-standard HTML sanitization library (CodeQL recommendation)
    try:
        import bleach
        BLEACH_AVAILABLE = True
    except ImportError:
        BLEACH_AVAILABLE = False
    
    # Remove HTML tags to get text content for analysis
    def strip_html_tags(html_text):
        """
        SECURITY FIX for CodeQL Alert #32: Bad HTML filtering regexp
        
        Uses industry-standard bleach library when available (CodeQL recommendation).
        Fallback to robust regex patterns for malformed HTML tags.
        """
        
        if BLEACH_AVAILABLE:
            # PREFERRED: Use bleach library for bulletproof HTML sanitization
            # This handles all edge cases including malformed tags
            clean_text = bleach.clean(html_text, tags=[], strip=True, strip_comments=True)
            # Clean up whitespace and return
            return re.sub(r'\s+', ' ', clean_text).strip()
        
        else:
            # FALLBACK: Enhanced regex approach for environments without bleach
            # Handle malformed closing tags like </script >, </script foo="bar">
            
            # Pass 1: Remove dangerous scripts - iterative to catch all variations
            old_content = ""
            while old_content != html_text:
                old_content = html_text
                # Match <script> with any attributes, content, and malformed </script> tags
                html_text = re.sub(r'<script[^>]*>.*?</script[^>]*>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
            
            # Pass 2: Remove dangerous styles with same approach
            old_content = ""
            while old_content != html_text:
                old_content = html_text
                html_text = re.sub(r'<style[^>]*>.*?</style[^>]*>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
            
            # Pass 3: Remove other dangerous tags with malformed closing tag handling
            for tag in ['iframe', 'object', 'embed', 'link', 'meta']:
                old_content = ""
                while old_content != html_text:
                    old_content = html_text
                    html_text = re.sub(f'<{tag}[^>]*>.*?</{tag}[^>]*>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
            
            # Pass 4: Remove remaining HTML tags with robust pattern
            while '<' in html_text and '>' in html_text:
                old_text = html_text
                # Remove well-formed tags
                html_text = re.sub(r'<[^<>]+>', '', html_text)
                # Remove malformed tags (security fix)
                html_text = re.sub(r'<[^>]*>', '', html_text)
                # Break if no changes (prevent infinite loop)
                if html_text == old_text:
                    break
            
            # Pass 5: Decode HTML entities
            html_text = unescape(html_text)
            
            # Pass 6: Clean up whitespace
            html_text = re.sub(r'\s+', ' ', html_text).strip()
            return html_text
    
    # Extract text content
    text_content = strip_html_tags(html_body)
    
    # Look for email thread separators in the text content
    thread_patterns = [
        r'From:\s*[^\n]+',
        r'Sent:\s*[^\n]+', 
        r'Date:\s*[^\n]+',
        r'To:\s*[^\n]+',
        r'Subject:\s*[^\n]+',
        r'-----\s*Original\s*Message\s*-----',
        r'________________________________',
        r'On\s+.+\s+wrote:',
        r'>+\s*From:',
        r'>+\s*Sent:',
        r'發件人:\s*[^\n]+',  # Chinese "From:"
        r'發送時間:\s*[^\n]+',  # Chinese "Sent:"
        r'主題:\s*[^\n]+',  # Chinese "Subject:"
    ]
    
    # Find all thread separator positions
    separators = []
    for pattern in thread_patterns:
        for match in re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE):
            separators.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'pattern': pattern
            })
    
    # Sort separators by position
    separators.sort(key=lambda x: x['start'])
    
    # Split content into blocks based on separators
    if not separators:
        # No threading found, return complete content
        return [{
            'content': text_content,
            'meta': 'Complete Email Content (HTML)',
            'block_number': 1,
            'original_html': html_body
        }]
    
    blocks = []
    current_pos = 0
    
    for i, sep in enumerate(separators):
        # Add content before this separator (if any)
        if sep['start'] > current_pos:
            pre_content = text_content[current_pos:sep['start']].strip()
            if pre_content and len(pre_content) > 50:  # Only add substantial content
                blocks.append({
                    'content': pre_content,
                    'meta': f'Email Content Block {len(blocks) + 1}',
                    'block_number': len(blocks) + 1
                })
        
        # Find the end of this email block (next separator or end of text)
        next_sep_start = separators[i + 1]['start'] if i + 1 < len(separators) else len(text_content)
        
        # Extract this email block
        block_content = text_content[sep['start']:next_sep_start].strip()
        if block_content:
            blocks.append({
                'content': block_content,
                'meta': f"Email Thread - {sep['text'][:50]}...",
                'block_number': len(blocks) + 1,
                'separator': sep['text']
            })
        
        current_pos = next_sep_start
    
    # If no blocks were created, return the original content
    if not blocks:
        blocks = [{
            'content': text_content,
            'meta': 'Complete Email Content (HTML Processed)',
            'block_number': 1,
            'original_html': html_body
        }]
    
    return blocks

def parse_plain_text_threads(text_body):
    """
    Parse plain text email body to extract threaded conversations
    """
    import re
    
    # Split by common email thread delimiters for plain text
    patterns = [
        r'(?=^From:)',
        r'(?=^Sent:)', 
        r'(?=^Date:)',
        r'(?=^>.*From:)',
        r'(?=^>.*Sent:)',
        r'(?=^-----Original Message-----)',
        r'(?=^________________________________)',
        r'(?=^On.*wrote:)',
        r'(?=^\s*From:.*[\r\n])',
        r'(?=^\s*Sent:.*[\r\n])'
    ]
    
    # Try each pattern and use the one that gives the most splits
    best_blocks = [text_body]
    
    for pattern in patterns:
        try:
            test_blocks = re.split(pattern, text_body, flags=re.MULTILINE | re.IGNORECASE)
            test_blocks = [b.strip() for b in test_blocks if b.strip()]
            if len(test_blocks) > len(best_blocks):
                best_blocks = test_blocks
        except:
            continue
    
    # Convert to structured format
    thread_blocks = []
    for i, block in enumerate(best_blocks):
        if block.strip():
            # Extract metadata and content
            lines = block.strip().splitlines()
            meta_lines = []
            content_lines = []
            
            # Look for metadata patterns at start
            for j, line in enumerate(lines):
                if (line.startswith(('From:', 'Sent:', 'Date:', 'To:', 'Subject:')) or
                    line.strip().startswith('>') or
                    'wrote:' in line.lower() or
                    'original message' in line.lower()):
                    meta_lines.append(line)
                else:
                    # Rest is content
                    content_lines = lines[j:]
                    break
            
            meta = '\n'.join(meta_lines) if meta_lines else f'Email Thread Block {i+1}'
            content = '\n'.join(content_lines) if content_lines else block
            
            thread_blocks.append({
                'content': content.strip(),
                'meta': meta.strip(),
                'block_number': i + 1
            })
    
    # If no proper splits found, return original as single block
    if not thread_blocks:
        thread_blocks = [{
            'content': text_body.strip(),
            'meta': 'Complete Email Content (Plain Text)',
            'block_number': 1
        }]
    
    return thread_blocks