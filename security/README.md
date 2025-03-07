# Security Module

The security module is a modular framework for API key verification, credential management, and threat intelligence in Python applications.

## Architecture

The security module has been refactored from a monolithic structure into a more modular architecture:

```
security/
├── __init__.py             # Main interface
├── README.md               # This file
└── modules/                # Specialized modules
    ├── __init__.py         # Package marker
    ├── credentials.py      # Credential management
    ├── intel.py            # Intelligence data management
    ├── middleware.py       # Web security middleware
    ├── taxii.py            # STIX/TAXII integration
    ├── threat.py           # Threat monitoring and analysis
    └── utils.py            # Common utilities
```

## Features

- **Credential Management**: Secure storage, verification, and rotation of API keys and other credentials
- **Threat Intelligence**: Collection, storage, and analysis of security intelligence
- **STIX/TAXII Integration**: Integration with standard threat intelligence platforms
- **Web Security Middleware**: Security middleware for Flask applications
- **Threat Detection**: Rule-based threat detection and monitoring

## Usage

### Basic Initialization

```python
import security

# Initialize the security module
security.initialize()
```

### Credential Verification

```python
# Verify an API key
is_valid = security.verify_api_key(api_key)

# Verify a database password
is_valid = security.verify_db_password(password)

# Log credential usage
security.log_credential_usage('api_key', 'component', 'operation')
```

### Threat Intelligence

```python
# Add an indicator of compromise (IOC)
security.add_ioc('ip', '192.168.1.1', 'internal', 80)

# Check if an IOC exists
result = security.check_ioc('ip', '192.168.1.1')

# Search intelligence data
results = security.search_intelligence(query={'type': 'ip'})
```

### Threat Detection

```python
# Extract IOCs from text
iocs = security.extract_iocs(text)

# Check threat intelligence for a value
result = security.check_threat_intelligence('192.168.1.1')

# Create a threat rule
rule = security.create_threat_rule(
    name='Suspicious IP',
    description='Detects access from suspicious IP addresses',
    detection={
        'ioc': {
            'type': 'ip',
            'value': '192.168.0.0/16'
        }
    },
    severity='medium'
)
```

### Flask Integration

```python
from flask import Flask
import security

app = Flask(__name__)

# Apply security middleware
security.create_security_middleware(app)

# Protect a route with API key verification
@app.route('/api/protected')
@security.require_api_key
def protected_route():
    return {'status': 'success'}
```

## Configuration

The module uses environment variables and configuration files for its settings.
Key configuration options include:

- `API_KEY`: API key for verification
- `DB_PASSWORD`: Database password
- `SECRET_TOKEN`: Secret token for secure operations
- `MAIL_API_KEY`: API key for mail services
- `LOGGING_API_KEY`: API key for logging services

## Data Storage

The module uses a directory structure for storing data:

- `data/credentials/`: Credential metadata
- `data/credential_history/`: History of credential changes
- `data/intel/`: Intelligence data
- `data/iocs/`: Indicators of compromise
- `data/taxii_configs/`: TAXII server configurations
- `data/threat_rules/`: Threat detection rules
- `data/logs/`: Log files

## Testing

The module includes comprehensive tests in the `tests/` directory:

```bash
python -m unittest discover -s tests
```

## Security Best Practices

- Always use environment variables for storing credentials
- Regularly rotate credentials using the `rotate_credential` function
- Monitor credential usage with `get_recent_usage` and `analyze_for_suspicious_activity`
- Implement proper access controls and audit logging
- Keep the module and its dependencies up to date 