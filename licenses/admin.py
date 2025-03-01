# File: licenses/admin.py
from django.contrib import admin
from .models import LicenseType, License, LicenseCheck


class LicenseCheckInline(admin.TabularInline):
    model = LicenseCheck
    extra = 0
    readonly_fields = ['timestamp', 'status', 'ip_address', 'hardware_id', 'user_agent', 'message']
    can_delete = False
    max_num = 0
    ordering = ['-timestamp']


@admin.register(LicenseType)
class LicenseTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_days', 'max_instances', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['key_short', 'user', 'license_type', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'license_type', 'created_at']
    search_fields = ['key', 'user__username', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'last_checked']
    inlines = [LicenseCheckInline]
    
    actions = ['activate_licenses', 'deactivate_licenses', 'revoke_licenses']
    
    def key_short(self, obj):
        """Display a shortened version of the key in the admin list"""
        return f"{obj.key[:10]}..."
    
    key_short.short_description = 'License Key'
    
    def activate_licenses(self, request, queryset):
        """Admin action to activate selected licenses"""
        activated = 0
        for license in queryset:
            if license.status != 'active' and license.status != 'revoked':
                license.activate()
                activated += 1
        
        self.message_user(request, f"{activated} licenses activated successfully")
    
    activate_licenses.short_description = "Activate selected licenses"
    
    def deactivate_licenses(self, request, queryset):
        """Admin action to deactivate selected licenses"""
        deactivated = 0
        for license in queryset:
            if license.status == 'active':
                license.deactivate()
                deactivated += 1
        
        self.message_user(request, f"{deactivated} licenses deactivated successfully")
    
    deactivate_licenses.short_description = "Deactivate selected licenses"
    
    def revoke_licenses(self, request, queryset):
        """Admin action to revoke selected licenses"""
        revoked = 0
        for license in queryset:
            if license.status != 'revoked':
                license.revoke()
                revoked += 1
        
        self.message_user(request, f"{revoked} licenses revoked successfully")
    
    revoke_licenses.short_description = "Revoke selected licenses (permanent)"


@admin.register(LicenseCheck)
class LicenseCheckAdmin(admin.ModelAdmin):
    list_display = ['license_key', 'status', 'timestamp', 'ip_address', 'hardware_id']
    list_filter = ['status', 'timestamp']
    search_fields = ['license__key', 'ip_address', 'hardware_id', 'message']
    readonly_fields = ['license', 'timestamp', 'status', 'ip_address', 'hardware_id', 'user_agent', 'message']
    
    def license_key(self, obj):
        """Display the license key for this check"""
        return f"{obj.license.key[:10]}..."
    
    license_key.short_description = 'License Key'