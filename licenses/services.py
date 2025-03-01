# File: licenses/services.py
from django.utils import timezone
from datetime import timedelta
from .models import License, LicenseType, LicenseCheck
from .utils import generate_license_key, validate_license_key_format
from django.db.models import Q


class LicenseService:
    """Service class for license-related operations"""
    
    @staticmethod
    def create_license(license_type_id, user=None, prefix=None, max_activations=1, notes=None):
        """Create a new license key"""
        try:
            license_type = LicenseType.objects.get(id=license_type_id)
            
            # Generate a unique license key
            key = generate_license_key(
                prefix=prefix, 
                user_id=user.id if user else None,
                license_type_id=license_type_id
            )
            
            # Create the license
            license = License.objects.create(
                key=key,
                user=user,
                license_type=license_type,
                max_activations=max_activations,
                notes=notes
            )
            
            return license
        except LicenseType.DoesNotExist:
            raise ValueError(f"License type with ID {license_type_id} does not exist")
        except Exception as e:
            raise Exception(f"Failed to create license: {str(e)}")
    
    @staticmethod
    def validate_license(key, hardware_id=None):
        """Validate a license key and return validation status"""
        if not validate_license_key_format(key):
            return {
                'valid': False,
                'message': 'Invalid license key format'
            }
            
        try:
            license = License.objects.get(key=key)
            
            # Record the check attempt
            check_result = license.validate_license(hardware_id=hardware_id)
            
            if not check_result:
                return {
                    'valid': False,
                    'message': f'License check failed: {license.status}',
                    'status': license.status
                }
                
            return {
                'valid': True,
                'message': 'License is valid',
                'license_type': license.license_type.name,
                'expires_at': license.expires_at,
                'status': license.status
            }
        except License.DoesNotExist:
            return {
                'valid': False,
                'message': 'License key does not exist'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error validating license: {str(e)}'
            }
    
    @staticmethod
    def activate_license(key, hardware_id=None):
        """Activate a license"""
        try:
            license = License.objects.get(key=key)
            
            if license.status == 'active':
                return {
                    'success': False,
                    'message': 'License is already active'
                }
                
            if license.status == 'revoked':
                return {
                    'success': False,
                    'message': 'License has been revoked and cannot be activated'
                }
                
            if license.status == 'expired':
                return {
                    'success': False,
                    'message': 'License has expired and cannot be activated'
                }
            
            activation_result = license.activate(hardware_id)
            
            if not activation_result:
                return {
                    'success': False,
                    'message': 'Failed to activate license'
                }
                
            return {
                'success': True,
                'message': 'License activated successfully',
                'license_data': {
                    'key': license.key,
                    'status': license.status,
                    'expires_at': license.expires_at,
                    'license_type': license.license_type.name
                }
            }
        except License.DoesNotExist:
            return {
                'success': False,
                'message': 'License key does not exist'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error activating license: {str(e)}'
            }
    
    @staticmethod
    def deactivate_license(key):
        """Deactivate a license"""
        try:
            license = License.objects.get(key=key)
            
            if license.status != 'active':
                return {
                    'success': False,
                    'message': f'License is not active (current status: {license.status})'
                }
                
            deactivation_result = license.deactivate()
            
            if not deactivation_result:
                return {
                    'success': False,
                    'message': 'Failed to deactivate license'
                }
                
            return {
                'success': True,
                'message': 'License deactivated successfully'
            }
        except License.DoesNotExist:
            return {
                'success': False,
                'message': 'License key does not exist'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deactivating license: {str(e)}'
            }
    
    @staticmethod
    def revoke_license(key, reason=None):
        """Revoke a license permanently"""
        try:
            license = License.objects.get(key=key)
            
            if license.status == 'revoked':
                return {
                    'success': False,
                    'message': 'License is already revoked'
                }
            
            license.revoke()
            
            if reason:
                license.notes = f"{license.notes or ''}\nRevoked: {reason}"
                license.save()
                
            return {
                'success': True,
                'message': 'License revoked successfully'
            }
        except License.DoesNotExist:
            return {
                'success': False,
                'message': 'License key does not exist'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error revoking license: {str(e)}'
            }
    
    @staticmethod
    def get_license_info(key):
        """Get detailed information about a license"""
        try:
            license = License.objects.get(key=key)
            
            return {
                'success': True,
                'license_data': {
                    'key': license.key,
                    'status': license.status,
                    'created_at': license.created_at,
                    'activation_date': license.activation_date,
                    'expires_at': license.expires_at,
                    'last_checked': license.last_checked,
                    'license_type': license.license_type.name,
                    'max_activations': license.max_activations,
                    'user': license.user.username if license.user else None,
                    'hardware_id': license.hardware_id,
                    'notes': license.notes
                }
            }
        except License.DoesNotExist:
            return {
                'success': False,
                'message': 'License key does not exist'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving license info: {str(e)}'
            }
    
    @staticmethod
    def search_licenses(query=None, status=None, license_type=None, active_only=False, order_by='-created_at'):
        """Search and filter licenses"""
        filters = Q()
        
        if query:
            filters |= Q(key__icontains=query) | Q(notes__icontains=query)
            
            # If the query could be a username
            filters |= Q(user__username__icontains=query)
            
        if status:
            filters &= Q(status=status)
            
        if license_type:
            filters &= Q(license_type__name=license_type)
            
        if active_only:
            filters &= Q(status='active')
            
        try:
            licenses = License.objects.filter(filters).order_by(order_by)
            return licenses
        except Exception as e:
            raise Exception(f"Error searching licenses: {str(e)}")