# Eve Project Online Deployment

This README provides instructions for deploying the Eve Project online using JavaScript and Docker.

## Overview

The Eve Project is an AI assistant system with memory enhancement capabilities. This repository includes a modernized setup for easy deployment to various cloud providers.

## Features

- **RESTful API**: Full API access to Eve's capabilities
- **Web Interface**: Beautiful, responsive UI for interacting with Eve
- **WebSockets**: Real-time communication for chat functionality
- **Python Integration**: Leverages Python scripts for NLP capabilities
- **Containerized**: Easy deployment with Docker
- **Monitoring**: Prometheus and Grafana integration for system monitoring
- **Automated Backups**: Scheduled backups of data and database
- **SSL Support**: Secure communication with SSL/TLS

## Prerequisites

- Node.js (v16+)
- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- Git (recommended for version control)

## Installation

### Automated Setup (Recommended)

#### Windows Users
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/eve-project.git
   cd eve-project
   ```
2. Run the setup script:
   ```
   setup.bat
   ```

#### macOS/Linux Users
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/eve-project.git
   cd eve-project
   ```
2. Make the setup script executable and run it:
   ```
   chmod +x setup.sh
   ./setup.sh
   ```
   
   Alternatively, you can use the Node.js setup script:
   ```
   node setup.js
   ```

### Verifying Your Installation

After setup, you can verify that all components are correctly installed and configured:

```
node verify-installation.js
```

This verification script will check:
- Node.js dependencies
- Python dependencies
- Required directories
- Environment configuration
- Docker configuration (if applicable)

If any issues are found, the script will provide guidance on how to resolve them.

### Manual Setup

If you prefer to set up the project manually:

1. Ensure you have the following prerequisites:
   - Node.js v16.0 or higher
   - Python 3.8 or higher
   - npm and pip package managers
   - (Optional) Docker and Docker Compose for containerized deployment

2. Install dependencies:
   ```
   npm install
   pip install -r requirements.txt
   ```

3. Create required directories:
   ```
   mkdir -p data logs journals messages
   ```

4. Create an environment file:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file to match your environment.

## Docker Deployment

To deploy the Eve Project using Docker:

1. Build and start the application:
   ```
   docker-compose up -d
   ```

2. To stop the application:
   ```
   docker-compose down
   ```

### Monitoring

The Docker deployment includes Prometheus and Grafana for monitoring:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (default credentials: admin/eveproject)

## Cloud Deployment Options

### Deployment Script

For easy deployment to various cloud platforms, use the deployment script:

```
node deployment.js --platform=[heroku|render|digitalocean|aws]
```

### Manual Cloud Deployment

#### Heroku
```
heroku create
git push heroku main
```

#### Render
Connect your GitHub repository to Render and follow the deployment instructions.

#### Digital Ocean
Deploy using the Digital Ocean App Platform or create a Droplet and use Docker Compose.

#### AWS
Deploy using Elastic Beanstalk or set up an EC2 instance with Docker.

## Multi-Region Deployment

The Eve Project supports deployment across multiple geographic regions for improved availability, redundancy, and performance. This configuration allows your application to:

- Reduce latency for global users
- Increase fault tolerance
- Improve disaster recovery capabilities
- Scale resources based on regional demand

### Setting Up Multi-Region Deployment

#### Prerequisites
- Multiple cloud provider accounts or regions
- DNS service with geo-routing capabilities (e.g., AWS Route 53, Cloudflare)
- Database with cross-region replication support

#### Configuration Steps

1. Create a multi-region configuration file:
   ```
   cp multi-region-config.example.js multi-region-config.js
   ```
   
2. Edit the configuration file to specify your regions:
   ```javascript
   // Example configuration
   module.exports = {
     regions: [
       {
         name: 'us-east',
         provider: 'aws',
         region: 'us-east-1',
         primaryDatabase: true
       },
       {
         name: 'eu-west',
         provider: 'aws',
         region: 'eu-west-1',
         primaryDatabase: false
       },
       {
         name: 'asia-east',
         provider: 'gcp',
         region: 'asia-east1',
         primaryDatabase: false
       }
     ],
     synchronization: {
       interval: 300, // seconds
       strategy: 'eventual-consistency'
     }
   };
   ```

3. Deploy to multiple regions using the multi-region deployment script:
   ```
   node deploy-multi-region.js
   ```

### Setting Up Data Synchronization

For proper operation across regions, configure data synchronization:

```
node setup-sync.js --primary-region=us-east --strategy=eventual-consistency
```

Available synchronization strategies:
- `eventual-consistency`: Updates propagate asynchronously (recommended)
- `strong-consistency`: Synchronous updates across regions
- `read-local-write-global`: Reads from local region, writes to all regions

### Traffic Management

Configure global traffic routing using the included script:

```
node setup-global-routing.js --method=latency-based
```

Routing methods:
- `latency-based`: Routes users to the lowest-latency region
- `geo-proximity`: Routes based on geographic proximity
- `weighted`: Distributes traffic according to specified weights
- `failover`: Sets primary and backup regions

### Monitoring Multi-Region Deployments

Monitor your multi-region deployment using the enhanced monitoring dashboard:

```
http://your-domain.com/admin/multi-region-status
```

This dashboard provides:
- Health status of each region
- Synchronization lag metrics
- Regional traffic distribution
- Failover readiness indicators

## Security Setup

### SSL Configuration
For production deployments, configure SSL:

```
node setup-ssl.js
```

### Automated Backups
Configure automated backups:

```
node setup-backups.js --schedule="0 0 * * *" --destination="/path/to/backups"
```

## Monitoring Setup

The Eve Project includes built-in monitoring with Prometheus and Grafana:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (default credentials: admin/eveproject)

## Load Testing

To perform load testing:

```
node load-test.js --users=100 --duration=60
```

## API Documentation

Access the API documentation at:

```
http://localhost:3000/api-docs
```

## Troubleshooting

If you encounter issues during setup or deployment:

1. Run the verification script to identify problems:
   ```
   node verify-installation.js
   ```

2. Check the logs:
   ```
   cat logs/app.log
   ```

3. For Docker-related issues:
   ```
   docker-compose logs
   ```

4. If you're still having problems, please open an issue on GitHub.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Directory Structure

- `/secure-credentials` - Repository for securely storing and managing API keys and service credentials

## Secure Credentials Repository

The project includes a comprehensive system for securely managing sensitive credentials:

### Features

- **Encrypted Storage**: All credentials are stored with AES encryption
- **Command-Line Interface**: Easy-to-use PowerShell scripts for credential management
- **Import/Export Tools**: Import credentials from environment variables or config files
- **Backup System**: Automatic backups of credential data

### Getting Started

1. Navigate to the `/secure-credentials` directory:
   ```powershell
   cd secure-credentials
   ```

2. Add a new credential:
   ```powershell
   ./credential-manager.ps1 -Action Add -ServiceName "MyAPI" -Username "apiuser" -Password "apisecret" -Description "API credentials for service X"
   ```

3. Retrieve a credential:
   ```powershell
   ./credential-manager.ps1 -Action Get -ServiceName "MyAPI"
   ```

4. List all stored credentials:
   ```powershell
   ./credential-manager.ps1 -Action List
   ```

5. Import credentials from a configuration file:
   ```powershell
   ./import-credentials.ps1 -ConfigFile "my-credentials.json"
   ```

See the [Secure Credentials README](./secure-credentials/README.md) for more details.

## Security Notes

- The credentials repository is configured to be excluded from Git by default
- Never commit the encryption key or credentials file to version control
- Regular rotation of credentials is recommended

## MyProject Credential Management System

This project demonstrates a secure approach to managing sensitive credentials in both JavaScript and Python applications.

## Secure Credential Management

This project uses a secure approach to credential management:

1. **Isolated Storage**: All credentials are stored in `C:\Documents\credentials\myproject\` outside the codebase
2. **Individual Files**: Each credential is stored in its own file for better isolation and management
3. **Backward Compatibility**: Support for legacy `.env` files is maintained

## Available Credentials

The system manages the following credentials:

- `API_KEY`: Used for API authentication
- `DB_PASSWORD`: Used for database connections
- `SECRET_TOKEN`: Used for cryptographic operations

## Setting Up Development Environment

To set up your development environment:

1. Create the credentials directory:
   ```
   mkdir -p C:\Documents\credentials\myproject
   ```

2. Create individual credential files:
   ```
   echo "your-api-key-here" > C:\Documents\credentials\myproject\API_KEY
   echo "your-db-password-here" > C:\Documents\credentials\myproject\DB_PASSWORD
   echo "your-secret-token-here" > C:\Documents\credentials\myproject\SECRET_TOKEN
   ```

3. OR create a `.env` file (for backward compatibility):
   ```
   echo "API_KEY=your-api-key-here" > C:\Documents\credentials\myproject\.env
   echo "DB_PASSWORD=your-db-password-here" >> C:\Documents\credentials\myproject\.env
   echo "SECRET_TOKEN=your-secret-token-here" >> C:\Documents\credentials\myproject\.env
   ```

## Running the Application

### JavaScript
```
node myproject/app.js
```

### Python
```
python myproject/app.py
```

## Testing Credential Loading

To verify that credentials are loading correctly:

### JavaScript
```
node myproject/test_credentials.js
```

### Python
```
python myproject/test_credentials.py
```

## API Credential Security Best Practices

Following GitHub's [official recommendations](https://docs.github.com/en/rest/authentication/keeping-your-api-credentials-secure) for API credential security:

### Choose Appropriate Authentication Methods

- Use personal access tokens for personal access
- Create GitHub Apps for accessing on behalf of organizations
- Use built-in tokens for GitHub Actions workflows

### Limit Credential Permissions

- Follow the principle of least privilege
- Only grant the specific permissions needed
- Regularly audit and revise permissions

### Store Authentication Credentials Securely

- Never hardcode authentication credentials in your code
- Consider using secret managers like Azure Key Vault or HashiCorp Vault
- Never push unencrypted credentials to any repository, even private ones
- Use secret scanning to detect credentials accidentally committed to repositories

### Limit Access to Credentials

- Don't share personal access tokens with others
- For team access, use secure shared systems (1Password, Azure KeyVault, etc.)
- For GitHub Actions workflows, use encrypted secrets

### Use Credentials Securely in Code

- Store tokens in environment variables or dedicated credential files outside source code
- Never include credentials in logs or debugging output
- Our application automatically masks credentials when logging using the `maskCredential()` function

### Prepare for Security Breaches

If a credential is compromised:
1. Generate a new credential immediately
2. Replace the old credential in all systems
3. Delete the compromised credential
4. Review access logs for suspicious activity

## Credential Rotation

When rotating credentials:

1. Update the corresponding file in `C:\Documents\credentials\myproject\`
2. Restart any running applications to load the new credentials

## Security Best Practices

- Never commit credentials to source control
- Use strong, unique credentials for each environment
- Rotate credentials regularly
- Use different credentials for development, staging, and production
- Monitor for unauthorized access attempts

## Project Structure

```
myproject/
├── app.js            # JavaScript application entry point
├── app.py            # Python application entry point
├── config.js         # JavaScript credential loading module
├── config.py         # Python credential loading module
├── test_credentials.js # JavaScript credential testing
└── test_credentials.py # Python credential testing
```

## Credential Verification and Monitoring

The project includes built-in verification of credential validity:

- Each credential is validated before use with format-specific checks
- Invalid credentials cause early failure with clear error messages
- The system logs credential usage with privacy-preserving masking
- Monitoring can be integrated to detect unusual credential access patterns

## Security Identifiers and Tracking

Each credential usage is tracked with:

1. **Unique Request IDs**: Every API call generates a unique identifier
2. **Usage Timestamps**: All credential access is timestamped
3. **Access Logging**: Records which components accessed credentials
4. **IP Logging**: Records source IP addresses for external API calls

This tracking enables security audits and helps identify potential compromises 