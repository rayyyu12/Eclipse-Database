# File: licenses/management/commands/generate_key.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from rich.console import Console
from rich.table import Table
from licenses.models import LicenseType, License
from licenses.services import LicenseService


class Command(BaseCommand):
    help = 'Generate a new license key'

    def add_arguments(self, parser):
        parser.add_argument(
            'license_type_id',
            type=int,
            help='The ID of the license type'
        )
        
        parser.add_argument(
            '--user',
            dest='username',
            help='Username to assign the license to'
        )
        
        parser.add_argument(
            '--prefix',
            help='Prefix for the license key'
        )
        
        parser.add_argument(
            '--activations',
            type=int,
            default=1,
            help='Maximum number of activations allowed'
        )
        
        parser.add_argument(
            '--notes',
            help='Notes for the license'
        )
        
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of licenses to generate'
        )

    def handle(self, *args, **options):
        console = Console()
        
        try:
            license_type_id = options['license_type_id']
            username = options.get('username')
            prefix = options.get('prefix')
            max_activations = options.get('activations', 1)
            notes = options.get('notes')
            count = options.get('count', 1)
            
            # Check if license type exists
            try:
                license_type = LicenseType.objects.get(id=license_type_id)
            except LicenseType.DoesNotExist:
                available_types = LicenseType.objects.all()
                if available_types:
                    console.print("[bold red]Error:[/bold red] License type not found.")
                    table = Table(title="Available License Types")
                    table.add_column("ID", style="dim")
                    table.add_column("Name")
                    table.add_column("Duration (days)")
                    table.add_column("Max Instances")
                    
                    for lt in available_types:
                        table.add_row(
                            str(lt.id),
                            lt.name,
                            str(lt.duration_days),
                            str(lt.max_instances)
                        )
                    
                    console.print(table)
                else:
                    console.print("[bold red]Error:[/bold red] No license types found. Create one first.")
                return
            
            # Find user if provided
            user = None
            if username:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    console.print(f"[bold yellow]Warning:[/bold yellow] User '{username}' not found. License will be created without a user.")
            
            # Generate the licenses
            licenses = []
            for i in range(count):
                license = LicenseService.create_license(
                    license_type_id=license_type_id,
                    user=user,
                    prefix=prefix,
                    max_activations=max_activations,
                    notes=notes
                )
                licenses.append(license)
            
            # Display results
            if count == 1:
                console.print(f"[bold green]Success![/bold green] License generated.")
                
                # Display license details
                table = Table(title="License Details")
                table.add_column("Field", style="cyan")
                table.add_column("Value")
                
                table.add_row("License Key", licenses[0].key)
                table.add_row("License Type", license_type.name)
                table.add_row("Status", licenses[0].status)
                table.add_row("User", username if username else "None")
                table.add_row("Created", licenses[0].created_at.strftime('%Y-%m-%d %H:%M:%S'))
                table.add_row("Expires", licenses[0].expires_at.strftime('%Y-%m-%d %H:%M:%S') if licenses[0].expires_at else "Not set")
                
                console.print(table)
            else:
                console.print(f"[bold green]Success![/bold green] {count} licenses generated.")
                
                # Display all licenses
                table = Table(title=f"{count} Licenses Generated")
                table.add_column("License Key", style="cyan")
                table.add_column("Status")
                table.add_column("Created")
                table.add_column("Expires")
                
                for license in licenses:
                    table.add_row(
                        license.key,
                        license.status,
                        license.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        license.expires_at.strftime('%Y-%m-%d %H:%M:%S') if license.expires_at else "Not set"
                    )
                
                console.print(table)
                
        except Exception as e:
            raise CommandError(f"Failed to generate license: {str(e)}")