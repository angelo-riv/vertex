# Secure Logging System for Medical Device Compliance
# Requirement 9.5: Exclude personally identifiable information from debug logs

import logging
import re
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime
import os

class PIIFilter(logging.Filter):
    """
    Logging filter to remove or mask personally identifiable information (PII)
    from log messages to ensure HIPAA compliance and patient privacy.
    """
    
    def __init__(self):
        super().__init__()
        
        # PII patterns to detect and mask
        self.pii_patterns = [
            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            
            # Phone numbers (various formats)
            (r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', '[PHONE]'),
            
            # Social Security Numbers
            (r'\b\d{3}-?\d{2}-?\d{4}\b', '[SSN]'),
            
            # Credit card numbers (basic pattern)
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),
            
            # Names (when preceded by common identifiers)
            (r'(?i)\b(?:name|patient|user)[:=]\s*["\']?([A-Za-z\s]{2,30})["\']?', r'\1: [NAME]'),
            
            # Addresses (basic pattern)
            (r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b', '[ADDRESS]'),
            
            # IP addresses (for privacy)
            (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', '[IP]'),
            
            # UUIDs (patient IDs)
            (r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', '[UUID]'),
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [(re.compile(pattern), replacement) for pattern, replacement in self.pii_patterns]
        
        # Sensitive field names to mask in JSON/dict logs
        self.sensitive_fields = {
            'email', 'phone', 'full_name', 'name', 'address', 'ssn', 'social_security',
            'credit_card', 'password', 'token', 'secret', 'key', 'patient_name',
            'first_name', 'last_name', 'middle_name', 'birth_date', 'dob',
            'medical_record_number', 'mrn', 'insurance_number'
        }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to remove PII before logging.
        """
        try:
            # Clean the main log message
            if hasattr(record, 'msg') and record.msg:
                record.msg = self._clean_message(str(record.msg))
            
            # Clean arguments if present
            if hasattr(record, 'args') and record.args:
                cleaned_args = []
                for arg in record.args:
                    if isinstance(arg, (dict, list)):
                        cleaned_args.append(self._clean_data_structure(arg))
                    else:
                        cleaned_args.append(self._clean_message(str(arg)))
                record.args = tuple(cleaned_args)
            
            # Clean extra fields
            for attr_name in dir(record):
                if not attr_name.startswith('_') and attr_name not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName', 'process']:
                    attr_value = getattr(record, attr_name)
                    if isinstance(attr_value, str):
                        setattr(record, attr_name, self._clean_message(attr_value))
                    elif isinstance(attr_value, (dict, list)):
                        setattr(record, attr_name, self._clean_data_structure(attr_value))
            
            return True
            
        except Exception as e:
            # If filtering fails, log the error but don't block the original log
            print(f"PII Filter error: {e}")
            return True
    
    def _clean_message(self, message: str) -> str:
        """
        Clean a text message by removing PII patterns.
        """
        cleaned = message
        
        for pattern, replacement in self.compiled_patterns:
            cleaned = pattern.sub(replacement, cleaned)
        
        return cleaned
    
    def _clean_data_structure(self, data: Any) -> Any:
        """
        Recursively clean data structures (dicts, lists) to remove PII.
        """
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Check if key indicates sensitive data
                if key.lower() in self.sensitive_fields:
                    cleaned[key] = self._mask_sensitive_value(value)
                else:
                    cleaned[key] = self._clean_data_structure(value)
            return cleaned
            
        elif isinstance(data, list):
            return [self._clean_data_structure(item) for item in data]
            
        elif isinstance(data, str):
            return self._clean_message(data)
            
        else:
            return data
    
    def _mask_sensitive_value(self, value: Any) -> str:
        """
        Mask sensitive values while preserving some structure for debugging.
        """
        if value is None:
            return None
            
        str_value = str(value)
        
        # For emails, show domain but mask user part
        if '@' in str_value:
            parts = str_value.split('@')
            if len(parts) == 2:
                return f"[MASKED]@{parts[1]}"
        
        # For other values, show length and type
        return f"[MASKED:{type(value).__name__}:{len(str_value)}]"
    
    def is_sensitive_key(self, key: str) -> bool:
        """
        Check if a key contains sensitive data based on patterns and field names.
        """
        if not key:
            return False
        
        # Check registered sensitive fields
        if key.lower() in self.sensitive_fields:
            return True
        
        # Check for sensitive patterns
        sensitive_patterns = [
            r'patient', r'user', r'auth', r'token', r'session',
            r'medical', r'device', r'sensor', r'calibration',
            r'password', r'email', r'phone', r'clinical'
        ]
        
        return any(
            re.search(pattern, key, re.IGNORECASE) 
            for pattern in sensitive_patterns
        )

class SecureLogger:
    """
    Secure logger wrapper that ensures PII-free logging for medical applications.
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create secure console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Add PII filter
        pii_filter = PIIFilter()
        console_handler.addFilter(pii_filter)
        
        # Create secure formatter
        formatter = SecureFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # Add file handler for production (if configured)
        log_file = os.getenv("SECURE_LOG_FILE")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.addFilter(pii_filter)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with PII filtering."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with PII filtering."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with PII filtering."""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with PII filtering."""
        self.logger.debug(message, extra=kwargs)
    
    def log_sensor_data(self, device_id: str, data_count: int, connection_status: str):
        """
        Log sensor data reception without exposing sensitive information.
        """
        # Hash device ID for privacy while maintaining uniqueness for debugging
        device_hash = hashlib.sha256(device_id.encode()).hexdigest()[:8]
        
        self.info(
            f"Sensor data received from device {device_hash}: "
            f"count={data_count}, status={connection_status}"
        )
    
    def log_user_action(self, action: str, user_id: Optional[str] = None, **context):
        """
        Log user actions with privacy protection.
        """
        # Hash user ID for privacy
        user_hash = None
        if user_id:
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
        
        self.info(
            f"User action: {action}",
            user_hash=user_hash,
            **context
        )
    
    def log_clinical_event(self, event_type: str, patient_id: Optional[str] = None, **details):
        """
        Log clinical events with patient privacy protection.
        """
        # Hash patient ID for privacy
        patient_hash = None
        if patient_id:
            patient_hash = hashlib.sha256(patient_id.encode()).hexdigest()[:8]
        
        # Remove any PII from details
        clean_details = PIIFilter()._clean_data_structure(details)
        
        self.info(
            f"Clinical event: {event_type}",
            patient_hash=patient_hash,
            **clean_details
        )

class SecureFormatter(logging.Formatter):
    """
    Custom formatter that ensures no PII leaks through formatting.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Apply standard formatting
        formatted = super().format(record)
        
        # Additional PII cleaning as final safety net
        pii_filter = PIIFilter()
        return pii_filter._clean_message(formatted)

# Global secure logger instances
security_logger = SecureLogger("vertex.security", logging.INFO)
clinical_logger = SecureLogger("vertex.clinical", logging.INFO)
device_logger = SecureLogger("vertex.device", logging.INFO)
api_logger = SecureLogger("vertex.api", logging.INFO)

def get_secure_logger(name: str) -> SecureLogger:
    """
    Get a secure logger instance for the specified module.
    """
    return SecureLogger(f"vertex.{name}")

def log_security_event(event_type: str, details: Dict[str, Any]):
    """
    Log security-related events with proper PII protection.
    """
    security_logger.info(f"Security event: {event_type}", **details)

def log_api_access(method: str, path: str, status_code: int, user_id: Optional[str] = None):
    """
    Log API access with privacy protection.
    """
    user_hash = None
    if user_id:
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]
    
    api_logger.info(
        f"API access: {method} {path} -> {status_code}",
        user_hash=user_hash
    )

def configure_secure_logging():
    """
    Configure secure logging for the entire application.
    """
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Add PII filter to all existing handlers
    pii_filter = PIIFilter()
    for handler in root_logger.handlers:
        handler.addFilter(pii_filter)
    
    # Configure third-party library loggers
    logging.getLogger("uvicorn").addFilter(pii_filter)
    logging.getLogger("fastapi").addFilter(pii_filter)
    logging.getLogger("supabase").addFilter(pii_filter)
    
    security_logger.info("Secure logging configured successfully")