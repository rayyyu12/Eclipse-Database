# File: licenses/management/commands/check_key.py
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from licenses.models import License, LicenseCheck
from licenses.services import LicenseService
from licenses.utils import generate_hardware_id


class Command(BaseCommand):
    help = 'Check license key status and validity'

    def add_arguments(self, parser):
        parser.add_argument(
            'key',
            help='The license key to check'
        )
        
        parser.add_argument(
            '--hardware-id',
            help='Hardware ID for validation (defaults to current system)'
        )
        
        parser.add_argument(
            '--activity',
            action='store_true',
            help='Show license activity history'
        )

    def handle(self, *args, **options):
        console = Console()
        
        try:
            key = options['key']
            hardware_id = options.get('hardware_id')
            show_activity = options.get('activity', False)
            
            # If no hardware ID provided, generate one from current system
            if not hardware_id:
                hardware_id = generate_hardware_id()
                console.print(f"[dim]Using hardware ID: {hardware_id[:8]}...[/dim]")
            
            # Validate the license
            result = LicenseService.validate_license(key, hardware_id)
            
            if result['valid']:
                console.print(Panel(
                    f"License key [bold cyan]{key}[/bold cyan] is [bold green]VALID[/bold green]",
                    expand=False
                ))
                
                # Get detailed info
                info = LicenseService.get_license_info(key)
                
                if info['success']:
                    license_data = info['license_data']
                    
                    table = Table(title="License Details")
                    table.add_column("Attribute", style="cyan")
                    table.add_column("Value")
                    
                    table.add_row("Key", license_data['key'])
                    table.add_row("Status", f"[green]{license_data['status']}[/green]" if license_data['status'] == 'active' else license_data['status'])
                    table.add_row("Type", license_data['license_type'])
                    table.add_row("Created", str(license_data['created_at']))
                    table.add_row("Activated", str(license_data['activation_date']) if license_data['activation_date'] else "Not activated")
                    table.add_row("Expires", str(license_data['expires_at']) if license_data['expires_at'] else "No expiration")
                    table.add_row("Last Checked", str(license_data['last_checked']) if license_data['last_checked'] else "Never")
                    table.add_row("User", license_data['user'] if license_data['user'] else "Not assigned")
                    
                    console.print(table)
                    
                    # Show activity if requested
                    if show_activity:
                        try:
                            license_obj = License.objects.get(key=key)
                            checks = LicenseCheck.objects.filter(license=license_obj).order_by('-timestamp')[:20]
                            
                            activity_table = Table(title="License Activity (Last 20 Events)")
                            activity_table.add_column("Timestamp", style="dim")
                            activity_table.add_column("Status")
                            activity_table.add_column("Message")
                            activity_table.add_column("Hardware ID", style="dim")
                            
                            for check in checks:
                                status_style = "green" if check.status.startswith("check_success") or check.status == "activated" else "red"
                                activity_table.add_row(
                                    check.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                    f"[{status_style}]{check.status}[/{status_style}]",
                                    check.message or "",
                                    check.hardware_id[:8] + "..." if check.hardware_id else ""
                                )
                                
                            console.print(activity_table)
                        except Exception as e:
                            console.print(f"[bold yellow]Warning:[/bold yellow] Could not retrieve activity: {str(e)}")
            else:
                console.print(Panel(
                    f"License key [bold]{key}[/bold] is [bold red]INVALID[/bold red]\n\n{result['message']}",
                    title="Validation Failed",
                    expand=False
                ))
                
        except Exception as e:
            raise CommandError(f"Error checking license: {str(e)}")