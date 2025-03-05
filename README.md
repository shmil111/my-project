# MyProject

A simple project demonstrating secure configuration management with both Python and JavaScript implementations.

## Project Description

This project showcases best practices for handling sensitive configuration data such as API keys and database passwords. It provides both Python and JavaScript implementations that securely load environment variables from a dedicated location outside the project directory.

## Features

- Secure loading of environment variables from a dedicated directory
- Configuration for both Python and JavaScript applications
- Simple application structure for both languages
- Environment variable masking in console output
- Security-focused approach to credential management

## Setup

1. Copy `.env.example` to `C:/Documents/credentials/myproject/.env`
2. Fill in your actual API keys and passwords in the `.env` file
3. Install dependencies:
   - For Python: `pip install -r requirements.txt`
   - For JavaScript: `npm install`
4. Run the application:
   - For Python: `python app.py`
   - For JavaScript: `node app.js`

## Project Structure

```
myproject/
├── app.py              # Python application entry point
├── app.js              # JavaScript application entry point
├── config.py           # Python configuration loader
├── config.js           # JavaScript configuration loader
├── .env.example        # Example environment variables file
├── requirements.txt    # Python dependencies
├── package.json        # JavaScript dependencies
└── README.md           # This file
```

## Security Notes

- Never commit your actual `.env` file to Git
- Store sensitive credentials in a secure location outside your project directory
- Use environment variables for all sensitive information
- Consider using a secret management service for production environments

## License

MIT # Test authentication
