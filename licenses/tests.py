import os
import uuid
import hashlib
import hmac
import random
import string
import base64
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
import jwt


def generate_license_key(prefix=None, secret=None, user_id=None, license_type_id=None):
    """
    Generate a unique license key with the following format:
    XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    
    The license key contains a verification mechanism via JWT.
    """
    if not secret:
        secret = settings.LICENSE_SECRET
    
    # Generate a random string as the base for the license key
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    
    # Create a payload for encoding
    current_time = datetime.utcnow()
    payload = {
        'jti': str(uuid.uuid4()),  # JWT ID
        'iat': current_time,
        'user_id': user_id,
        'license_type': license_type_id,
        'random': random_part,
    }
    
    # Create the JWT token
    jwt_token = jwt.encode(payload, secret, algorithm='HS256')
    
    # Convert the JWT to a shorter string
    raw_key_bytes = hashlib.sha256(jwt_token.encode('utf-8')).digest()
    key_b64 = base64.b32encode(raw_key_bytes).decode('utf-8')
    
    # Format the key with prefix and separators
    key = key_b64[:25].upper()  # Use only first 25 chars to keep it manageable
    if prefix:
        key = f"{prefix}-{key}"
    
    # Format with dashes every 5 characters
    formatted_key = '-'.join([key[i:i+5] for i in range(0, len(key), 5)])
    return formatted_key


def validate_license_key_format(key):
    """Validate the format of a license key"""
    # Remove any dashes
    key_clean = key.replace('-', '').upper()
    
    # Check for valid base32 characters (excluding padding)
    valid_chars = set(string.ascii_uppercase + string.digits)
    return all(c in valid_chars for c in key_clean) and 20 <= len(key_clean) <= 30


def generate_hardware_id():
    """
    Generate a pseudo hardware ID for testing purposes.
    In a real application, you would collect system-specific hardware information.
    """
    # This is a simplified example - in a real app, collect actual hardware info
    import platform
    system_info = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'machine': platform.machine(),
        'processor': platform.processor()
    }
    
    # Create a hash of the system info
    hw_id_string = '-'.join(f"{k}:{v}" for k, v in system_info.items())
    return hashlib.sha256(hw_id_string.encode()).hexdigest()


def verify_hardware_id(stored_id, current_id):
    """
    Verify that the hardware ID matches the one stored in the license.
    In a real app, you might want to allow for some differences.
    """
    return stored_id == current_id