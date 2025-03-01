# File: licenses/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class LicenseType(models.Model):
    """License type model defining different product tiers"""
    name = models.CharField(max_length=50)
    description = models.TextField()
    max_instances = models.IntegerField(default=1)
    duration_days = models.IntegerField(default=365)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class License(models.Model):
    """License model to store license key information"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
        ('pending', 'Pending Activation'),
    )

    key = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    license_type = models.ForeignKey(LicenseType, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    activation_date = models.DateTimeField(null=True, blank=True)
    hardware_id = models.CharField(max_length=255, null=True, blank=True)
    max_activations = models.IntegerField(default=1)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.key[:8]}... ({self.status})"

    def save(self, *args, **kwargs):
        # Set expiration date based on license type if not set manually
        if not self.expires_at and self.license_type:
            if self.activation_date:
                self.expires_at = self.activation_date + timezone.timedelta(days=self.license_type.duration_days)
            else:
                self.expires_at = timezone.now() + timezone.timedelta(days=self.license_type.duration_days)
        
        # Check if expired
        if self.expires_at and self.expires_at < timezone.now() and self.status != 'revoked':
            self.status = 'expired'
        
        super().save(*args, **kwargs)

    def activate(self, hardware_id=None):
        """Activate the license"""
        if self.status != 'revoked':
            self.status = 'active'
            self.activation_date = timezone.now()
            self.expires_at = self.activation_date + timezone.timedelta(days=self.license_type.duration_days)
            
            if hardware_id:
                self.hardware_id = hardware_id
                
            self.save()
            LicenseCheck.objects.create(
                license=self,
                status='activated',
                hardware_id=hardware_id
            )
            return True
        return False

    def deactivate(self):
        """Deactivate the license"""
        if self.status == 'active':
            self.status = 'pending'
            self.save()
            LicenseCheck.objects.create(
                license=self,
                status='deactivated'
            )
            return True
        return False

    def revoke(self):
        """Revoke the license permanently"""
        self.status = 'revoked'
        self.save()
        LicenseCheck.objects.create(
            license=self,
            status='revoked'
        )
        return True

    def validate_license(self, hardware_id=None):
        """Check license validity and record the check"""
        self.last_checked = timezone.now()
        
        if self.expires_at and self.expires_at < timezone.now():
            self.status = 'expired'
            self.save()
            
            LicenseCheck.objects.create(
                license=self, 
                status='check_failed',
                message='License expired',
                hardware_id=hardware_id
            )
            return False
            
        if self.status != 'active':
            LicenseCheck.objects.create(
                license=self, 
                status='check_failed',
                message=f'License not active, status: {self.status}',
                hardware_id=hardware_id
            )
            return False
            
        # Verify hardware ID if needed
        if hardware_id and self.hardware_id and hardware_id != self.hardware_id:
            LicenseCheck.objects.create(
                license=self, 
                status='check_failed',
                message='Hardware ID mismatch',
                hardware_id=hardware_id
            )
            return False
            
        self.save()
        
        LicenseCheck.objects.create(
            license=self,
            status='check_success',
            hardware_id=hardware_id
        )
        return True


class LicenseCheck(models.Model):
    """Model to log license check and validation attempts"""
    LICENSE_CHECK_STATUSES = (
        ('check_success', 'Check Successful'),
        ('check_failed', 'Check Failed'),
        ('activated', 'License Activated'),
        ('deactivated', 'License Deactivated'),
        ('revoked', 'License Revoked'),
    )
    
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name='checks')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=LICENSE_CHECK_STATUSES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    hardware_id = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.license.key[:8]}... - {self.status} at {self.timestamp}"