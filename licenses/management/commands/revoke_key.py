# File: licenses/management/commands/revoke_key.py
from django.core.management.base import BaseCommand, CommandError
from rich.console import Console
from rich.prompt import Confirm
from licenses.services import LicenseService


class Command(BaseCommand):
    help = 'Revoke a license key'

    def add_arguments(self, parser):
        parser.add_argument(
            'key',
            help='The license key to revoke'
        )
        
        parser.add_argument(
            '--reason',
            help='Reason for revoking the license'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        console = Console()
        
        try:
            key = options['key']
            reason = options.get('reason')
            force = options.get('force', False)
            
            # Get license info first
            info = LicenseService.get_license_info(key)
            
            if not info['success']:
                console.print(f"[bold red]Error:[/bold red] {info['message']}")
                return
                
            license_data = info['license_data']
            
            # Show license info
            console.print(f"License: [bold cyan]{key}[/bold cyan]")
            console.print(f"Status: {license_data['status']}")
            console.print(f"Type: {license_data['license_type']}")
            console.print(f"User: {license_data['user'] or 'Not assigned'}")
            
            # Skip confirmation if forced
            if not force:
                confirmed = Confirm.ask("\nAre you sure you want to revoke this license? This action cannot be undone.")
                if not confirmed:
                    console.print("[yellow]Operation cancelled.[/yellow]")
                    return
            
            # Revoke the license
            result = LicenseService.revoke_license(key, reason)
            
            if result['success']:
                console.print(f"[bold green]Success![/bold green] {result['message']}")
            else:
                console.print(f"[bold red]Error:[/bold red] {result['message']}")
                
        except Exception as e:
            raise CommandError(f"Error revoking license: {str(e)}")