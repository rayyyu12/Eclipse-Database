# File: licenses/management/commands/activate_key.py
from django.core.management.base import BaseCommand, CommandError
from rich.console import Console
from licenses.services import LicenseService
from licenses.utils import generate_hardware_id


class Command(BaseCommand):
    help = 'Activate a license key'

    def add_arguments(self, parser):
        parser.add_argument(
            'key',
            help='The license key to activate'
        )
        
        parser.add_argument(
            '--hardware-id',
            help='Hardware ID to associate with this license (defaults to current system)'
        )

    def handle(self, *args, **options):
        console = Console()
        
        try:
            key = options['key']
            hardware_id = options.get('hardware_id')
            
            # If no hardware ID provided, generate one from current system
            if not hardware_id:
                hardware_id = generate_hardware_id()
                console.print(f"[dim]Using hardware ID: {hardware_id[:8]}...[/dim]")
            
            # Activate the license
            result = LicenseService.activate_license(key, hardware_id)
            
            if result['success']:
                license_data = result['license_data']
                
                console.print(f"[bold green]Success![/bold green] {result['message']}")
                console.print(f"License: [bold cyan]{license_data['key']}[/bold cyan]")
                console.print(f"Status: [green]{license_data['status']}[/green]")
                console.print(f"Type: {license_data['license_type']}")
                console.print(f"Expires: {license_data['expires_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                console.print(f"[bold red]Error:[/bold red] {result['message']}")
                
        except Exception as e:
            raise CommandError(f"Error activating license: {str(e)}")