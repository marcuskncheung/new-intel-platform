#!/usr/bin/env python3
"""
Input Validation and Sanitization Module
Provides comprehensive input validation and XSS protection
"""

import re
import html
import bleach
from urllib.parse import urlparse
from flask import request, abort

class InputValidator:
    """Input validation and sanitization utilities"""
    
    # Allowed HTML tags for rich text content
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
    ]
    
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
        'a': ['href', 'title'],
    }
    
    @staticmethod
    def sanitize_html(content):
        """Sanitize HTML content to prevent XSS"""
        if not content:
            return content
        
        return bleach.clean(
            content, 
            tags=InputValidator.ALLOWED_TAGS,
            attributes=InputValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def escape_html(content):
        """Escape HTML entities"""
        if not content:
            return content
        return html.escape(str(content))
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_case_number(case_number):
        """Validate case number format"""
        if not case_number:
            return False
        
        # Pattern: A-Z{1,3} followed by 4 digits, hyphen, 3-4 digits
        pattern = r'^[A-Z]{1,3}[0-9]{4}-[0-9]{3,4}$'
        return re.match(pattern, case_number) is not None
    
    @staticmethod
    def validate_filename(filename):
        """Validate and sanitize filename"""
        if not filename:
            return False
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Check for allowed extensions
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif'}
        extension = '.' + filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        return extension in allowed_extensions and len(filename) <= 255
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        if not url:
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def sanitize_search_query(query):
        """Sanitize search query to prevent injection"""
        if not query:
            return ""
        
        # Remove potentially dangerous characters
        query = re.sub(r'[<>"\';(){}[\]\\]', '', str(query))
        
        # Limit length
        return query[:200].strip()
    
    @staticmethod
    def validate_pagination(page, per_page=None):
        """Validate pagination parameters"""
        try:
            page = int(page) if page else 1
            per_page = int(per_page) if per_page else 20
            
            # Reasonable limits
            page = max(1, min(page, 10000))
            per_page = max(1, min(per_page, 100))
            
            return page, per_page
        except (ValueError, TypeError):
            return 1, 20
    
    @staticmethod
    def validate_date_range(start_date, end_date):
        """Validate date range inputs"""
        from datetime import datetime, timedelta
        
        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Reasonable date range (not more than 5 years)
            max_range = timedelta(days=1825)  # 5 years
            if start_date and end_date:
                if end_date - start_date > max_range:
                    return None, None
                if start_date > end_date:
                    return None, None
            
            return start_date, end_date
        except (ValueError, TypeError):
            return None, None

class CSRFProtection:
    """CSRF protection utilities"""
    
    @staticmethod
    def validate_request_method(allowed_methods=None):
        """Validate HTTP request method"""
        if allowed_methods is None:
            allowed_methods = ['GET', 'POST']
        
        if request.method not in allowed_methods:
            abort(405)  # Method not allowed
    
    @staticmethod
    def validate_content_type():
        """Validate content type for POST requests"""
        if request.method == 'POST':
            content_type = request.content_type
            if content_type and not content_type.startswith(('application/x-www-form-urlencoded', 'multipart/form-data')):
                if not content_type.startswith('application/json'):
                    abort(400)  # Bad request

class RateLimiting:
    """Basic rate limiting utilities"""
    
    _request_counts = {}
    
    @staticmethod
    def check_rate_limit(identifier, max_requests=100, window_minutes=60):
        """Basic rate limiting check"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old entries
        RateLimiting._request_counts = {
            k: v for k, v in RateLimiting._request_counts.items()
            if v['timestamp'] > window_start
        }
        
        # Check current count
        if identifier in RateLimiting._request_counts:
            count = RateLimiting._request_counts[identifier]['count']
            if count >= max_requests:
                return False
            RateLimiting._request_counts[identifier]['count'] += 1
        else:
            RateLimiting._request_counts[identifier] = {
                'count': 1,
                'timestamp': now
            }
        
        return True

def validate_form_input(form_data, validation_rules):
    """Validate form input against rules"""
    errors = {}
    cleaned_data = {}
    
    for field, rules in validation_rules.items():
        value = form_data.get(field)
        
        # Required field check
        if rules.get('required') and not value:
            errors[field] = 'This field is required'
            continue
        
        if not value:
            cleaned_data[field] = None
            continue
        
        # Type validation
        field_type = rules.get('type', 'string')
        if field_type == 'email' and not InputValidator.validate_email(value):
            errors[field] = 'Invalid email format'
            continue
        elif field_type == 'case_number' and not InputValidator.validate_case_number(value):
            errors[field] = 'Invalid case number format'
            continue
        elif field_type == 'url' and not InputValidator.validate_url(value):
            errors[field] = 'Invalid URL format'
            continue
        
        # Length validation
        max_length = rules.get('max_length')
        if max_length and len(str(value)) > max_length:
            errors[field] = f'Maximum length is {max_length} characters'
            continue
        
        min_length = rules.get('min_length')
        if min_length and len(str(value)) < min_length:
            errors[field] = f'Minimum length is {min_length} characters'
            continue
        
        # Sanitization
        if rules.get('sanitize_html'):
            value = InputValidator.sanitize_html(value)
        elif rules.get('escape_html'):
            value = InputValidator.escape_html(value)
        elif rules.get('sanitize_search'):
            value = InputValidator.sanitize_search_query(value)
        
        cleaned_data[field] = value
    
    return cleaned_data, errors
