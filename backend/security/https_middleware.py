# HTTPS Security Middleware for Medical Device Compliance
# Requirement 9.2: HTTPS encryption for all Supabase cloud communications

from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import os

logger = logging.getLogger(__name__)

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS connections for production environments.
    Redirects HTTP requests to HTTPS for security compliance.
    """
    
    def __init__(self, app, force_https: bool = None):
        super().__init__(app)
        # Force HTTPS in production or when explicitly enabled
        self.force_https = force_https if force_https is not None else (
            os.getenv("ENVIRONMENT", "development").lower() == "production" or
            os.getenv("FORCE_HTTPS", "false").lower() == "true"
        )
        
    async def dispatch(self, request: Request, call_next):
        # Skip HTTPS enforcement for local development
        if not self.force_https:
            return await call_next(request)
            
        # Check if request is already HTTPS
        if request.url.scheme == "https":
            return await call_next(request)
            
        # Check for forwarded protocol headers (common in reverse proxy setups)
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto == "https":
            return await call_next(request)
            
        # Allow localhost and internal IPs for development
        host = request.client.host if request.client else ""
        if host in ["127.0.0.1", "localhost", "::1"] or host.startswith("192.168.") or host.startswith("10."):
            return await call_next(request)
            
        # Redirect HTTP to HTTPS
        https_url = request.url.replace(scheme="https")
        logger.warning(f"Redirecting HTTP request to HTTPS: {request.url} -> {https_url}")
        return RedirectResponse(url=str(https_url), status_code=301)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers for medical device compliance.
    Implements security best practices for healthcare applications.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers for medical device compliance
        security_headers = {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy for privacy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy for medical applications
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://*.supabase.co wss://*.supabase.co; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Strict Transport Security (HSTS) for HTTPS enforcement
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Permissions policy for medical device security
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(self), "
                "accelerometer=(self)"
            )
        }
        
        # Add security headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
            
        return response

def verify_supabase_https_config():
    """
    Verify that Supabase configuration uses HTTPS URLs.
    Requirement 9.2: HTTPS encryption for all Supabase cloud communications
    """
    supabase_url = os.getenv("SUPABASE_URL", "")
    
    if not supabase_url:
        logger.error("SUPABASE_URL environment variable not set")
        raise ValueError("SUPABASE_URL must be configured")
        
    if not supabase_url.startswith("https://"):
        logger.error(f"Supabase URL must use HTTPS: {supabase_url}")
        raise ValueError("SUPABASE_URL must use HTTPS protocol for security compliance")
        
    logger.info(f"Supabase HTTPS configuration verified: {supabase_url}")
    return True

def get_secure_supabase_config():
    """
    Get secure Supabase configuration with HTTPS enforcement.
    """
    verify_supabase_https_config()
    
    return {
        "url": os.getenv("SUPABASE_URL"),
        "key": os.getenv("SUPABASE_SERVICE_KEY"),
        "options": {
            # Force HTTPS for all requests
            "schema": "public",
            "headers": {
                "User-Agent": "Vertex-Rehabilitation-System/1.0"
            },
            # Additional security options
            "realtime": {
                "params": {
                    "eventsPerSecond": 10  # Rate limiting for security
                }
            }
        }
    }