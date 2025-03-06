# Environment Variables

This document describes all environment variables used in the application. You can configure these variables through a `.env` file in the root directory or by setting them directly in your environment.

## Server Configuration

| Variable | Description | Required | Default | Format |
| --- | --- | --- | --- | --- |
| `NODE_ENV` | Environment mode | Yes | `development` | One of: `development`, `production`, `test` |
| `PORT` | Server port | Yes | `3000` | Port number (0-65535) |
| `LOG_LEVEL` | Logging verbosity | No | `info` | One of: `error`, `warn`, `info`, `debug` |
| `CORS_ORIGIN` | CORS allowed origins | No | `*` | URL or `*` for all origins |

## Authentication

| Variable | Description | Required | Default | Format |
| --- | --- | --- | --- | --- |
| `JWT_SECRET` | Secret key for JWT tokens | Yes | - | String (min 32 chars) |
| `JWT_EXPIRES_IN` | JWT token expiration time | No | `1d` | Time period (e.g., `1h`, `7d`) |

## Redis Configuration

| Variable | Description | Required | Default | Format |
| --- | --- | --- | --- | --- |
| `REDIS_HOST` | Redis server hostname | No | - | Hostname or IP |
| `REDIS_PORT` | Redis server port | No | `6379` | Port number |
| `REDIS_PASSWORD` | Redis server password | No | - | String |
| `REDIS_DB` | Redis database number | No | `0` | Number |

## GitHub Integration

| Variable | Description | Required | Default | Format |
| --- | --- | --- | --- | --- |
| `GITHUB_TOKEN` | GitHub personal access token | No | - | String (min 30 chars) |

## Webhook Configuration

| Variable | Description | Required | Default | Format |
| --- | --- | --- | --- | --- |
| `WEBHOOKS_ENABLED` | Enable webhook endpoints | No | `false` | Boolean (`true` or `false`) |
| `WEBHOOK_SECRET` | Secret for webhook signature validation | No | - | String (min 16 chars) |

## Example .env File

```
# Server
NODE_ENV=development
PORT=3000
LOG_LEVEL=info
CORS_ORIGIN=*

# Authentication
JWT_SECRET=your-jwt-secret-should-be-at-least-32-characters-long
JWT_EXPIRES_IN=1d

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# GitHub Integration
GITHUB_TOKEN=your-github-personal-access-token

# Webhooks
WEBHOOKS_ENABLED=true
WEBHOOK_SECRET=your-webhook-secret
```

## Validation

The application validates all required environment variables at startup. If any required variables are missing or invalid, the application will log an error and exit.

### Validation Rules

- **Required Variables**: If a required variable is missing and has no default, the application will exit with an error.
- **Port Numbers**: Must be valid port numbers between 0 and 65535.
- **JWT Secret**: Must be at least 32 characters long for security.
- **GitHub Token**: Should be at least 30 characters long.
- **Webhook Secret**: Should be at least 16 characters long for security.

## Best Practices

1. **Environment-Specific Configuration**: Use different `.env` files for different environments (e.g., `.env.development`, `.env.production`).
2. **Secrets Management**: Never commit `.env` files containing secrets to version control. Use secret management tools in production.
3. **Default Values**: The application provides sensible defaults for non-critical settings, but you should explicitly set values for production deployments.
4. **Validation**: The application validates environment variables at startup to catch configuration issues early. 