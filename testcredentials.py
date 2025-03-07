#!/usr/bin/env python3
"""
Test script to verify credential loading.
"""
from config import API_KEY, DB_PASSWORD, SECRET_TOKEN

def main():
    """Test that we can load credentials from both .env and individual files."""
    print("Testing credential loading from C:\\Documents\\credentials\\myproject\\")
    print("-" * 60)
    
    # Check if we successfully loaded the API key
    if API_KEY:
        print(f"API_KEY loaded: {API_KEY[:3]}...{API_KEY[-3:] if len(API_KEY) > 6 else ''}")
    else:
        print("Failed to load API_KEY")
        
    # Check if we successfully loaded the database password
    if DB_PASSWORD:
        print(f"DB_PASSWORD loaded: {DB_PASSWORD[:3]}...{DB_PASSWORD[-3:] if len(DB_PASSWORD) > 6 else ''}")
    else:
        print("Failed to load DB_PASSWORD")
        
    # Check if we successfully loaded the secret token
    if SECRET_TOKEN:
        print(f"SECRET_TOKEN loaded: {SECRET_TOKEN[:3]}...{SECRET_TOKEN[-3:] if len(SECRET_TOKEN) > 6 else ''}")
    else:
        print("Failed to load SECRET_TOKEN")

if __name__ == "__main__":
    main() 