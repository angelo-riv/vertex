# Authentication and Authorization Middleware
# Requirement 9.3: Implement proper authentication and authorization for database access

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import hashlib
import hmac

logger = logging.getLogger(__name__)

# Security bearer for JWT token extraction
security = HTTPBearer(auto_error=False)

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for authentication and authorization of API requests.
    Implements role-based access control for medical device security.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/",
            "/docs",
            "/openapi.json",
            "/api/health",
            "/api/demo/status",
            "/api/demo/scenarios"
        }
        
        # ESP32 device endpoints (use device authentication)
        self.device_endpoints = {
            "/api/sensor-data",
            "/api/sensor-data/test"
        }
        
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        if request.url.path in self.public_endpoints:
            return await call_next(request)
            
        # Handle ESP32 device authentication
        if request.url.path in self.device_endpoints:
            if not await self._authenticate_device(request):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid device authentication"
                )
            return await call_next(request)
            
        # Handle user authentication for other endpoints
        if not await self._authenticate_user(request):
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
            
        return await call_next(request)
    
    async def _authenticate_device(self, request: Request) -> bool:
        """
        Authenticate ESP32 device requests using device ID and signature.
        """
        try:
            # Extract device authentication from headers
            device_id = request.headers.get("X-Device-ID")
            device_signature = request.headers.get("X-Device-Signature")
            timestamp = request.headers.get("X-Timestamp")
            
            if not all([device_id, device_signature, timestamp]):
                logger.warning(f"Missing device authentication headers from {request.client.host}")
                return False
                
            # Verify device ID format
            if not device_id.startswith("ESP32_"):
                logger.warning(f"Invalid device ID format: {device_id}")
                return False
                
            # Verify timestamp (prevent replay attacks)
            try:
                request_time = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
                current_time = datetime.now(timezone.utc)
                time_diff = abs((current_time - request_time).total_seconds())
                
                if time_diff > 300:  # 5 minutes tolerance
                    logger.warning(f"Device request timestamp too old: {time_diff}s")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid timestamp format: {timestamp}")
                return False
                
            # Verify device signature (simplified for demo - use proper device certificates in production)
            device_secret = os.getenv("DEVICE_SECRET", "device-secret-key")
            expected_signature = hmac.new(
                device_secret.encode(),
                f"{device_id}:{timestamp}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(device_signature, expected_signature):
                logger.warning(f"Invalid device signature for {device_id}")
                return False
                
            # Store device info in request state
            request.state.device_id = device_id
            request.state.authenticated_device = True
            
            logger.debug(f"Device authenticated successfully: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Device authentication error: {str(e)}")
            return False
    
    async def _authenticate_user(self, request: Request) -> bool:
        """
        Authenticate user requests using JWT tokens from Supabase.
        """
        try:
            # Extract JWT token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.debug("No valid Authorization header found")
                return False
                
            token = auth_header.split(" ")[1]
            
            # Verify JWT token (simplified - use proper Supabase JWT verification in production)
            try:
                # In production, verify with Supabase JWT secret
                payload = jwt.decode(
                    token,
                    self.supabase_jwt_secret or self.jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_exp": True}
                )
                
                # Extract user information
                user_id = payload.get("sub")
                user_role = payload.get("role", "authenticated")
                user_email = payload.get("email")
                
                if not user_id:
                    logger.warning("JWT token missing user ID")
                    return False
                    
                # Store user info in request state
                request.state.user_id = user_id
                request.state.user_role = user_role
                request.state.user_email = user_email
                request.state.authenticated_user = True
                
                logger.debug(f"User authenticated successfully: {user_email}")
                return True
                
            except jwt.ExpiredSignatureError:
                logger.warning("JWT token has expired")
                return False
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"User authentication error: {str(e)}")
            return False

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from request state.
    """
    if not getattr(request.state, "authenticated_user", False):
        return None
        
    return {
        "user_id": getattr(request.state, "user_id", None),
        "user_role": getattr(request.state, "user_role", None),
        "user_email": getattr(request.state, "user_email", None)
    }

def get_current_device(request: Request) -> Optional[str]:
    """
    Get current authenticated device ID from request state.
    """
    if not getattr(request.state, "authenticated_device", False):
        return None
        
    return getattr(request.state, "device_id", None)

def require_role(required_role: str):
    """
    Dependency to require specific user role for endpoint access.
    """
    def role_checker(request: Request):
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        user_role = user.get("user_role", "")
        if user_role != required_role and user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail=f"Role '{required_role}' required for this operation"
            )
            
        return user
    
    return role_checker

def require_therapist_role():
    """
    Dependency to require therapist role for clinical threshold configuration.
    Therapists and admins can configure patient-specific thresholds.
    """
    def therapist_role_checker(request: Request):
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        user_role = user.get("user_role", "")
        if user_role not in ["therapist", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Therapist role required for threshold configuration"
            )
            
        return user
    
    return therapist_role_checker

def require_clinical_access():
    """
    Dependency to require clinical access for ESP32 device management and clinical analytics.
    Therapists, clinicians, and admins can access clinical features.
    """
    def clinical_access_checker(request: Request):
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        user_role = user.get("user_role", "")
        if user_role not in ["therapist", "clinician", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="Clinical access required for this operation"
            )
            
        return user
    
def require_patient_access(patient_id: str):
    """
    Dependency to ensure user can only access their own patient data.
    """
    def patient_access_checker(request: Request):
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
            
        user_id = user.get("user_id")
        user_role = user.get("user_role", "")
        
        # Admin, therapist, and clinician roles can access any patient data
        if user_role in ["admin", "therapist", "clinician"]:
            return user
            
        # Regular users can only access their own data
        if user_id != patient_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: can only access own patient data"
            )
            
        return user
    
    return patient_access_checker

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for API security.
    Prevents abuse and ensures system stability.
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # In production, use Redis or similar
        
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_minute = datetime.now().minute
        
        # Create key for rate limiting
        rate_limit_key = f"{client_ip}:{current_minute}"
        
        # Check current request count
        current_count = self.request_counts.get(rate_limit_key, 0)
        
        if current_count >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}: {current_count} requests")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
            
        # Increment request count
        self.request_counts[rate_limit_key] = current_count + 1
        
        # Clean up old entries (simple cleanup - use proper TTL in production)
        if len(self.request_counts) > 1000:
            # Keep only current and previous minute
            keys_to_keep = [
                f"{client_ip}:{current_minute}",
                f"{client_ip}:{(current_minute - 1) % 60}"
            ]
            self.request_counts = {
                k: v for k, v in self.request_counts.items()
                if any(k.endswith(f":{minute}") for minute in [current_minute, (current_minute - 1) % 60])
            }
            
        return await call_next(request)