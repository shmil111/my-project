#!/usr/bin/env python3
"""
Flask middleware for security checks and request verification.
"""
import logging
import ipaddress
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from flask import request, g, Response, jsonify
import re

# Import from local modules
from .utils import generate_request_id, mask_credential
from .credentials import log_credential_usage, verify_api_key

# Set up logging
logger = logging.getLogger(__name__)

# IP whitelist for trusted addresses
TRUSTED_IPS = [
    '127.0.0.1',          # localhost
    '10.0.0.0/8',         # private network
    '172.16.0.0/12',      # private network
    '192.168.0.0/16',     # private network
]

def is_ip_trusted(ip_address: str) -> bool:
    """
    Check if an IP address is in the trusted list.
    
    Args:
        ip_address: IP address to check
        
    Returns:
        True if trusted, False otherwise
    """
    if not ip_address:
        return False
        
    try:
        # Check exact matches
        if ip_address in TRUSTED_IPS:
            return True
            
        # Check CIDR ranges
        client_ip = ipaddress.ip_address(ip_address)
        for trusted_range in TRUSTED_IPS:
            if '/' in trusted_range:
                if client_ip in ipaddress.ip_network(trusted_range):
                    return True
    except (ValueError, TypeError) as e:
        logger.error(f"Error checking trusted IP: {e}")
        
    return False

def require_api_key(f: Callable) -> Callable:
    """
    Decorator to require a valid API key for route access.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify(error="API key is required"), 401
            
        request_id = generate_request_id()
        
        # Verify the API key
        if not verify_api_key(api_key, 
                             component='api', 
                             operation=request.endpoint, 
                             request_id=request_id,
                             ip_address=request.remote_addr,
                             user_agent=request.user_agent.string):
            return jsonify(error="Invalid API key"), 403
            
        # Store request ID in Flask global context
        g.request_id = request_id
        
        return f(*args, **kwargs)
    return decorated

def create_security_middleware(app):
    """
    Create security middleware for a Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        """Middleware function to run before each request."""
        # Add request ID to request context
        request_id = generate_request_id()
        g.request_id = request_id
        
        # Log request
        logger.info(f"Request: {request.method} {request.path} "
                   f"(request_id: {request_id}, ip: {request.remote_addr})")
        
        # Check if path is exempted from security checks
        exempt_paths = ['/health', '/metrics', '/docs', '/static']
        for path in exempt_paths:
            if request.path.startswith(path):
                return None
        
        # Check if IP is trusted for sensitive endpoints
        sensitive_patterns = [
            r'^/admin',
            r'^/security',
            r'^/credentials',
            r'/internal/',
        ]
        
        for pattern in sensitive_patterns:
            if re.match(pattern, request.path):
                if not is_ip_trusted(request.remote_addr):
                    logger.warning(f"Unauthorized access attempt to sensitive endpoint: "
                                  f"{request.path} from {request.remote_addr} "
                                  f"(request_id: {request_id})")
                    return jsonify(error="Access denied from untrusted IP"), 403

    @app.after_request
    def after_request(response):
        """Middleware function to run after each request."""
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
        
        # Log response status
        logger.info(f"Response: {response.status_code} "
                   f"(request_id: {g.get('request_id', 'unknown')})")
        
        return response
        
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle uncaught exceptions."""
        request_id = g.get('request_id', 'unknown')
        
        logger.error(f"Unhandled exception: {str(e)} "
                    f"(request_id: {request_id})", 
                    exc_info=True)
        
        return jsonify(error="Internal server error", 
                      request_id=request_id), 500
    
    # Register middleware functions
    logger.info("Security middleware initialized")
