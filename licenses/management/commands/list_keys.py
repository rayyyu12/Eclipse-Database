# File: licenses/management/commands/list_keys.py
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from rich.console import Console
from rich.table import Table
from licenses.models import License, LicenseType


class Command(BaseCommand):
    help = 'List all license keys with filtering options'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            choices=['active', 'expired', 'revoked', 'pending'],
            help='Filter by license status'
        )
        
        parser.add_argument(
            '--type',
            dest='license_type',
            help='Filter by license type name'
        )
        
        parser.add_argument(
            '--user',
            help='Filter by username'
        )
        
        parser.add_argument(
            '--expiring',
            type=int,
            help='Show licenses expiring in the next N days'
        )
        
        parser.add_argument(
            '--search',
            help='Search by license key or notes'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of results (default: 50)'
        )

    def handle(self, *args, **options):
        console = Console()
        
        try:
            status = options.get('status')
            license_type = options.get('license_type')
            username = options.get('user')
            expiring_days = options.get('expiring')
            search = options.get('search')
            limit = options.get('limit', 50)
            
            # Build query filters
            filters = Q()
            
            if status:
                filters &= Q(status=status)
                
            if license_type:
                filters &= Q(license_type__name__icontains=license_type)
                
            if username:
                filters &= Q(user__username__icontains=username)
                
            if expiring_days:
                expiry_cutoff = timezone.now() + timedelta(days=expiring_days)
                filters &= Q(expires_at__lte=expiry_cutoff, expires_at__gt=timezone.now())
                
            if search:
                filters &= Q(key__icontains=search) | Q(notes__icontains=search)
            
            # Get licenses
            licenses = License.objects.filter(filters).select_related('license_type', 'user').order_by('-created_at')[:limit]
            
            # Count total matches
            total_count = License.objects.filter(filters).count()
            
            # Display results
            table = Table(show_header=True)
            table.add_column("License Key", style="cyan")
            table.add_column("Status")
            table.add_column("Type")
            table.add_column("User")
            table.add_column("Created", style="dim")
            table.add_column("Expires")
            
            for license in licenses:
                # Format status with color
                status_str = license.status
                if license.status == 'active':
                    status_str = f"[green]{license.status}[/green]"
                elif license.status == 'expired':
                    status_str = f"[yellow]{license.status}[/yellow]"
                elif license.status == 'revoked':
                    status_str = f"[red]{license.status}[/red]"
                
                # Add row
                table.add_row(
                    license.key,
                    status_str,
                    license.license_type.name,
                    license.user.username if license.user else "-",
                    license.created_at.strftime('%Y-%m-%d') if license.created_at else "-",
                    license.expires_at.strftime('%Y-%m-%d') if license.expires_at else "-"
                )
                
            # Show results
            console.print(f"\nFound {total_count} licenses" + (f" (showing {len(licenses)})" if total_count > limit else ""))
            
            if licenses:
                console.print(table)
            else:
                console.print("[yellow]No licenses found matching the criteria.[/yellow]")
                
            # Show filters applied
            filters_applied = []
            if status:
                filters_applied.append(f"status={status}")
            if license_type:
                filters_applied.append(f"type={license_type}")
            if username:
                filters_applied.append(f"user={username}")
            if expiring_days:
                filters_applied.append(f"expiring in {expiring_days} days")
            if search:
                filters_applied.append(f"search='{search}'")
                
            if filters_applied:
                console.print("[dim]Filters: " + ", ".join(filters_applied) + "[/dim]")
                
        except Exception as e:
            raise CommandError(f"Error listing licenses: {str(e)}")