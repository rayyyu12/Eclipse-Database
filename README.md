# License Manager

A Django-based license key management system for software applications. This system provides a database and CLI interface to create, manage, and validate license keys for your software products.

## Overview

The License Manager is a standalone Django application designed to handle all aspects of software licensing:

- Generate cryptographically secure license keys
- Manage different license types and tiers
- Activate licenses with hardware binding
- Track license usage and validation history
- Validate licenses through CLI or API
- Revoke or deactivate licenses as needed

This system can be used as a centralized license server for your software products or integrated directly into your applications.

## Core Features

### License Generation & Management

- **Unique License Keys**: Generate cryptographically secure license keys with optional prefixes
- **Multiple License Types**: Define different license tiers with varying durations and capabilities
- **User Assignment**: Associate licenses with specific users for tracking
- **Expiration Management**: Set and enforce license expiration dates
- **Hardware Binding**: Limit license usage to specific devices
- **Activity Logging**: Track all license activities for audit purposes

### Validation & Security

- **License Validation**: Check license validity with hardware verification
- **Activation/Deactivation**: Enable activation workflows for license management
- **Revocation**: Permanently revoke licenses when needed
- **Comprehensive Logging**: Track all license checks and attempts

### User Interface

- **Command Line Interface**: Manage all license operations via CLI
- **Django Admin Interface**: Web-based administration
- **Readable Output**: Rich console output with colorized tables and text

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- virtualenv (recommended)

### Setup Steps

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/license-manager.git
cd license-manager
```

2. **Create a Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure the Environment**

For production environments, edit `license_manager/settings.py` and update:
- `SECRET_KEY` (generate a new one)
- `LICENSE_SECRET` (for license key generation)
- `DEBUG = False`
- Configure a production database if needed

5. **Initialize the Database**

```bash
python manage.py makemigrations licenses
python manage.py migrate
```

6. **Create an Admin User**

```bash
python manage.py createsuperuser
```

7. **Create License Types**

```bash
python manage.py shell
```

```python
from licenses.models import LicenseType

# Create different license tiers
LicenseType.objects.create(
    name="Standard",
    description="Standard license with 1 year validity",
    max_instances=1,
    duration_days=365
)

LicenseType.objects.create(
    name="Professional",
    description="Professional license with extended features",
    max_instances=3,
    duration_days=365
)

LicenseType.objects.create(
    name="Enterprise",
    description="Enterprise license with multi-user support",
    max_instances=10,
    duration_days=730
)

# Exit the shell
exit()
```

8. **Start the Development Server** (optional for web admin)

```bash
python manage.py runserver
```

## Usage Guide

### License Management Commands

#### Generate License Keys

Generate a new license key for a specific license type:

```bash
# Basic usage (where 1 is the license type ID)
python manage.py generate_key 1

# Generate with user assignment
python manage.py generate_key 1 --user johndoe

# Generate with custom prefix and notes
python manage.py generate_key 1 --prefix ACME --notes "Customer: Acme Corp"

# Generate multiple licenses
python manage.py generate_key 1 --count 5 --prefix BULK

# Generate with custom activation limit
python manage.py generate_key 1 --activations 3
```

#### Check License Status

Validate and display information about a license:

```bash
# Basic check
python manage.py check_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX

# Check with hardware validation
python manage.py check_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX --hardware-id "your-hardware-id"

# Show activity history
python manage.py check_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX --activity
```

#### List Licenses

Display and filter license keys:

```bash
# List all licenses (limited to 50 by default)
python manage.py list_keys

# Filter by status
python manage.py list_keys --status active

# Filter by license type
python manage.py list_keys --type "Professional"

# Find licenses expiring soon
python manage.py list_keys --expiring 30

# Search by key or notes
python manage.py list_keys --search "ACME"

# Combine filters
python manage.py list_keys --status active --type "Enterprise" --limit 100
```

#### Activate a License

Activate a pending license:

```bash
# Simple activation
python manage.py activate_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX

# Activate with hardware binding
python manage.py activate_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX --hardware-id "your-hardware-id"
```

#### Revoke a License

Permanently revoke a license:

```bash
# Revoke with confirmation prompt
python manage.py revoke_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX

# Revoke with reason
python manage.py revoke_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX --reason "Terms violation"

# Force revoke without confirmation
python manage.py revoke_key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX --force
```

### Django Admin Interface

Access the admin interface by running the server and navigating to `/admin/`:

```bash
python manage.py runserver
```

Then visit http://127.0.0.1:8000/admin/ and log in with your superuser credentials.

The admin interface provides a user-friendly way to:
- Create and manage license types
- Generate and modify license keys
- View license usage history
- Search and filter licenses
- Perform bulk operations

## Integration Guide

### Integrating with Your Application

To incorporate license validation in your applications, you can:

#### Option 1: Direct Database Integration

If your application is also Django-based, you can include this app as a dependency:

```python
# In your project's settings.py
INSTALLED_APPS = [
    # ... other apps
    'licenses',
]
```

Then use the LicenseService in your code:

```python
from licenses.services import LicenseService
from licenses.utils import generate_hardware_id

# Get current hardware ID
hardware_id = generate_hardware_id()

# Validate a license
result = LicenseService.validate_license('XXXXX-XXXXX-XXXXX-XXXXX-XXXXX', hardware_id)

if result['valid']:
    # License is valid - enable features
    print(f"License valid until {result['expires_at']}")
else:
    # License is invalid - restrict features
    print(f"License invalid: {result['message']}")
```

#### Option 2: REST API Integration

For non-Django applications, you could set up a REST API (not included by default, but easy to add):

1. Add a REST API view
2. Call the API endpoint from your application

Example API client code (Python):

```python
import requests
import hashlib
import platform

def generate_hardware_id():
    """Generate a hardware ID based on system information"""
    system_info = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'machine': platform.machine(),
        'processor': platform.processor(),
    }
    
    hw_id_string = '-'.join(f"{k}:{v}" for k, v in system_info.items())
    return hashlib.sha256(hw_id_string.encode()).hexdigest()

def validate_license(license_key, api_url):
    hardware_id = generate_hardware_id()
    
    response = requests.post(
        f"{api_url}/validate/", 
        json={
            'license_key': license_key,
            'hardware_id': hardware_id
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return {'valid': False, 'message': 'Error connecting to license server'}
```

#### Option 3: Offline Validation

For applications that need to work offline, you can implement a JWT-based validation approach:

1. Generate signed license tokens that contain expiration and feature information
2. Validate the token signatures locally in your application

## Security Considerations

1. **Environment Security**:
   - Use HTTPS for all API communications
   - Store `LICENSE_SECRET` in environment variables, not in source code
   - Use a production database with proper credentials

2. **License Key Protection**:
   - Use hardware binding to prevent license sharing
   - Implement periodic online validation when possible
   - Consider obfuscation techniques for offline validation code

3. **Server Hardening**:
   - Limit access to your license server
   - Implement rate limiting to prevent brute force attacks
   - Set up proper firewall rules and secure the server

## Deployment Options

### Standard Django Deployment

For production, deploy using a standard Django setup:
- WSGI server (Gunicorn, uWSGI)
- Web server (Nginx, Apache)
- Database (PostgreSQL recommended)
- HTTPS with Let's Encrypt

Example Gunicorn configuration:

```bash
gunicorn license_manager.wsgi:application --bind 0.0.0.0:8000
```

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name license.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/license-manager;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### Docker Deployment

For containerized deployment, create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "license_manager.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Build and run the Docker container:

```bash
docker build -t license-manager .
docker run -p 8000:8000 -e LICENSE_SECRET=your_secure_secret license-manager
```

## Customization

### Adding New License Features

To add new license features, modify the `LicenseType` model:

1. Edit `licenses/models.py` to add new fields
2. Create and apply migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Changing License Key Format

To modify the license key format, edit the `generate_license_key` function in `licenses/utils.py`.

### Adding API Endpoints

To add REST API capabilities:

1. Create serializers in `licenses/serializers.py`
2. Create views in `licenses/views.py`
3. Define URL patterns in `licenses/urls.py`
4. Update the project URLs in `license_manager/urls.py`

## Troubleshooting

### Common Issues

**Migration errors**:
```bash
# Reset migrations if needed
rm -rf licenses/migrations
python manage.py makemigrations licenses
python manage.py migrate
```

**Permission issues**:
```bash
# Fix file permissions
chmod +x manage.py
```

**Database connection errors**:
- Check database credentials in settings.py
- Ensure the database server is running
- Verify network connectivity to the database

## Contributing

Contributions are welcome! Here's how to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure everything works
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

For development work:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
python manage.py test

# Check code style
flake8 .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django framework
- Rich library for CLI output
- PyJWT for license validation

---

## Contact & Support

For questions, issues, or support:
- Open an issue on GitHub
- Contact: your-email@example.com

Made with ❤️ by Your Name/Organization
