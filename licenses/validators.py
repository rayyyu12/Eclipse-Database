# File: licenses/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re
from .utils import validate_license_key_format


def validate_license_key(value):
    """
    Validate that a license key is properly formatted.
    Format should be: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    """
    if not validate_license_key_format(value):
        raise ValidationError(
            _('%(value)s is not a valid license key. Format should be XXXXX-XXXXX-XXXXX-XXXXX-XXXXX'),
            params={'value': value},
        )


def validate_hardware_id(value):
    """
    Validate that a hardware ID looks like a SHA-256 hash.
    """
    if not value:  # Accept empty hardware IDs
        return
        
    # Check if it looks like a SHA-256 hash (64 hex characters)
    if not re.match(r'^[0-9a-f]{64}$', value.lower()):
        raise ValidationError(
            _('%(value)s is not a valid hardware ID. Expected a 64-character hexadecimal string.'),
            params={'value': value},
        )


def validate_expiry_date(value):
    """
    Validate that an expiry date is in the future.
    """
    from django.utils import timezone
    
    if value and value <= timezone.now():
        raise ValidationError(
            _('Expiry date must be in the future.'),
        )


def validate_license_type(value):
    """
    Validate that a license type is active.
    """
    from .models import LicenseType
    
    if isinstance(value, LicenseType) and not value.is_active:
        raise ValidationError(
            _('The selected license type is not active.'),
        )


def validate_max_activations(value):
    """
    Validate that max_activations is a positive integer.
    """
    if value <= 0:
        raise ValidationError(
            _('Maximum activations must be greater than zero.'),
        )


def validate_license_prefix(value):
    """
    Validate that a license prefix only contains letters and numbers.
    """
    if value and not re.match(r'^[A-Z0-9]+$', value):
        raise ValidationError(
            _('License prefix must contain only uppercase letters and numbers.'),
        )


# For integration with Django forms or serializers, you can create validator classes

class LicenseKeyValidator:
    """
    Validator for license keys that can be used with Django forms or serializers.
    """
    def __call__(self, value):
        validate_license_key(value)


class HardwareIDValidator:
    """
    Validator for hardware IDs that can be used with Django forms or serializers.
    """
    def __call__(self, value):
        validate_hardware_id(value)